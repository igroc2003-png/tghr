import os
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types


# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = 5108587018  # ВСТАВЬ СЮДА СВОЙ TELEGRAM ID (ЧИСЛОМ)

# ============================================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище состояний
users = {}

QUESTIONS = [
    "Как тебя зовут?",
    "Сколько тебе лет?",
    "В каком ты городе?",
    "Есть ли опыт работы? Если да — какой?",
    "Оставь номер телефона или @username для связи"
]

# ================= HANDLERS =================

@dp.message(CommandStart())
async def start(message: types.Message):
    users[message.from_user.id] = {"step": 0, "answers": []}

    kb = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="📋 Посмотреть вакансии")]],
        resize_keyboard=True
    )

    await message.answer(
        "Привет! 👋\n"
        "Я HR-бот.\n"
        "Помогу подобрать вакансию и передать заявку рекрутеру.",
        reply_markup=kb
    )


@dp.message(lambda m: m.text == "📋 Посмотреть вакансии")
async def vacancies(message: types.Message):
    users[message.from_user.id] = {"step": 0, "answers": []}

    await message.answer(
        "📌 Актуальные вакансии:\n\n"
        "1️⃣ Менеджер по продажам\n"
        "2️⃣ Оператор чата\n"
        "3️⃣ Помощник руководителя\n\n"
        "Ответь на несколько вопросов 👇"
    )

    await message.answer(QUESTIONS[0])


@dp.message()
async def interview(message: types.Message):
    user_id = message.from_user.id

    if user_id not in users:
        return

    step = users[user_id]["step"]
    users[user_id]["answers"].append(message.text)
    users[user_id]["step"] += 1

    if users[user_id]["step"] < len(QUESTIONS):
        await message.answer(QUESTIONS[users[user_id]["step"]])
    else:
        answers = users[user_id]["answers"]

        text = (
            "🆕 Новая заявка\n\n"
            f"👤 Имя: {answers[0]}\n"
            f"🎂 Возраст: {answers[1]}\n"
            f"🏙 Город: {answers[2]}\n"
            f"💼 Опыт: {answers[3]}\n"
            f"📞 Контакт: {answers[4]}"
        )

        await bot.send_message(HR_CHAT_ID, text)

        await message.answer(
            "✅ Спасибо! Заявка отправлена рекрутеру.\n"
            "Мы свяжемся с тобой в ближайшее время."
        )

        users.pop(user_id, None)

# ================= START =================

async def main():
    logging.info("🤖 HR-бот запущен (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
