import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

from db import (
    init_db,
    get_all_vacancies,
    get_vacancy_by_id,
    add_vacancy
)

# ================= НАСТРОЙКИ =================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

ADMIN_ID = 5108587018  # 🔴 ВСТАВЬ СЮДА СВОЙ TELEGRAM ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= КЛАВИАТУРА =================

def vacancies_keyboard():
    keyboard = []

    vacancies = get_all_vacancies()
    if not vacancies:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Вакансий нет", callback_data="empty")]
            ]
        )

    for vid, title in vacancies:
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"vacancy:{vid}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ================= ХЕНДЛЕРЫ =================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет! Я HR-бот.\n\n"
        "Выбери вакансию 👇",
        reply_markup=vacancies_keyboard()
    )


@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Вакансия не найдена")
        return

    title, description, link = data

    await callback.message.answer(
        f"📌 <b>{title}</b>\n\n{description}\n\n🔗 {link}",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "empty")
async def empty_callback(callback):
    await callback.answer("Пока вакансий нет")


# ================= АДМИН-КОМАНДЫ =================

@dp.message(Command("add"))
async def add_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа")
        return

    await message.answer(
        "✍️ Добавление вакансии\n\n"
        "Формат:\n"
        "<code>/add\n"
        "Название\n"
        "Описание\n"
        "Ссылка</code>",
        parse_mode="HTML"
    )


@dp.message(Command("delete"))
async def delete_command(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У тебя нет доступа")
        return

    vacancies = get_all_vacancies()
    if not vacancies:
        await message.answer("Вакансий нет")
        return

    text = "🗑 Удаление вакансии\n\nОтправь:\n<code>/delete ID</code>\n\nСписок:\n"
    for vid, title in vacancies:
        text += f"{vid} — {title}\n"

    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.startswith("/add\n"))
async def process_add(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    parts = message.text.split("\n", 3)
    if len(parts) < 4:
        await message.answer("❌ Неверный формат")
        return

    _, title, description, link = parts
    add_vacancy(title.strip(), description.strip(), link.strip())

    await message.answer("✅ Вакансия добавлена")


@dp.message(F.text.startswith("/delete "))
async def process_delete(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        vacancy_id = int(message.text.split()[1])
    except ValueError:
        await message.answer("❌ Укажи ID числом")
        return

    from db import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
    conn.commit()
    conn.close()

    await message.answer("🗑 Вакансия удалена")


# ================= ЗАПУСК =================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
