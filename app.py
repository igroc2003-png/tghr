import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db import (
    init_db,
    add_vacancy,
    get_all_vacancies,
    get_vacancy_by_id,
    update_vacancy,
    delete_vacancy
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = 5108587018  # твой Telegram ID

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ================= FSM =================

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


# ================= КНОПКИ =================

def main_keyboard(user_id):
    keyboard = []

    for vid, title in get_all_vacancies():
        keyboard.append([
            InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")
        ])

    if user_id == HR_CHAT_ID:
        keyboard.append([
            InlineKeyboardButton("🛠 Админ-панель", callback_data="admin")
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def admin_panel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton("➕ Добавить вакансию", callback_data="admin_add")],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]
    )


def admin_vacancy_keyboard(vacancy_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{vacancy_id}"),
                InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{vacancy_id}")
            ],
            [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
        ]
    )


def user_vacancy_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton("⬅️ Назад", callback_data="back")]]
    )


# ================= START =================

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "📋 Актуальные вакансии:",
        reply_markup=main_keyboard(message.from_user.id)
    )


# ================= АДМИН-ПАНЕЛЬ =================

@dp.callback_query(F.data == "admin")
async def admin_panel(callback: CallbackQuery):
    if callback.from_user.id != HR_CHAT_ID:
        return

    await callback.message.answer(
        "🛠 Админ-панель",
        reply_markup=admin_panel_keyboard()
    )
    await callback.answer()


# ================= ДОБАВИТЬ =================

@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправь картинку вакансии")
    await state.set_state(AddVacancy.photo)
    await callback.answer()


@dp.message(AddVacancy.photo, F.photo)
async def add_photo(message: Message, state: FSMContext):
    await state.update_data(image_id=message.photo[-1].file_id)
    await message.answer("✏️ Название вакансии")
    await state.set_state(AddVacancy.title)


@dp.message(AddVacancy.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Описание вакансии")
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
        data["image_id"]
    )

    await message.answer("✅ Вакансия добавлена")
    await state.clear()


# ================= ПОКАЗ =================

@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Не найдено")
        return

    title, description, link, image_id = data
    text = f"<b>{title}</b>\n\n{description}\n\n🔗 {link}"

    keyboard = (
        admin_vacancy_keyboard(vacancy_id)
        if callback.from_user.id == HR_CHAT_ID
        else user_vacancy_keyboard()
    )

    if image_id:
        await callback.message.answer_photo(
            photo=image_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )

    await callback.answer()


# ================= УДАЛИТЬ =================

@dp.callback_query(F.data.startswith("delete:"))
async def delete_vac(callback: CallbackQuery):
    if callback.from_user.id != HR_CHAT_ID:
        return

    vacancy_id = int(callback.data.split(":")[1])
    delete_vacancy(vacancy_id)

    await callback.message.answer("🗑 Вакансия удалена")
    await callback.answer()


# ================= НАЗАД =================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "📋 Актуальные вакансии:",
        reply_markup=main_keyboard(callback.from_user.id)
    )
    await callback.answer()


# ================= RUN =================

async def main():
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
