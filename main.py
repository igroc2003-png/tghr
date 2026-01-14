import asyncio
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import add_user_tag, get_users_by_tag, remove_user_tags

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================== СОСТОЯНИЕ ==================

state = {
    "mode": None,        # job | post
    "text": None,
    "photo": None,
    "tags": set(),
    "user_tags": set()   # временное хранилище выбранных интересов
}

# ================== АВТО-ТЕГИ ==================

AUTO_TAGS = {
    "Продажи": ["продав", "продаж"],
    "БезОпыта": ["без опыта", "обуч"],
    "Подработка": ["смен", "подработ"],
    "Удаленка": ["удален", "онлайн"],
    "Курьер": ["курьер", "достав"],
    "Офис": ["офис"],
}

def extract_auto_tags(text: str):
    text = text.lower()
    tags = set()
    for tag, keys in AUTO_TAGS.items():
        if any(k in text for k in keys):
            tags.add(tag)
    return tags

# ================== ФОРМАТИРОВАНИЕ ВАКАНСИИ ==================

def format_job(raw: str):
    raw_l = raw.lower()

    title = raw.split("\n")[0].strip().title()

    salary = re.search(r"\d{3,6}", raw)
    salary_text = f"{salary.group()} ₽ за смену" if salary else "по договорённости"

    schedule = re.search(r"\d+/\d+", raw)
    schedule_text = schedule.group() if schedule else "обсуждается"

    link = re.search(r"https?://\S+", raw)
    link_text = link.group() if link else "написать в личные сообщения"

    experience = "не требуется (обучение)" if "без опыта" in raw_l else "желателен"

    tags = extract_auto_tags(raw)

    text = (
        f"🔥 {title.upper()}\n\n"
        f"👷 Должность:\n— {title}\n\n"
        f"💰 Доход:\n— {salary_text}\n\n"
        f"⏱ График:\n— {schedule_text}\n\n"
        f"🎓 Опыт:\n— {experience}\n\n"
        f"✍️ Отклик:\n👉 {link_text}\n\n"
        + " ".join(f"#{t}" for t in tags)
    )

    return text, tags

# ================== КЛАВИАТУРЫ ==================

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")],
        [InlineKeyboardButton(text="📝 Опубликовать пост", callback_data="add_post")],
        [InlineKeyboardButton(text="📂 Выбрать интересы", callback_data="user_menu")]
    ])

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])

def categories_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Курьер / Доставка", callback_data="tag_Курьер")],
        [InlineKeyboardButton(text="💻 Удалёнка", callback_data="tag_Удаленка")],
        [InlineKeyboardButton(text="💼 Офис / Продажи", callback_data="tag_Продажи")],
        [InlineKeyboardButton(text="🗑 Очистить интересы", callback_data="clear_interests")],
        [InlineKeyboardButton(text="✅ Готово", callback_data="save_interests")]
    ])

# ================== ПРОВЕРКА ПОДПИСКИ ==================

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

@router.message(CommandStart())
async def start(message: Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Подпишись на канал:\n"
            f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await message.answer("📂 Выбери интересы:", reply_markup=categories_kb())

# ================== МЕНЮ ИНТЕРЕСОВ ==================

@router.callback_query(F.data == "user_menu")
async def user_menu(cb: CallbackQuery):
    await cb.message.answer("📂 Выбери интересы:", reply_markup=categories_kb())
    await cb.answer()

# ================== ВЫБОР ИНТЕРЕСОВ ==================

@router.callback_query(F.data.startswith("tag_"))
async def toggle_tag(cb: CallbackQuery):
    tag = cb.data.replace("tag_", "")
    user_tags = state["user_tags"]

    if tag in user_tags:
        user_tags.remove(tag)
        await cb.answer(f"❌ #{tag} убран")
    else:
        user_tags.add(tag)
        await cb.answer(f"✅ #{tag} добавлен")

# ================== СОХРАНИТЬ ИНТЕРЕСЫ ==================

@router.callback_query(F.data == "save_interests")
async def save_interests(cb: CallbackQuery):
    if not state["user_tags"]:
        await cb.answer("❗ Ничего не выбрано", show_alert=True)
        return

    for tag in state["user_tags"]:
        add_user_tag(cb.from_user.id, tag)

    tags_text = " ".join(f"#{t}" for t in state["user_tags"])
    state["user_tags"] = set()

    await cb.message.answer(f"✅ Интересы сохранены:\n{tags_text}")
    await cb.answer()

# ================== ОЧИСТКА ИНТЕРЕСОВ ==================

@router.callback_query(F.data == "clear_interests")
async def clear_interests(cb: CallbackQuery):
    remove_user_tags(cb.from_user.id)
    state["user_tags"] = set()
    await cb.message.answer("🗑 Все интересы удалены")
    await cb.answer()

# ================== ДОБАВЛЕНИЕ КОНТЕНТА ==================

@router.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery):
    state["mode"] = "job"
    await cb.message.answer("✏️ Напиши вакансию простым текстом")
    await cb.answer()

@router.callback_query(F.data == "add_post")
async def add_post(cb: CallbackQuery):
    state["mode"] = "post"
    await cb.message.answer("📝 Отправь пост (текст или фото + текст)")
    await cb.answer()

# ================== ПРИЁМ СООБЩЕНИЯ ==================

@router.message(F.from_user.id == ADMIN_ID)
async def receive(message: Message):
    if not state.get("mode"):
        return

    raw = message.text or message.caption
    photo = message.photo[-1].file_id if message.photo else None

    if not raw:
        await message.answer("❌ Нужно добавить текст")
        return

    if state["mode"] == "job":
        text, tags = format_job(raw)
    else:
        text = raw
        tags = extract_auto_tags(raw)

    state["text"] = text
    state["photo"] = photo
    state["tags"] = tags

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=confirm_kb())
    else:
        await message.answer(text, reply_markup=confirm_kb())

# ================== ПУБЛИКАЦИЯ ==================

@router.callback_query(F.data == "publish")
async def publish(cb: CallbackQuery):
    text = state["text"]
    photo = state["photo"]

    if photo:
        await bot.send_photo(CHANNEL_USERNAME, photo, caption=text)
    else:
        await bot.send_message(CHANNEL_USERNAME, text)

    for tag in state["tags"]:
        for uid in get_users_by_tag(tag):
            try:
                if photo:
                    await bot.send_photo(uid, photo, caption=text)
                else:
                    await bot.send_message(uid, text)
            except:
                pass

    state["mode"] = None
    await cb.message.answer("✅ Опубликовано", reply_markup=admin_kb())
    await cb.answer()

# ================== ЗАПУСК ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
