import os
import logging
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
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
    keyboard = [[
        InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")
    ]]
    if user_id == HR_CHAT_ID:
        keyboard.append([
            InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="admin_add")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def vacancies_keyboard():
    keyboard = [
        [InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")]
        for vid, title in get_all_vacancies()
    ]
    keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_yes:{vacancy_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="delete_no")
        ]
    ])

# ================== START ==================

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в HR-бот",
        reply_markup=main_keyboard(message.from_user.id)
    )

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

# ================== ВАКАНСИЯ ==================

@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Вакансия не найдена")
        return

    title, description, link, image_id = data
    text = f"📌 <b>{title}</b>\n\n{description}\n\n🔗 {link}"

    if image_id:
        await callback.message.answer_photo(
            photo=image_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vacancy_id)
            if callback.from_user.id == HR_CHAT_ID else None
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vacancy_id)
            if callback.from_user.id == HR_CHAT_ID else None
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

    add_vacancy(
        data["title"],
        data["description"],
        message.text,
        data.get("image_id")
    )

    await message.answer("✅ Вакансия добавлена")
    await state.clear()

# ================== РЕДАКТИРОВАНИЕ ==================

@dp.callback_query(F.data.startswith("edit:"))
async def edit_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != HR_CHAT_ID:
        await callback.answer("⛔ Нет доступа")
        return

    vacancy_id = int(callback.data.split(":")[1])
    title, desc, link, image_id = get_vacancy_by_id(vacancy_id)

    await state.update_data(
        vacancy_id=vacancy_id,
        old_title=title,
        old_description=desc,
        old_link=link,
        old_image_id=image_id
    )

    await callback.message.answer("📸 Новая картинка или `-` (оставить старую)")
    await state.set_state(EditVacancy.photo)
    await callback.answer()


@dp.message(EditVacancy.photo)
async def edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()

    if message.text == "-":
        image_id = data["old_image_id"]
    elif message.photo:
        image_id = message.photo[-1].file_id
    else:
        await message.answer("Отправь фото или `-`")
        return

    await state.update_data(image_id=image_id)
    await message.answer("✏️ Новое название или `-`")
    await state.set_state(EditVacancy.title)


@dp.message(EditVacancy.title)
async def edit_title(message: Message, state: FSMContext):
    data = await state.get_data()
    title = data["old_title"] if message.text == "-" else message.text

    await state.update_data(title=title)
    await message.answer("📝 Новое описание или `-`")
    await state.set_state(EditVacancy.description)


@dp.message(EditVacancy.description)
async def edit_description(message: Message, state: FSMContext):
    data = await state.get_data()
    description = data["old_description"] if message.text == "-" else message.text

    await state.update_data(description=description)
    await message.answer("🔗 Новая ссылка или `-`")
    await state.set_state(EditVacancy.link)


@dp.message(EditVacancy.link)
async def edit_link(message: Message, state: FSMContext):
    data = await state.get_data()
    link = data["old_link"] if message.text == "-" else message.text

    update_vacancy(
        data["vacancy_id"],
        data["title"],
        data["description"],
        link,
        data["image_id"]
    )

    await message.answer("✅ Вакансия обновлена")
    await state.clear()

# ================== УДАЛЕНИЕ ==================

@dp.callback_query(F.data.startswith("delete_confirm:"))
async def delete_confirm(callback: CallbackQuery):
    if callback.from_user.id != HR_CHAT_ID:
        await callback.answer("⛔ Нет доступа")
        return

    vacancy_id = int(callback.data.split(":")[1])

    await callback.message.answer(
        "⚠️ Точно удалить вакансию?",
        reply_markup=confirm_delete_keyboard(vacancy_id)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("delete_yes:"))
async def delete_yes(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    delete_vacancy(vacancy_id)

    await callback.message.answer("🗑 Вакансия удалена")
    await callback.answer()


@dp.callback_query(F.data == "delete_no")
async def delete_no(callback: CallbackQuery):
    await callback.message.answer("❌ Удаление отменено")
    await callback.answer()

# ================== MAIN ==================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
