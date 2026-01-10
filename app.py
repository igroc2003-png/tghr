import os
import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import (
    init_db, add_vacancy, get_all_vacancies,
    get_vacancy_by_id, update_vacancy, delete_vacancy
)

# ================== НАСТРОЙКИ ==================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = 5108587018

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================== FSM ==================

class AddVacancy(StatesGroup):
    photo = State()
    title = State()
    description = State()
    link = State()


class EditVacancy(StatesGroup):
    vacancy_id = State()
    photo = State()
    title = State()
    description = State()
    link = State()

# ================== КЛАВИАТУРЫ ==================

def main_keyboard(user_id: int):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]
    if user_id == HR_CHAT_ID:
        kb.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="admin_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def vacancies_keyboard():
    kb = [
        [InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")]
        for vid, title in get_all_vacancies()
    ]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def vacancy_admin_keyboard(vacancy_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{vacancy_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_confirm:{vacancy_id}")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в HR-бот",
        reply_markup=main_keyboard(message.from_user.id)
    )

# ================== АДМИН-ПАНЕЛЬ (⬅️ ВОТ ЧЕГО НЕ ХВАТАЛО) ==================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != HR_CHAT_ID:
        await callback.answer("⛔ Нет доступа")
        return

    await callback.message.answer(
        "🛠 Админ-панель",
        reply_markup=admin_keyboard()
    )
    await callback.answer()

# ================== НАВИГАЦИЯ ==================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "Главное меню",
        reply_markup=main_keyboard(callback.from_user.id)
    )
    await callback.answer()


@dp.callback_query(F.data == "vacancies")
async def show_vacancies(callback: CallbackQuery):
    await callback.message.answer(
        "📋 Список вакансий:",
        reply_markup=vacancies_keyboard()
    )
    await callback.answer()

# ================== ОСТАЛЬНОЙ КОД БЕЗ ИЗМЕНЕНИЙ ==================
# (добавление, редактирование, удаление вакансий — всё как раньше)

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
