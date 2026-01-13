
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import add_user_tag, get_users_by_tag

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

def categories_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚚 Доставка / Курьеры", callback_data="cat_delivery")],
        [InlineKeyboardButton(text="💻 Удалёнка", callback_data="cat_remote")],
        [InlineKeyboardButton(text="💼 Офис / Продажи", callback_data="cat_office")],
    ])

def delivery_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚴 Курьер", callback_data="tag_Курьер")],
        [InlineKeyboardButton(text="📦 Доставка", callback_data="tag_Доставка")],
        [InlineKeyboardButton(text="🕒 Подработка", callback_data="tag_Подработка")],
    ])

def remote_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Удаленка", callback_data="tag_Удаленка")],
        [InlineKeyboardButton(text="📞 CallCenter", callback_data="tag_CallCenter")],
    ])

def office_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💼 Офис", callback_data="tag_Офис")],
        [InlineKeyboardButton(text="📈 Продажи", callback_data="tag_Продажи")],
    ])

async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except:
        return False

@dp.message(CommandStart())
async def start(message: Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Подпишись на канал:\n"
            f"https://t.me/{CHANNEL_USERNAME[1:]}"
        )
        return

    await message.answer("Выбери категорию:", reply_markup=categories_kb())

@dp.callback_query(F.data == "cat_delivery")
async def cat_delivery(callback: CallbackQuery):
    await callback.message.edit_text("Доставка:", reply_markup=delivery_kb())

@dp.callback_query(F.data == "cat_remote")
async def cat_remote(callback: CallbackQuery):
    await callback.message.edit_text("Удалёнка:", reply_markup=remote_kb())

@dp.callback_query(F.data == "cat_office")
async def cat_office(callback: CallbackQuery):
    await callback.message.edit_text("Офис:", reply_markup=office_kb())

@dp.callback_query(F.data.startswith("tag_"))
async def save_tag(callback: CallbackQuery):
    tag = callback.data.replace("tag_", "")
    add_user_tag(callback.from_user.id, tag)
    await callback.message.answer(f"Тег сохранён: #{tag}")
    await callback.answer()

@dp.message(F.from_user.id == ADMIN_ID)
async def admin_post(message: Message):
    text = message.text or ""
    tags = {w[1:] for w in text.split() if w.startswith("#")}

    await bot.send_message(CHANNEL_USERNAME, text)

    sent = 0
    for tag in tags:
        for uid in get_users_by_tag(tag):
            try:
                await bot.send_message(uid, text)
                sent += 1
            except:
                pass

    await message.reply(f"Опубликовано в канале и разослано ({sent})")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
