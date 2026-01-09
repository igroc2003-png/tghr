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
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from db import (
    init_db,
    add_vacancy,
    get_all_vacancies,
    get_vacancy_by_id
)

# ================= НАСТРОЙКИ =================

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

# ================= КНОПКИ =================

def vacancies_keyboard():
    keyboard = []

    for vid, title in get_all_vacancies():
        keyboard.append([
            InlineKeyboardButton(
                text=title,
                callback_data=f"vacancy:{vid}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Назад к вакансиям", callback_data="back")]
        ]
    )

# ================= КОМАНДЫ =================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Выберите вакансию:",
        reply_markup=vacancies_keyboard()
    )


@dp.message(Command("add"))
async def add_start(message: Message, state: FSMContext):
    if message.from_user.id != HR_CHAT_ID:
        return

    await message.answer("📸 Отправь картинку вакансии")
    await state.set_state(AddVacancy.photo)


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
        title=data["title"],
        description=data["description"],
        link=message.text,
        image_id=data.get("image_id")
    )

    await message.answer("✅ Вакансия добавлена")
    await state.clear()

# ================= ПОКАЗ ВАКАНСИИ =================

@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback: CallbackQuery):
    vacancy_id = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vacancy_id)

    if not data:
        await callback.answer("Вакансия не найдена")
        return

    title, description, link, image_id = data

    text = (
        f"📌 <b>{title}</b>\n\n"
        f"{description}\n\n"
        f"🔗 {link}"
    )

    if image_id:
        await callback.message.answer_photo(
            photo=image_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

    await callback.answer()

# ================= НАЗАД =================

@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer(
        "📋 Список вакансий:",
        reply_markup=vacancies_keyboard()
    )
    await callback.answer()

# ================= ЗАПУСК =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
