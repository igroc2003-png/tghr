import os
import asyncio
import logging

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
    init_db, add_user, get_users_stats,
    get_all_vacancies, get_vacancy_by_id,
    add_vacancy, update_vacancy, delete_vacancy,
    notifications_enabled, toggle_notifications
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

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

# ================= KEYBOARDS =================

def main_keyboard(uid):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_keyboard():
    notif = "🔔 ВКЛ" if notifications_enabled() else "🔕 ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="admin_add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text=f"Уведомления {notif}", callback_data="toggle_notifications")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def vacancies_keyboard():
    kb = [
        [InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")]
        for vid, title in get_all_vacancies()
    ]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def vacancy_admin_keyboard(vid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{vid}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{vid}")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def confirm_delete_keyboard(vid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Нет", callback_data="back"),
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete:{vid}")
        ]
    ])

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    is_new = add_user(message.from_user.id)

    if is_new and notifications_enabled() and message.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"👤 Новый пользователь: {message.from_user.id}")

    await message.answer("👋 Добро пожаловать", reply_markup=main_keyboard(message.from_user.id))

# ================= VACANCIES =================

@dp.callback_query(F.data == "vacancies")
async def vacancies(callback: CallbackQuery):
    await callback.message.answer("📋 Вакансии:", reply_markup=vacancies_keyboard())
    await callback.answer()


@dp.callback_query(F.data.startswith("vacancy:"))
async def vacancy(callback: CallbackQuery):
    vid = int(callback.data.split(":")[1])
    data = get_vacancy_by_id(vid)
    if not data:
        await callback.answer("Не найдено")
        return

    title, desc, link, image = data
    text = f"<b>{title}</b>\n\n{desc}\n\n🔗 {link}"

    if image:
        await callback.message.answer_photo(
            image, caption=text, parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vid) if callback.from_user.id == ADMIN_ID else None
        )
    else:
        await callback.message.answer(
            text, parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vid) if callback.from_user.id == ADMIN_ID else None
        )
    await callback.answer()

# ================= ADD =================

@dp.callback_query(F.data == "admin_add")
async def admin_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Фото или `-`")
    await state.set_state(AddVacancy.photo)
    await callback.answer()


@dp.message(AddVacancy.photo)
async def add_photo(message: Message, state: FSMContext):
    if message.text == "-":
        await state.update_data(image_id=None)
    elif message.photo:
        await state.update_data(image_id=message.photo[-1].file_id)
    else:
        return await message.answer("Фото или `-`")

    await message.answer("✏️ Название")
    await state.set_state(AddVacancy.title)


@dp.message(AddVacancy.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Описание")
    await state.set_state(AddVacancy.description)


@dp.message(AddVacancy.description)
async def add_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("🔗 Ссылка")
    await state.set_state(AddVacancy.link)


@dp.message(AddVacancy.link)
async def add_link(message: Message, state: FSMContext):
    data = await state.get_data()
    add_vacancy(data["title"], data["description"], message.text, data["image_id"])
    await message.answer("✅ Вакансия добавлена")
    await state.clear()

# ================= EDIT =================

@dp.callback_query(F.data.startswith("edit:"))
async def edit_start(callback: CallbackQuery, state: FSMContext):
    vid = int(callback.data.split(":")[1])
    await state.update_data(vacancy_id=vid)
    await callback.message.answer("📸 Новое фото или `-`")
    await state.set_state(EditVacancy.photo)
    await callback.answer()


@dp.message(EditVacancy.photo)
async def edit_photo(message: Message, state: FSMContext):
    if message.text == "-":
        await state.update_data(image_id=None)
    elif message.photo:
        await state.update_data(image_id=message.photo[-1].file_id)
    else:
        return await message.answer("Фото или `-`")

    await message.answer("✏️ Новое название")
    await state.set_state(EditVacancy.title)


@dp.message(EditVacancy.title)
async def edit_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📝 Новое описание")
    await state.set_state(EditVacancy.description)


@dp.message(EditVacancy.description)
async def edit_desc(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("🔗 Новая ссылка")
    await state.set_state(EditVacancy.link)


@dp.message(EditVacancy.link)
async def edit_link(message: Message, state: FSMContext):
    data = await state.get_data()
    update_vacancy(
        data["vacancy_id"],
        data["title"],
        data["description"],
        message.text,
        data["image_id"]
    )
    await message.answer("✏️ Вакансия обновлена")
    await state.clear()

# ================= DELETE =================

@dp.callback_query(F.data.startswith("delete:"))
async def delete_confirm(callback: CallbackQuery):
    vid = int(callback.data.split(":")[1])
    await callback.message.answer(
        "⚠️ Удалить вакансию?",
        reply_markup=confirm_delete_keyboard(vid)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_delete:"))
async def delete_yes(callback: CallbackQuery):
    vid = int(callback.data.split(":")[1])
    delete_vacancy(vid)
    await callback.message.answer("🗑 Вакансия удалена")
    await callback.answer()

# ================= STATS =================

@dp.callback_query(F.data == "admin_stats")
async def stats(callback: CallbackQuery):
    t, d, w, m = get_users_stats()
    await callback.message.answer(
        f"📊 Статистика\n\n👥 {t}\n🆕 {d}\n📈 {w}\n📊 {m}"
    )
    await callback.answer()

# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
