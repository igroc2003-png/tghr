import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_NUMERIC_ID, ADMIN_ID
from db import (
    save_user_tags,
    get_all_users,
    count_users,
    can_send,
    block_user
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= KEYBOARDS =================
def admin_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🎯 Рассылка по тегу", callback_data="admin_tag")],
        ]
    )


# ================= ADMIN CHECK =================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ================= /admin =================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "🔥 Админ-панель",
        reply_markup=admin_kb()
    )


# ================= STATS =================
@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    total = count_users()

    await call.message.edit_text(
        f"📊 Статистика:\n\n"
        f"👥 Пользователей: {total}",
        reply_markup=admin_kb()
    )


# ================= BROADCAST =================
@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state("broadcast_text")
    await call.message.edit_text("📢 Отправь текст рассылки:")


@dp.message(F.text, state="broadcast_text")
async def send_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text
    users = get_all_users()

    sent = 0
    for user_id, _ in users:
        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.5)
        except:
            block_user(user_id)

    await message.answer(f"✅ Рассылка завершена\nОтправлено: {sent}")
    await state.clear()


# ================= TAG BROADCAST =================
@dp.callback_query(F.data == "admin_tag")
async def admin_tag(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state("tag_name")
    await call.message.edit_text("🎯 Введи тег (например: remote):")


@dp.message(F.text, state="tag_name")
async def tag_name(message: Message, state: FSMContext):
    await state.update_data(tag=message.text.lower())
    await state.set_state("tag_text")
    await message.answer("✍️ Введи текст рассылки:")


@dp.message(F.text, state="tag_text")
async def send_tag_broadcast(message: Message, state: FSMContext):
    data = await state.get_data()
    tag = data["tag"]
    text = message.text

    users = get_all_users()
    sent = 0

    for user_id, tags_str in users:
        if tag not in tags_str:
            continue

        try:
            await bot.send_message(user_id, text)
            sent += 1
            await asyncio.sleep(0.6)
        except:
            block_user(user_id)

    await message.answer(f"✅ Отправлено по тегу «{tag}»: {sent}")
    await state.clear()


# ================= RUN =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
