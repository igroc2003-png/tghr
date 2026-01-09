import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from openai import OpenAI

# ===== ENV =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY не задан")

# ===== CLIENTS =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = "Ты полезный Telegram-ассистент. Отвечай кратко и по делу."

# ===== HANDLERS =====
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("🤖 GPT-бот запущен. Напиши любой вопрос.")

@dp.message()
async def gpt_reply(message: types.Message):
    await bot.send_chat_action(message.chat.id, "typing")

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message.text}
        ],
        temperature=0.7
    )

    answer = response.choices[0].message.content
    await message.answer(answer)

# ===== START =====
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

