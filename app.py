import os
import asyncio
import logging

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types

from openai import OpenAI


# ================== ENV ==================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не задан")

# ================== LOGS ==================
logging.basicConfig(level=logging.INFO)

# ================== GPT (OpenRouter) ==================
client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "https://example.com",
        "X-Title": "Telegram GPT Bot"
    }
)

# ================== TELEGRAM ==================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    try:
        completion = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты полезный Telegram-бот ассистент."},
                {"role": "user", "content": message.text}
            ]
        )

        answer = completion.choices[0].message.content
        await message.answer(answer)

    except Exception as e:
        logging.exception(e)
        await message.answer("❌ Ошибка GPT")

# ================== START ==================
async def main():
    logging.info("🤖 Бот запущен (polling)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
