import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_ID
from db import conn, cur

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

admin_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")]
])

@dp.message(CommandStart())
async def start(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer("👑 Админ-панель", reply_markup=admin_kb)
    else:
        await msg.answer("👋 Я подбираю вакансии бесплатно по интересам.")

@dp.callback_query(F.data == "add_job")
async def add_job(cb):
    if cb.from_user.id == ADMIN_ID:
        await cb.message.answer("✏️ Отправь текст вакансии одним сообщением")

@dp.message(F.from_user.id == ADMIN_ID)
async def admin_post(msg: Message):
    text = msg.text
    if not text:
        return
    await bot.send_message(CHANNEL_ID, text)
    await msg.answer("✅ Вакансия опубликована и отправлена подписчикам")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
