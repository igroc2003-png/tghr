import asyncio
from typing import Set

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, ADMIN_ID, CHANNEL_USERNAME
from db import (
    init_db,
    get_users_by_interests,
    get_all_users,
    save_stat_delivery,
)

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

INTERESTS = {
    "Курьеры": "🚚 Доставка / Курьеры",
    "Магазины": "🏪 Магазины / Склады",
    "Фастфуд": "🍔 Фастфуд",
    "Коллцентр": "📞 Call-центр",
    "Клининг": "🧹 Клининг",
    "Мастер": "🏗 Мастер / Отделка",
    "Офис": "💼 Офис / Продажи",
    "Финансы": "🏦 Банк / Финансы",
    "Учитель": "👨🏫 Преподаватель",
    "Водитель": "🚗 Водитель / Такси",
    "Удаленка": "💻 Удалёнка",
    "Подработка": "⏱️ Подработка",
}

class AdminForm(StatesGroup):
    waiting_job = State()
    waiting_post = State()
    preview = State()

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")],
        [InlineKeyboardButton(text="📝 Добавить пост", callback_data="add_post")],
    ])

def preview_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    ])

@router.message(CommandStart())
async def start(m: Message):
    if m.from_user.id == ADMIN_ID:
        await m.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await m.answer("👋 Бот вакансий")

@router.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminForm.waiting_job)
    await cb.message.answer("✍️ Отправь текст вакансии (теги добавятся автоматически)")
    await cb.answer()

@router.callback_query(F.data == "add_post")
async def add_post(cb: CallbackQuery, state: FSMContext):
    await state.set_state(AdminForm.waiting_post)
    await cb.message.answer("📝 Отправь пост (будет разослан всем)")
    await cb.answer()

@router.message(AdminForm.waiting_job)
async def job_text(m: Message, state: FSMContext):
    auto_tags = [k for k in INTERESTS if k.lower() in m.text.lower()]
    text = m.html_text + "\n\n" + " ".join(f"#{t}" for t in auto_tags)

    await state.update_data(text=text, photo=m.photo[-1].file_id if m.photo else None, tags=auto_tags, mode="job")
    await state.set_state(AdminForm.preview)

    if m.photo:
        await m.answer_photo(m.photo[-1].file_id, caption=text, reply_markup=preview_kb())
    else:
        await m.answer(text, reply_markup=preview_kb())

@router.message(AdminForm.waiting_post)
async def post_text(m: Message, state: FSMContext):
    await state.update_data(text=m.html_text, photo=m.photo[-1].file_id if m.photo else None, mode="post")
    await state.set_state(AdminForm.preview)

    if m.photo:
        await m.answer_photo(m.photo[-1].file_id, caption=m.html_text, reply_markup=preview_kb())
    else:
        await m.answer(m.html_text, reply_markup=preview_kb())

@router.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.answer("❌ Отменено")
    await cb.answer()

@router.callback_query(F.data == "publish")
async def publish(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data["text"]
    photo = data.get("photo")
    mode = data["mode"]

    if mode == "job":
        users = get_users_by_interests(data["tags"])
    else:
        users = get_all_users()

    delivered = 0
    for uid in users:
        try:
            if photo:
                await bot.send_photo(uid, photo, caption=text)
            else:
                await bot.send_message(uid, text)
            delivered += 1
            save_stat_delivery(uid)
        except:
            pass

    # канал
    if photo:
        await bot.send_photo(CHANNEL_USERNAME, photo, caption=text)
    else:
        await bot.send_message(CHANNEL_USERNAME, text)

    await state.clear()
    await cb.message.answer(f"✅ Опубликовано и разослано: {delivered}")
    await cb.answer()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
