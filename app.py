import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from db import (
    init_db,
    add_user,
    get_users_stats,
    get_all_vacancies,
    get_vacancy_by_id,
    add_vacancy,
    delete_vacancy,
    notifications_enabled,
    toggle_notifications
)

# ================== НАСТРОЙКИ ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018  # ← твой Telegram ID

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== КЛАВИАТУРЫ ==================

def main_keyboard(user_id: int):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]

    if user_id == ADMIN_ID:
        kb.append([
            InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")
        ])

    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_keyboard():
    notif = "🔔 Уведомления: ВКЛ" if notifications_enabled() else "🔕 Уведомления: ВЫКЛ"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="admin_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text=notif, callback_data="toggle_notifications")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def vacancies_keyboard():
    kb = [
        [InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")]
        for vid, title in get_all_vacancies()
    ]

    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message):
    is_new = add_user(message.from_user.id)

    if is_new and notifications_enabled() and message.from_user.id != ADMIN_ID:
        await bot.send_message(
            ADMIN_ID,
            "👤 <b>Новый пользователь</b>\n\n"
            f"ID: <code>{message.from_user.id}</code>\n"
            f"Имя: {message.from_user.full_name}",
            parse_mode="HTML"
        )

    await message.answer(
        "👋 Добро пожаловать",
        reply_markup=main_keyboard(message.from_user.id)
    )

# ================== НАВИГАЦИЯ ==================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "Главное меню",
        reply_markup=main_keyboard(callback.from_user.id)
    )
    await callback.answer()

# ================== ВАКАНСИИ ==================

@dp.callback_query(F.data == "vacancies")
async def vacancies(callback: CallbackQuery):
    await callback.message.answer(
        "📋 Вакансии:",
        reply_markup=vacancies_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("vacancy:"))
async def vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Вакансия не найдена")
        return

    title, description, link, image_id = data
    text = f"<b>{title}</b>\n\n{description}\n\n🔗 {link}"

    if image_id:
        await callback.message.answer_photo(
            image_id,
            caption=text,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML"
        )

    await callback.answer()

# ================== АДМИН ==================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    await callback.message.answer(
        "🛠 Админ-панель",
        reply_markup=admin_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == "toggle_notifications")
async def toggle_notif(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    toggle_notifications()
    await callback.message.edit_reply_markup(reply_markup=admin_keyboard())
    await callback.answer("Готово")


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return

    total, today, week, month = get_users_stats()

    await callback.message.answer(
        "📊 <b>Статистика пользователей</b>\n\n"
        f"👥 Всего: {total}\n"
        f"🆕 Сегодня: {today}\n"
        f"📈 7 дней: {week}\n"
        f"📊 30 дней: {month}",
        parse_mode="HTML"
    )
    await callback.answer()

# ================== MAIN ==================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
