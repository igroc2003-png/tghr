import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------- КНОПКИ ----------

def subscribe_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Подписаться на канал",
                    url=f"https://t.me/{CHANNEL_USERNAME[1:]}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Я подписался",
                    callback_data="check_sub"
                )
            ]
        ]
    )


def directions_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🐍 Python", callback_data="dir_python")],
            [InlineKeyboardButton(text="🎨 Дизайн", callback_data="dir_design")],
            [InlineKeyboardButton(text="📊 Менеджмент", callback_data="dir_management")]
        ]
    )


# ---------- ПРОВЕРКА ПОДПИСКИ ----------

async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except:
        return False


# ---------- /start ----------

@dp.message(CommandStart())
async def start(message: Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Для доступа к подбору вакансий\n"
            "подпишись на канал 👇",
            reply_markup=subscribe_kb()
        )
        return

    await message.answer(
        "👋 Я бесплатно подбираю вакансии по интересам.\n\n"
        "🎯 Выбери направление 👇",
        reply_markup=directions_kb()
    )


# ---------- ПРОВЕРКА КНОПКИ «Я ПОДПИСАЛСЯ» ----------

@dp.callback_query(F.data == "check_sub")
async def check_sub(callback: CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        await callback.message.edit_text(
            "✅ Спасибо за подписку!\n\n"
            "🎯 Теперь выбери направление 👇",
            reply_markup=directions_kb()
        )
    else:
        await callback.answer(
            "❌ Подписка не найдена.\nПодпишись и нажми ещё раз.",
            show_alert=True
        )


# ---------- ВЫБОР НАПРАВЛЕНИЯ ----------

@dp.callback_query(F.data.startswith("dir_"))
async def choose_direction(callback: CallbackQuery):
    direction = callback.data.replace("dir_", "")

    await callback.message.answer(
        f"✅ Отлично!\n\n"
        f"Я буду подбирать вакансии по направлению:\n"
        f"🔥 {direction.capitalize()}\n\n"
        f"📢 Все вакансии публикуем в канале:\n"
        f"{CHANNEL_USERNAME}"
    )
    await callback.answer()


# ---------- ЗАПУСК ----------

async def main():
    print("🤖 Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
