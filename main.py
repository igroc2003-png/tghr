import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_NUMERIC_ID, ADMIN_ID
from smart_tags import extract_tags
from db import save_user, get_users, save_vacancy, count_users, count_vacancies

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

class AddVacancy(StatesGroup):
    waiting_text = State()

def interests_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🐍 Python", callback_data="interest_python")],
        [InlineKeyboardButton(text="🎨 Дизайн", callback_data="interest_designer")],
        [InlineKeyboardButton(text="📊 Менеджмент", callback_data="interest_manager")]
    ])

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="admin_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")]
    ])

@dp.message(CommandStart())
async def start(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        await msg.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await msg.answer("👋 Я бесплатно подбираю вакансии по интересам", reply_markup=interests_kb())

@dp.callback_query(F.data.startswith("interest_"))
async def save_interest(call: CallbackQuery):
    save_user(call.from_user.id, call.data.replace("interest_", ""))
    await call.message.edit_text("✅ Интерес сохранён")

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await call.message.answer(
        f"📊 Статистика\n\n👥 Пользователей: {count_users()}\n📄 Вакансий: {count_vacancies()}"
    )

@dp.callback_query(F.data == "admin_add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        return
    await state.set_state(AddVacancy.waiting_text)
    await call.message.answer("✍️ Отправь текст вакансии")

@dp.message(AddVacancy.waiting_text)
async def add_vacancy(msg: Message, state: FSMContext):
    text = msg.text
    tags = extract_tags(text)

    save_vacancy(text, str(tags))

    await bot.send_message(
        CHANNEL_NUMERIC_ID,
        f"🔥 Новая вакансия\n\n{text}\n\n🏷 {tags['profession']} | {tags['level']} | {tags['format']}"
    )

    sent = 0
    for user_id, interest in get_users():
        if interest == tags["profession"]:
            try:
                await bot.send_message(user_id, f"🔥 Вакансия:\n\n{text}")
                sent += 1
                await asyncio.sleep(0.4)
            except:
                pass

    await msg.answer(f"✅ Вакансия добавлена\n📨 Отправлено: {sent}", reply_markup=admin_kb())
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
