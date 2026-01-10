import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import (
    init_db,
    add_user,
    get_users_stats_extended,
    add_vacancy,
    get_all_vacancies,
    get_vacancy_by_id,
    update_vacancy,
    delete_vacancy
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
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
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


def confirm_delete_keyboard(vacancy_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete:{vacancy_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="back")
        ]
    ])

# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id)
    await message.answer("👋 Добро пожаловать в HR-бот", reply_markup=main_keyboard(message.from_user.id))

# ================== НАВИГАЦИЯ ==================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer("Главное меню", reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer()

# ================== ВАКАНСИИ ==================

@dp.callback_query(F.data == "vacancies")
async def show_vacancies(callback: CallbackQuery):
    await callback.message.answer("📋 Вакансии:", reply_markup=vacancies_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Вакансия не найдена")
        return

    title, description, link, image_id = data
    text = f"<b>{title}</b>\n\n{description}\n\n🔗 {link}"

    markup = vacancy_admin_keyboard(vacancy_id) if callback.from_user.id == HR_CHAT_ID else None

    if image_id:
        await callback.message.answer_photo(image_id, caption=text, parse_mode="HTML", reply_markup=markup)
    else:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)

    await callback.answer()

# ================== АДМИНКА ==================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != HR_CHAT_ID:
        await callback.answer("⛔ Нет доступа")
        return

    await callback.message.answer("🛠 Админ-панель", reply_markup=admin_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    total, today, week, month = get_users_stats_extended()

    await callback.message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего: <b>{total}</b>\n"
        f"🆕 Сегодня: <b>{today}</b>\n"
        f"📈 7 дней: <b>{week}</b>\n"
        f"📊 30 дней: <b>{month}</b>",
        parse_mode="HTML"
    )
    await callback.answer()

# ================== ДОБАВЛЕНИЕ ==================

@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправь фото или `-`")
    await state.set_state(AddVacancy.photo)
    await callback.answer()


@dp.message(AddVacancy.photo)
async def add_photo(message: Message, state: FSMContext):
    if message.text == "-":
        await state.update_data(image_id=None)
    elif message.photo:
        await state.update_data(image_id=message.photo[-1].file_id)
    else:
        await message.answer("Отправь фото или `-`")
        return

    await message.answer("✏️ Название вакансии")
    await state.set_state(AddVacancy.title)


@dp.message(AddVacancy.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Описание")
    await state.set_state(AddVacancy.description)


@dp.message(AddVacancy.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("🔗 Ссылка")
    await state.set_state(AddVacancy.link)


@dp.message(AddVacancy.link)
async def add_link(message: Message, state: FSMContext):
    data = await state.get_data()
    add_vacancy(data["title"], data["description"], message.text, data.get("image_id"))
    await message.answer("✅ Вакансия добавлена")
    await state.clear()

# ================== УДАЛЕНИЕ ==================

@dp.callback_query(F.data.startswith("delete_confirm:"))
async def confirm_delete(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    await callback.message.answer("❗ Точно удалить вакансию?", reply_markup=confirm_delete_keyboard(vacancy_id))
    await callback.answer()


@dp.callback_query(F.data.startswith("delete:"))
async def delete_vac(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    delete_vacancy(vacancy_id)
    await callback.message.answer("🗑 Вакансия удалена")
    await callback.answer()

# ================== MAIN ==================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
