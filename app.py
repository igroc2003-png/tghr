import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from db import init_db, get_all_vacancies, get_vacancy_by_id

# ================= НАСТРОЙКИ =================

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================= КЛАВИАТУРА =================

def vacancies_keyboard():
    keyboard = []

    vacancies = get_all_vacancies()
    if not vacancies:
        keyboard.append([
            InlineKeyboardButton(
                text="❌ Вакансий пока нет",
                callback_data="empty"
            )
        ])
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

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
        "Выбери вакансию из списка ниже 👇",
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
        f"📌 <b>{title}</b>\n\n"
        f"{description}\n\n"
        f"🔗 {link}",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "empty")
async def empty_callback(callback):
    await callback.answer("Пока вакансий нет")


# ================= ЗАПУСК =================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
