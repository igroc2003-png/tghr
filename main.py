import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import BOT_TOKEN, CHANNEL_NUMERIC_ID
from smart_tags import extract_tags
from db import save_vacancy, get_users

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer("👋 Я подбираю вакансии бесплатно по интересам.")


@dp.channel_post()
async def channel_post(msg: Message):
    if msg.chat.id != CHANNEL_NUMERIC_ID:
        return

    text = msg.text or msg.caption
    if not text:
        return

    tags = extract_tags(text)
    save_vacancy(text, str(tags))

    for user_id, user_tags in get_users():
        if tags["profession"] in user_tags:
            try:
                await bot.send_message(user_id, f"🔥 Вакансия:\n\n{text}")
                await asyncio.sleep(0.5)
            except:
                pass


async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
