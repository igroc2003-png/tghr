import asyncio
import re

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import (
    get_user_tags,
    add_user_tag,
    clear_user_tags,
    get_users_by_tag
)

# ================== BOT ==================

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== FSM ==================

class Form(StatesGroup):
    choosing_interests = State()
    adding_job = State()
    adding_post = State()
    confirm = State()

# ================== ИНТЕРЕСЫ ==================

INTERESTS = {
    "Курьеры": "🚚 Доставка / Курьеры",
    "Магазины": "🏪 Магазины / Склады",
    "Фастфуд": "🍔 Фастфуд",
    "Коллцентр": "📞 Call-центр",
    "Клининг": "🧹 Клининг",
    "Мастер": "🏗 Мастер / Отделка",
    "Офис": "💼 Офис / Продажи",
    "Финансы": "🏦 Банк / Финансы",
    "Учитель": "👨‍🏫 Преподаватель",
    "Водитель": "🚗 Водитель / Такси",
    "Удаленка": "💻 Удалёнка",
    "Подработка": "⏱ Подработка",
}

AUTO_TAGS = {
    "Курьеры": ["курьер", "достав"],
    "Магазины": ["магазин", "склад"],
    "Фастфуд": ["фастфуд", "кафе", "бургер"],
    "Коллцентр": ["call", "колл"],
    "Клининг": ["клининг", "уборк"],
    "Мастер": ["мастер", "ремонт", "отделк"],
    "Офис": ["офис", "продаж"],
    "Финансы": ["банк", "кредит"],
    "Учитель": ["учител", "преподав"],
    "Водитель": ["водител", "такси"],
    "Удаленка": ["удален", "онлайн"],
    "Подработка": ["подработ", "смен"],
}

# ================== УТИЛИТЫ ==================

def extract_auto_tags(text: str) -> set:
    text = text.lower()
    tags = set()
    for tag, keys in AUTO_TAGS.items():
        if any(k in text for k in keys):
            tags.add(tag)
    return tags


def format_job(raw: str):
    title = raw.split("\n")[0].strip().title()

    salary = re.search(r"\d{3,6}", raw)
    salary_text = f"{salary.group()} ₽" if salary else "по договорённости"

    link = re.search(r"https?://\S+", raw)
    link_text = link.group() if link else "в личные сообщения"

    tags = extract_auto_tags(raw)

    text = (
        f"🔥 {title.upper()}\n\n"
        f"👷 Должность:\n— {title}\n\n"
        f"💰 Доход:\n— {salary_text}\n\n"
        f"✍️ Отклик:\n👉 {link_text}\n\n"
    )

    if tags:
        text += " ".join(f"#{t}" for t in tags)

    return text, tags

# ================== КЛАВИАТУРЫ ==================

def interests_kb(selected: set):
    kb, row = [], []
    for tag, title in INTERESTS.items():
        mark = "✅" if tag in selected else "❌"
        row.append(
            InlineKeyboardButton(
                text=f"{mark} {title}",
                callback_data=f"tag_{tag}"
            )
        )
        if len(row) == 2:
            kb.append(row)
            row = []

    if row:
        kb.append(row)

    kb.append([
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear"),
        InlineKeyboardButton(text="✅ Готово", callback_data="done"),
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def edit_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Изменить интересы", callback_data="edit")]
    ])


def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")],
        [InlineKeyboardButton(text="📝 Опубликовать пост", callback_data="add_post")],
    ])


def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])

# ================== ПОДПИСКА ==================

async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except:
        return False

# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            f"📢 Подпишись на канал:\nhttps://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ-панель", reply_markup=admin_kb())
        return

    tags = set(get_user_tags(message.from_user.id))
    await state.set_state(Form.choosing_interests)
    await state.update_data(selected=tags)

    await message.answer(
        "📂 Выбери интересы:",
        reply_markup=interests_kb(tags)
    )

# ================== ИНТЕРЕСЫ ==================

@dp.callback_query(F.data.startswith("tag_"))
async def toggle_tag(cb: CallbackQuery, state: FSMContext):
    tag = cb.data.replace("tag_", "")
    data = await state.get_data()
    selected = set(data.get("selected", set()))

    selected.symmetric_difference_update({tag})
    await state.update_data(selected=selected)

    await cb.message.edit_reply_markup(reply_markup=interests_kb(selected))
    await cb.answer()


@dp.callback_query(F.data == "clear")
async def clear(cb: CallbackQuery, state: FSMContext):
    await state.update_data(selected=set())
    await cb.message.edit_reply_markup(reply_markup=interests_kb(set()))
    await cb.answer("Очищено")


@dp.callback_query(F.data == "done")
async def done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", set())

    clear_user_tags(cb.from_user.id)
    for tag in selected:
        add_user_tag(cb.from_user.id, tag)

    await state.clear()
    await cb.message.answer(
        "✅ Интересы сохранены",
        reply_markup=edit_kb()
    )
    await cb.answer()

@dp.callback_query(F.data == "edit")
async def edit(cb: CallbackQuery, state: FSMContext):
    tags = set(get_user_tags(cb.from_user.id))
    await state.set_state(Form.choosing_interests)
    await state.update_data(selected=tags)
    await cb.message.answer("🔁 Измени интересы:", reply_markup=interests_kb(tags))
    await cb.answer()

# ================== АДМИН ==================

@dp.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.adding_job)
    await cb.message.answer("✏️ Напиши текст вакансии")
    await cb.answer()

@dp.callback_query(F.data == "add_post")
async def add_post(cb: CallbackQuery, state: FSMContext):
    await state.set_state(Form.adding_post)
    await cb.message.answer("📝 Напиши пост")
    await cb.answer()

@dp.message(Form.adding_job)
@dp.message(Form.adding_post)
async def receive(message: Message, state: FSMContext):
    raw = message.text or message.caption
    photo = message.photo[-1].file_id if message.photo else None

    if await state.get_state() == Form.adding_job.state:
        text, tags = format_job(raw)
    else:
        text = raw
        tags = extract_auto_tags(raw)

    await state.update_data(text=text, tags=tags, photo=photo)
    await state.set_state(Form.confirm)

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=confirm_kb())
    else:
        await message.answer(text, reply_markup=confirm_kb())

# ================== ПУБЛИКАЦИЯ ==================

@dp.callback_query(F.data == "publish")
async def publish(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data["text"]
    photo = data.get("photo")
    tags = data.get("tags", set())

    if photo:
        await bot.send_photo(CHANNEL_USERNAME, photo, caption=text)
    else:
        await bot.send_message(CHANNEL_USERNAME, text)

    sent = 0
    for tag in tags:
        for uid in get_users_by_tag(tag):
            try:
                if photo:
                    await bot.send_photo(uid, photo, caption=text)
                else:
                    await bot.send_message(uid, text)
                sent += 1
            except:
                pass

    await state.clear()
    await cb.message.answer(
        f"✅ Опубликовано\n📩 Рассылка: {sent}",
        reply_markup=admin_kb()
    )
    await cb.answer()

@dp.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Отменено", reply_markup=admin_kb())
    await cb.answer()

# ================== RUN ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
