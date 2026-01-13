import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart

from config import BOT_TOKEN, CHANNEL_NUMERIC_ID
from smart_tags import extract_tags
from db import save_user, get_users, save_vacancy

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


def interests_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐍 Python", callback_data="interest_python")],
        [InlineKeyboardButton(text="🎨 Дизайн", callback_data="interest_designer")],
        [InlineKeyboardButton(text="📊 Менеджмент", callback_data="interest_manager")]
    ])


@dp.message(CommandStart())
async def start(msg: Message):
    await msg.answer(
        "👋 Я бесплатно подбираю вакансии по интересам.\n\n"
        "Выбери направление 👇",
        reply_markup=interests_kb()
    )


@dp.callback_query(F.data.startswith("interest_"))
async def save_interest(call: CallbackQuery):
    interest = call.data.replace("interest_", "")
    save_user(call.from_user.id, interest)

    await call.message.edit_text(
        f"✅ Готово!\n\n"
        f"Я буду присылать вакансии по направлению: *{interest}*",
        parse_mode="Markdown"
    )


@dp.channel_post()
async def channel_post(msg: Message):
    if msg.chat.id != CHANNEL_NUMERIC_ID:
        return

    text = msg.text or msg.caption
    if not text:
        return

    tags = extract_tags(text)
    save_vacancy(text, str(tags))

    for user_id, interest in get_users():
        if tags["profession"] == interest:
            try:
                await bot.send_message(
                    user_id,
                    f"🔥 Подходящая вакансия:\n\n{text}"
                )
                await asyncio.sleep(0.5)
            except:
                pass


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
