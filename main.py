import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import add_user_tag, get_users_by_tag

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# простое состояние
state = {}

# ---------- КЛАВИАТУРЫ ----------

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")],
        [InlineKeyboardButton(text="📂 Выбрать интересы", callback_data="user_menu")]
    ])

def categories_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Доставка / Курьеры", callback_data="cat_delivery")],
        [InlineKeyboardButton(text="💻 Удалёнка", callback_data="cat_remote")],
        [InlineKeyboardButton(text="💼 Офис / Продажи", callback_data="cat_office")],
    ])

def delivery_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚴 Курьер", callback_data="tag_Курьер")],
        [InlineKeyboardButton(text="📦 Доставка", callback_data="tag_Доставка")],
        [InlineKeyboardButton(text="🕒 Подработка", callback_data="tag_Подработка")],
    ])

def remote_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Удаленка", callback_data="tag_Удаленка")],
        [InlineKeyboardButton(text="📞 CallCenter", callback_data="tag_CallCenter")],
    ])

def office_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Офис", callback_data="tag_Офис")],
        [InlineKeyboardButton(text="📈 Продажи", callback_data="tag_Продажи")],
    ])

# ---------- ПРОВЕРКА ПОДПИСКИ ----------

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except:
        return False

# ---------- START ----------

@router.message(CommandStart())
async def start(message: Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Подпишись на канал:\n"
            f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ-меню", reply_markup=admin_kb())
    else:
        await message.answer("Выбери категорию:", reply_markup=categories_kb())

# ---------- МЕНЮ ПОЛЬЗОВАТЕЛЯ ----------

@router.callback_query(F.data == "user_menu")
async def user_menu(cb: CallbackQuery):
    await cb.message.answer("Выбери категорию:", reply_markup=categories_kb())
    await cb.answer()

@router.callback_query(F.data == "cat_delivery")
async def cat_delivery(cb: CallbackQuery):
    await cb.message.answer("Выбери интерес:", reply_markup=delivery_kb())
    await cb.answer()

@router.callback_query(F.data == "cat_remote")
async def cat_remote(cb: CallbackQuery):
    await cb.message.answer("Выбери интерес:", reply_markup=remote_kb())
    await cb.answer()

@router.callback_query(F.data == "cat_office")
async def cat_office(cb: CallbackQuery):
    await cb.message.answer("Выбери интерес:", reply_markup=office_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("tag_"))
async def save_tag(cb: CallbackQuery):
    tag = cb.data.replace("tag_", "")
    add_user_tag(cb.from_user.id, tag)
    await cb.message.answer(f"✅ Интерес сохранён: #{tag}")
    await cb.answer()

# ---------- ДОБАВЛЕНИЕ ВАКАНСИИ ----------

@router.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery):
    if cb.from_user.id != ADMIN_ID:
        await cb.answer("⛔ Нет доступа", show_alert=True)
        return

    state["awaiting_job"] = True
    await cb.message.answer(
        "✏️ Отправь вакансию ОДНИМ сообщением\n\n"
        "Можно:\n"
        "• текст\n"
        "• фото + подпись\n\n"
        "Теги пиши так:\n"
        "#Курьер #Удаленка #БезОпыта"
    )
    await cb.answer()

# ---------- ПРИЁМ ВАКАНСИИ (ТЕКСТ / ФОТО) ----------

@router.message(F.from_user.id == ADMIN_ID)
async def admin_post(message: Message):
    if not state.get("awaiting_job"):
        return

    state["awaiting_job"] = False

    text = message.caption or message.text or ""
    tags = {w[1:] for w in text.split() if w.startswith("#")}

    sent = 0

    # 🖼 Если есть фото
    if message.photo:
        photo_id = message.photo[-1].file_id

        # В канал
        await bot.send_photo(
            CHANNEL_USERNAME,
            photo_id,
            caption=text
        )

        # Рассылка
        for tag in tags:
            for uid in get_users_by_tag(tag):
                try:
                    await bot.send_photo(uid, photo_id, caption=text)
                    sent += 1
                except:
                    pass

    else:
        # Только текст
        await bot.send_message(CHANNEL_USERNAME, text)

        for tag in tags:
            for uid in get_users_by_tag(tag):
                try:
                    await bot.send_message(uid, text)
                    sent += 1
                except:
                    pass

    await message.answer(
        f"✅ Вакансия опубликована\n"
        f"📩 Рассылка: {sent} чел"
    )

# ---------- ЗАПУСК ----------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
