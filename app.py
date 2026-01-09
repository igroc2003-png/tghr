import asyncio
import os
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = 5108587018  # твой Telegram ID

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не найден")

# =========================
# ВАКАНСИИ
# =========================

VACANCIES = {
    "Менеджер по продажам": "Продажи, общение с клиентами, удалённо.\nЗП от 80 000 ₽",
    "Оператор чата": "Ответы клиентам в чате.\nГрафик 2/2, удалённо.\nЗП от 50 000 ₽",
    "HR-ассистент": "Подбор персонала, общение с кандидатами.\nЗП от 60 000 ₽",
}

# =========================
# ИНИЦИАЛИЗАЦИЯ
# =========================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

user_states = {}  # user_id -> состояние
user_data = {}    # user_id -> данные

# =========================
# КЛАВИАТУРЫ
# =========================

def vacancies_keyboard():
    buttons = [[KeyboardButton(text=v)] for v in VACANCIES.keys()]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# =========================
# HANDLERS
# =========================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Здравствуйте!\n"
        "Я HR-бот.\n\n"
        "Выберите вакансию:",
        reply_markup=vacancies_keyboard()
    )

@dp.message(lambda m: m.text in VACANCIES)
async def vacancy_selected(message: Message):
    user_id = message.from_user.id
    vacancy = message.text

    user_states[user_id] = "wait_name"
    user_data[user_id] = {"vacancy": vacancy}

    await message.answer(
        f"📌 *{vacancy}*\n\n"
        f"{VACANCIES[vacancy]}\n\n"
        "Введите ваше имя:",
        parse_mode="Markdown",
        reply_markup=None
    )

@dp.message(lambda m: user_states.get(m.from_user.id) == "wait_name")
async def get_name(message: Message):
    user_id = message.from_user.id
    user_data[user_id]["name"] = message.text
    user_states[user_id] = "wait_phone"

    await message.answer("📞 Введите ваш номер телефона:")

@dp.message(lambda m: user_states.get(m.from_user.id) == "wait_phone")
async def get_phone(message: Message):
    user_id = message.from_user.id
    user_data[user_id]["phone"] = message.text

    data = user_data[user_id]

    text = (
        "📥 *Новый отклик*\n\n"
        f"Вакансия: {data['vacancy']}\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Telegram: @{message.from_user.username}"
    )

    await bot.send_message(HR_CHAT_ID, text, parse_mode="Markdown")

    await message.answer(
        "✅ Спасибо! Ваш отклик отправлен HR.\n"
        "Мы свяжемся с вами.",
        reply_markup=vacancies_keyboard()
    )

    user_states.pop(user_id, None)
    user_data.pop(user_id, None)

@dp.message(lambda m: m.text == "❌ Отмена")
async def cancel(message: Message):
    user_id = message.from_user.id
    user_states.pop(user_id, None)
    user_data.pop(user_id, None)

    await message.answer(
        "Действие отменено.\nВыберите вакансию:",
        reply_markup=vacancies_keyboard()
    )

# =========================
# ЗАПУСК
# =========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
