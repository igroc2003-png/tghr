
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

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_vacancy")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notify")],
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
        c.execute("INSERT OR IGNORE INTO users VALUES (?,?)",
                  (m.from_user.id, datetime.now().date()))
        notify = c.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]

    if notify and m.from_user.id != ADMIN_ID:
        await bot.send_message(ADMIN_ID, f"👤 Новый пользователь: {m.from_user.id}")

    await m.answer("Добро пожаловать", reply_markup=main_kb(m.from_user.id))

# ================= NAV =================

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.message.answer("Главное меню", reply_markup=main_kb(c.from_user.id))

@dp.callback_query(F.data == "admin")
async def admin(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        return
    await c.message.answer("Админ панель", reply_markup=admin_kb())

# ================= VACANCIES =================

@dp.callback_query(F.data == "vacancies")
async def vacancies(c: CallbackQuery):
    with db() as conn:
        rows = conn.execute("SELECT id, title FROM vacancies").fetchall()

    kb = [[InlineKeyboardButton(text=t, callback_data=f"vac:{i}")] for i, t in rows]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    await c.message.answer("Вакансии:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

@dp.callback_query(F.data.startswith("vac:"))
async def vacancy(c: CallbackQuery):
    vid = int(c.data.split(":")[1])
    with db() as conn:
        v = conn.execute(
            "SELECT title, description, link, image_id FROM vacancies WHERE id=?",
            (vid,)
        ).fetchone()

    text = f"<b>{v[0]}</b>\n\n{v[1]}\n\n{v[2]}"
    if v[3]:
        await c.message.answer_photo(v[3], caption=text, parse_mode="HTML",
            reply_markup=vacancy_admin_kb(vid) if c.from_user.id == ADMIN_ID else None)
    else:
        await c.message.answer(text, parse_mode="HTML",
            reply_markup=vacancy_admin_kb(vid) if c.from_user.id == ADMIN_ID else None)

# ================= ADD FSM =================

@dp.callback_query(F.data == "add_vacancy")
async def add_start(c: CallbackQuery, s: FSMContext):
    await s.set_state(AddVacancy.photo)
    await c.message.answer("Фото или -", reply_markup=cancel_kb())

@dp.message(AddVacancy.photo)
async def add_photo(m: Message, s: FSMContext):
    if m.text == "-":
        await s.update_data(image_id=None)
    elif m.photo:
        await s.update_data(image_id=m.photo[-1].file_id)
    else:
        return await m.answer("Фото или -")
    await s.set_state(AddVacancy.title)
    await m.answer("Название", reply_markup=cancel_kb())

@dp.message(AddVacancy.title)
async def add_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(AddVacancy.description)
    await m.answer("Описание", reply_markup=cancel_kb())

@dp.message(AddVacancy.description)
async def add_desc(m: Message, s: FSMContext):
    await s.update_data(description=m.text)
    await s.set_state(AddVacancy.link)
    await m.answer("Ссылка", reply_markup=cancel_kb())

@dp.message(AddVacancy.link)
async def add_link(m: Message, s: FSMContext):
    d = await s.get_data()
    with db() as c:
        c.execute(
            "INSERT INTO vacancies VALUES (NULL,?,?,?,?)",
            (d["title"], d["description"], m.text, d["image_id"])
        )
    await s.clear()
    await m.answer("✅ Вакансия добавлена", reply_markup=main_kb(m.from_user.id))

# ================= EDIT FSM =================

@dp.callback_query(F.data.startswith("edit:"))
async def edit_start(c: CallbackQuery, s: FSMContext):
    vid = int(c.data.split(":")[1])
    await s.update_data(vid=vid)
    await s.set_state(EditVacancy.photo)
    await c.message.answer("Новое фото или -", reply_markup=cancel_kb())

@dp.message(EditVacancy.photo)
async def edit_photo(m: Message, s: FSMContext):
    if m.text == "-":
        pass
    elif m.photo:
        await s.update_data(image_id=m.photo[-1].file_id)
    else:
        return await m.answer("Фото или -")
    await s.set_state(EditVacancy.title)
    await m.answer("Новое название", reply_markup=cancel_kb())

@dp.message(EditVacancy.title)
async def edit_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(EditVacancy.description)
    await m.answer("Новое описание", reply_markup=cancel_kb())

@dp.message(EditVacancy.description)
async def edit_desc(m: Message, s: FSMContext):
    await s.update_data(description=m.text)
    await s.set_state(EditVacancy.link)
    await m.answer("Новая ссылка", reply_markup=cancel_kb())

@dp.message(EditVacancy.link)
async def edit_link(m: Message, s: FSMContext):
    d = await s.get_data()
    with db() as c:
        c.execute("""UPDATE vacancies
            SET title=?, description=?, link=?, image_id=COALESCE(?, image_id)
            WHERE id=?""", (d["title"], d["description"], m.text, d.get("image_id"), d["vid"]))
    await s.clear()
    await m.answer("✏️ Обновлено", reply_markup=main_kb(m.from_user.id))

# ================= DELETE =================

@dp.callback_query(F.data.startswith("del:"))
async def delete_confirm(c: CallbackQuery):
    vid = int(c.data.split(":")[1])
    await c.message.answer("Удалить вакансию?", reply_markup=confirm_delete_kb(vid))

@dp.callback_query(F.data.startswith("del_yes:"))
async def delete_yes(c: CallbackQuery):
    vid = int(c.data.split(":")[1])
    with db() as conn:
        conn.execute("DELETE FROM vacancies WHERE id=?", (vid,))
    await c.message.answer("🗑 Удалено", reply_markup=main_kb(c.from_user.id))

# ================= STATS =================

@dp.callback_query(F.data == "stats")
async def stats(c: CallbackQuery):
    today = datetime.now().date()
    with db() as conn:
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        d1 = cur.execute("SELECT COUNT(*) FROM users WHERE joined=?", (today,)).fetchone()[0]
        d7 = cur.execute("SELECT COUNT(*) FROM users WHERE joined>=?",
                         (today - timedelta(days=7),)).fetchone()[0]
        d30 = cur.execute("SELECT COUNT(*) FROM users WHERE joined>=?",
                          (today - timedelta(days=30),)).fetchone()[0]

    await c.message.answer(
        f"📊 Статистика\n"
        f"Сегодня: {d1}\n7 дней: {d7}\n30 дней: {d30}\nВсего: {total}"
    )

# ================= NOTIFY =================

@dp.callback_query(F.data == "notify")
async def toggle_notify(c: CallbackQuery):
    with db() as conn:
        cur = conn.cursor()
        val = cur.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]
        new = 0 if val else 1
        cur.execute("UPDATE settings SET value=? WHERE key='notify_users'", (new,))

    await c.message.answer(
        "🔔 Уведомления ВКЛ" if new else "🔕 Уведомления ВЫКЛ"
    )

@dp.callback_query(F.data == "cancel")
async def cancel(c: CallbackQuery, s: FSMContext):
    await s.clear()
    await c.message.answer("Отменено", reply_markup=main_kb(c.from_user.id))

# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
