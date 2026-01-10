import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage

from db import (
    init_db,
    get_all_vacancies,
    get_vacancy,
    delete_vacancy,
    add_user
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= КЛАВИАТУРЫ =================

def main_keyboard(uid):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def vacancies_keyboard():
    kb = []
    for vid, title in get_all_vacancies():
        kb.append([
            InlineKeyboardButton(text=title, callback_data=f"vacancy:{vid}")
        ])
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def vacancy_admin_keyboard(vacancy_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{vacancy_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{vacancy_id}")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def confirm_delete_keyboard(vacancy_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Да, удалить",
                callback_data=f"confirm_delete:{vacancy_id}"
            ),
            InlineKeyboardButton(
                text="❌ Отмена",
                callback_data="cancel_delete"
            )
        ]
    ])

# ================= START =================

@dp.message(CommandStart())
async def start(message: Message):
    add_user(message.from_user.id)
    await message.answer("👋 Добро пожаловать", reply_markup=main_keyboard(message.from_user.id))

# ================= НАВИГАЦИЯ =================

@dp.callback_query(F.data == "vacancies")
async def show_vacancies(callback: CallbackQuery):
    await callback.message.answer("📋 Вакансии:", reply_markup=vacancies_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "back")
async def back(callback: CallbackQuery):
    await callback.message.answer("Главное меню", reply_markup=main_keyboard(callback.from_user.id))
    await callback.answer()

# ================= ПРОСМОТР =================

@dp.callback_query(F.data.startswith("vacancy:"))
async def show_vacancy(callback: CallbackQuery):
    vid = int(callback.data.split(":")[1])
    data = get_vacancy(vid)

    if not data:
        await callback.answer("Не найдено")
        return

    title, desc, link, image_id = data
    text = f"<b>{title}</b>\n\n{desc}\n\n🔗 {link}"

    if image_id:
        await callback.message.answer_photo(
            image_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vid) if callback.from_user.id == ADMIN_ID else None
        )
    else:
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=vacancy_admin_keyboard(vid) if callback.from_user.id == ADMIN_ID else None
        )

    await callback.answer()

# ================= 🗑 УДАЛЕНИЕ С ПОДТВЕРЖДЕНИЕМ =================

@dp.callback_query(F.data.startswith("delete:"))
async def delete_request(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔", show_alert=True)
        return

    vid = int(callback.data.split(":")[1])

    await callback.message.answer(
        "⚠️ Ты уверен, что хочешь удалить вакансию?",
        reply_markup=confirm_delete_keyboard(vid)
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_delete:"))
async def delete_confirmed(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔", show_alert=True)
        return

    vid = int(callback.data.split(":")[1])
    delete_vacancy(vid)

    await callback.message.answer("🗑 Вакансия удалена")
    await callback.answer()


@dp.callback_query(F.data == "cancel_delete")
async def delete_cancel(callback: CallbackQuery):
    await callback.message.answer("❌ Удаление отменено")
    await callback.answer()

# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
