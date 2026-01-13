import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from config import BOT_TOKEN, CHANNEL_USERNAME

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def directions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐍 Python", callback_data="dir_python")],
        [InlineKeyboardButton(text="🎨 Дизайн", callback_data="dir_design")],
        [InlineKeyboardButton(text="📊 Менеджмент", callback_data="dir_management")],
    ])

def subscribed_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я подписался на канал", callback_data="subscribed")]
    ])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Я бесплатно подбираю вакансии по интересам.\n"
        "Без спама и фейков.\n\n"
        "🎯 Выбери направление — и получай\n"
        "только подходящие предложения 👇",
        reply_markup=directions_kb()
    )

@dp.callback_query(F.data.startswith("dir_"))
async def choose_direction(callback):
    direction = callback.data.replace("dir_", "")
    await callback.message.answer(
        f"✅ Готово!\n\n"
        f"Я буду подбирать для тебя вакансии по направлению: {direction.capitalize()}\n\n"
        f"📢 Все актуальные вакансии публикуем в канале:\n"
        f"{CHANNEL_USERNAME}",
        reply_markup=subscribed_kb()
    )
    await callback.answer()

@dp.callback_query(F.data == "subscribed")
async def subscribed(callback):
    await callback.message.answer(
        "🔥 Отлично!\n\n"
        "Теперь ты будешь получать подходящие вакансии."
    )
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())