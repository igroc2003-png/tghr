import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputMediaPhoto
)
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import (
    add_user_tag,
    get_user_tags,
    remove_user_tags,
    get_users_by_tag
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ================== STATE ==================

admin_state = {
    "mode": None,
    "text": None,
    "photos": [],
    "tags": set(),
    "preview_sent": False
}

# ================== ИНТЕРЕСЫ ==================

INTERESTS = {
    "Курьер": "🚚 Доставка / Курьеры",
    "Магазин": "🏪 Магазины / Склады",
    "Фастфуд": "🍔 Фастфуд",
    "CallCenter": "📞 Call-центр",
    "Клининг": "🧹 Клининг",
    "Мастер": "🏗 Мастер / Отделка",
    "Продажи": "💼 Офис / Продажи",
    "Банк": "🏦 Банк / Финансы",
    "Преподаватель": "👨‍🏫 Преподаватель",
    "Водитель": "🚗 Водитель / Такси",
    "Удаленка": "💻 Удалёнка",
    "Подработка": "⏱️ Подработка",
    "Вахта": "💼 Вахта"
}

AUTO_TAGS = {
    "Курьер": ["курьер", "достав"],
    "Магазин": ["магазин", "склад"],
    "Фастфуд": ["фастфуд", "кафе", "ресторан"],
    "CallCenter": ["call", "колл", "оператор"],
    "Клининг": ["клининг", "уборк"],
    "Мастер": ["мастер", "ремонт", "отделк"],
    "Продажи": ["продаж", "менеджер"],
    "Банк": ["банк", "финанс"],
    "Преподаватель": ["учител", "преподав"],
    "Водитель": ["водител", "такси"],
    "Удаленка": ["удален", "онлайн"],
    "Подработка": ["подработ", "смен"],
    "Вахта": ["вахта", "смен"]
}

def extract_auto_tags(text: str) -> set:
    text = (text or "").lower()
    return {tag for tag, keys in AUTO_TAGS.items() if any(k in text for k in keys)}

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
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])

def interests_kb(user_id: int):
    selected = set(get_user_tags(user_id))

    def btn(tag, label):
        mark = "✅" if tag in selected else "❌"
        return InlineKeyboardButton(
            text=f"{mark} {label}",
            callback_data=f"tag_{tag}"
        )

    rows = []
    items = list(INTERESTS.items())

    for i in range(0, len(items), 2):
        row = [btn(items[i][0], items[i][1])]
        if i + 1 < len(items):
            row.append(btn(items[i + 1][0], items[i + 1][1]))
        rows.append(row)

    rows.append([
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_interests"),
        InlineKeyboardButton(text="✅ Готово", callback_data="save_interests")
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)

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
        await message.answer(
            "📂 Выбери интересы:",
            reply_markup=interests_kb(message.from_user.id)
        )

# ================== ИНТЕРЕСЫ ==================

@dp.callback_query(F.data == "user_menu")
async def user_menu(cb: CallbackQuery):
    await cb.message.answer(
        "📂 Выбери интересы:",
        reply_markup=interests_kb(cb.from_user.id)
    )
    await cb.answer()

@dp.callback_query(F.data.startswith("tag_"))
async def toggle_tag(cb: CallbackQuery):
    tag = cb.data.replace("tag_", "")
    current = set(get_user_tags(cb.from_user.id))

    remove_user_tags(cb.from_user.id)
    if tag in current:
        current.remove(tag)
    else:
        current.add(tag)

    for t in current:
        add_user_tag(cb.from_user.id, t)

    await cb.message.edit_reply_markup(reply_markup=interests_kb(cb.from_user.id))
    await cb.answer()

@dp.callback_query(F.data == "save_interests")
async def save_interests(cb: CallbackQuery):
    await cb.message.answer("✅ Интересы сохранены")

    if cb.from_user.id == ADMIN_ID:
        await cb.message.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await cb.message.answer(
            "📂 Выбери интересы:",
            reply_markup=interests_kb(cb.from_user.id)
        )
    await cb.answer()

@dp.callback_query(F.data == "clear_interests")
async def clear_interests(cb: CallbackQuery):
    remove_user_tags(cb.from_user.id)
    await cb.message.answer("🗑 Интересы очищены")

    if cb.from_user.id == ADMIN_ID:
        await cb.message.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await cb.message.answer(
            "📂 Выбери интересы:",
            reply_markup=interests_kb(cb.from_user.id)
        )
    await cb.answer()

# ================== АДМИН ==================

@dp.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery):
    admin_state.clear()
    admin_state.update({
        "mode": "job",
        "photos": [],
        "tags": set(),
        "preview_sent": False
    })
    await cb.message.answer("✏️ Напиши вакансию")
    await cb.answer()

@dp.callback_query(F.data == "add_post")
async def add_post(cb: CallbackQuery):
    admin_state.clear()
    admin_state.update({
        "mode": "post",
        "photos": [],
        "tags": set(),
        "preview_sent": False
    })
    await cb.message.answer("📝 Напиши пост")
    await cb.answer()

@dp.callback_query(F.data == "edit")
async def edit(cb: CallbackQuery):
    admin_state["preview_sent"] = False
    await cb.message.answer("✏️ Отправь новый текст или фото")
    await cb.answer()

@dp.message(F.from_user.id == ADMIN_ID)
async def receive(message: Message):
    if admin_state.get("mode") not in ("job", "post"):
        return

    if message.photo:
        admin_state["photos"].append(message.photo[-1].file_id)
        if not message.caption:
            return

    if message.text or message.caption:
        admin_state["text"] = message.text or message.caption

    admin_state["tags"] = extract_auto_tags(admin_state["text"])

    if admin_state["preview_sent"]:
        return

    admin_state["preview_sent"] = True

    if admin_state["photos"]:
        await message.answer_photo(
            admin_state["photos"][0],
            caption=admin_state["text"],
            reply_markup=confirm_kb()
        )
    else:
        await message.answer(
            admin_state["text"],
            reply_markup=confirm_kb()
        )

# ================== ПУБЛИКАЦИЯ ==================

@dp.callback_query(F.data == "publish")
async def publish(cb: CallbackQuery):
    text = admin_state["text"]
    photos = admin_state["photos"]
    tags = admin_state["tags"]

    sent_users = set()

    # В КАНАЛ
    if photos:
        media = [InputMediaPhoto(media=photos[0], caption=text)]
        media += [InputMediaPhoto(media=p) for p in photos[1:]]
        await bot.send_media_group(CHANNEL_USERNAME, media)
    else:
        await bot.send_message(CHANNEL_USERNAME, text)

    # РАССЫЛКА
    for tag in tags:
        for uid in get_users_by_tag(tag):
            if uid in sent_users:
                continue
            try:
                if photos:
                    await bot.send_media_group(uid, media)
                else:
                    await bot.send_message(uid, text)
                sent_users.add(uid)
            except:
                pass

    admin_state.clear()
    await cb.message.answer(
        f"✅ Опубликовано\n📩 Отправлено пользователям: {len(sent_users)}",
        reply_markup=admin_kb()
    )
    await cb.answer()

@dp.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery):
    admin_state.clear()
    await cb.message.answer("❌ Отменено", reply_markup=admin_kb())
    await cb.answer()

# ================== ЗАПУСК ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())