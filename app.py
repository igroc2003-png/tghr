import os
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018
DB_NAME = "bot.db"

logging.basicConfig(level=logging.INFO)

# ================= DB =================

def db():
    return sqlite3.connect(DB_NAME)

def init_db():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            link TEXT,
            image_id TEXT
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined DATE
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('notify_users', 1)")
        c.commit()

# ================= FSM =================

class AddVacancy(StatesGroup):
    photo = State()
    title = State()
    description = State()
    link = State()

class EditVacancy(StatesGroup):
    photo = State()
    title = State()
    description = State()
    link = State()

# ================= BOT =================

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= KEYBOARDS =================

def main_kb(uid):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="🛠 Админ", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_kb(notify_enabled: bool):
    notify_text = "🔔 Уведомления" if notify_enabled else "🔕 Уведомления"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_vacancy")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text=notify_text, callback_data="notify")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])

def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
    ])

def vacancy_admin_kb(vid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{vid}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del:{vid}")
        ],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="vacancies")]
    ])

def confirm_delete_kb(vid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"del_yes:{vid}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="vacancies")
        ]
    ])

# ================= START =================

@dp.message(CommandStart())
async def start(m: Message):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO users VALUES (?,?)",
            (m.from_user.id, datetime.now().date())
        )
        notify = c.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]
        c.commit()

    if notify and m.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"👤 Новый пользователь: {m.from_user.id}")

    await m.answer("Добро пожаловать", reply_markup=main_kb(m.from_user.id))

# ================= NAV =================

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.answer()
    await c.message.answer("Главное меню", reply_markup=main_kb(c.from_user.id))

@dp.callback_query(F.data == "admin")
async def admin(c: CallbackQuery):
    await c.answer()
    if c.from_user.id != ADMIN_ID:
        return

    with db() as conn:
        notify = conn.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]

    await c.message.answer(
        "Админ панель",
        reply_markup=admin_kb(bool(notify))
    )

# ================= VACANCIES =================

@dp.callback_query(F.data == "vacancies")
async def vacancies(c: CallbackQuery):
    await c.answer()
    with db() as conn:
        rows = conn.execute("SELECT id, title FROM vacancies").fetchall()

    kb = [[InlineKeyboardButton(text=t, callback_data=f"vac:{i}")] for i, t in rows]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    await c.message.answer("Вакансии:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("vac:"))
async def vacancy(c: CallbackQuery):
    await c.answer()
    vid = int(c.data.split(":")[1])

    with db() as conn:
        v = conn.execute(
            "SELECT title, description, link, image_id FROM vacancies WHERE id=?",
            (vid,)
        ).fetchone()

    text = f"<b>{v[0]}</b>\n\n{v[1]}\n\n{v[2]}"
    if v[3]:
        await c.message.answer_photo(
            v[3], caption=text, parse_mode="HTML",
            reply_markup=vacancy_admin_kb(vid) if c.from_user.id == ADMIN_ID else None
        )
    else:
        await c.message.answer(
            text, parse_mode="HTML",
            reply_markup=vacancy_admin_kb(vid) if c.from_user.id == ADMIN_ID else None
        )

# ================= NOTIFY =================

@dp.callback_query(F.data == "notify")
async def toggle_notify(c: CallbackQuery):
    await c.answer()

    with db() as conn:
        cur = conn.cursor()
        val = cur.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]
        new = 0 if val else 1
        cur.execute(
            "UPDATE settings SET value=? WHERE key='notify_users'",
            (new,)
        )
        conn.commit()

    await c.message.edit_reply_markup(
        reply_markup=admin_kb(bool(new))
    )

# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
