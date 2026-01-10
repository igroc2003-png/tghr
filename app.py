import os
import asyncio
import logging
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ================= CONFIG =================

BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "YOUR_BOT_USERNAME"  # без @
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
            image_id TEXT,
            archived INTEGER DEFAULT 0
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined DATE
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value INTEGER
        )""")
        c.execute("""CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY
        )""")
        c.execute("INSERT OR IGNORE INTO settings VALUES ('notify_users', 1)")
        c.commit()

# ================= FSM =================

class AddVacancy(StatesGroup):
    photo = State()
    title = State()
    description = State()
    link = State()

# ================= BOT =================

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ================= HELPERS =================

def notify_enabled():
    with db() as c:
        return c.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0] == 1

def is_subscribed(uid):
    with db() as c:
        return c.execute(
            "SELECT 1 FROM subscriptions WHERE user_id=?",
            (uid,)
        ).fetchone() is not None

# ================= KEYBOARDS =================

def main_kb(uid):
    kb = [[InlineKeyboardButton("📋 Вакансии", callback_data="vacancies")]]

    sub_text = "❌ Отписаться от вакансий" if is_subscribed(uid) else "📩 Подписаться на вакансии"
    kb.append([InlineKeyboardButton(sub_text, callback_data="toggle_sub")])

    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 Админ", callback_data="admin")])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_kb():
    bell = "🔔 Уведомления" if notify_enabled() else "🔕 Уведомления"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ Добавить вакансию", callback_data="add_vacancy")],
        [InlineKeyboardButton(bell, callback_data="notify")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

def vacancy_kb(vid, title, is_admin=False):
    share_url = f"https://t.me/share/url?url=https://t.me/{BOT_USERNAME}&text=🔥 {title}"

    kb = []
    if is_admin:
        kb.append([
            InlineKeyboardButton("🗄 В архив", callback_data=f"archive:{vid}")
        ])

    kb.append([InlineKeyboardButton("📤 Поделиться вакансией", url=share_url)])
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="vacancies")])

    return InlineKeyboardMarkup(inline_keyboard=kb)

# ================= START =================

@dp.message(CommandStart())
async def start(m: Message):
    with db() as c:
        c.execute(
            "INSERT OR IGNORE INTO users VALUES (?,?)",
            (m.from_user.id, datetime.now().date())
        )
        c.commit()

    await m.answer("Добро пожаловать", reply_markup=main_kb(m.from_user.id))

# ================= BACK =================

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.answer()
    await c.message.answer("Главное меню", reply_markup=main_kb(c.from_user.id))

# ================= SUBSCRIBE =================

@dp.callback_query(F.data == "toggle_sub")
async def toggle_sub(c: CallbackQuery):
    await c.answer()
    with db() as conn:
        if is_subscribed(c.from_user.id):
            conn.execute("DELETE FROM subscriptions WHERE user_id=?", (c.from_user.id,))
        else:
            conn.execute("INSERT OR IGNORE INTO subscriptions VALUES (?)", (c.from_user.id,))
        conn.commit()

    await c.message.edit_reply_markup(reply_markup=main_kb(c.from_user.id))

# ================= ADMIN =================

@dp.callback_query(F.data == "admin")
async def admin(c: CallbackQuery):
    await c.answer()
    if c.from_user.id == ADMIN_ID:
        await c.message.answer("Админ панель", reply_markup=admin_kb())

@dp.callback_query(F.data == "notify")
async def toggle_notify(c: CallbackQuery):
    await c.answer()
    with db() as conn:
        val = conn.execute(
            "SELECT value FROM settings WHERE key='notify_users'"
        ).fetchone()[0]
        new = 0 if val else 1
        conn.execute(
            "UPDATE settings SET value=? WHERE key='notify_users'",
            (new,)
        )
        conn.commit()

    await c.message.edit_reply_markup(reply_markup=admin_kb())

# ================= VACANCIES =================

@dp.callback_query(F.data == "vacancies")
async def vacancies(c: CallbackQuery):
    await c.answer()
    with db() as conn:
        rows = conn.execute(
            "SELECT id, title FROM vacancies WHERE archived=0 ORDER BY id DESC"
        ).fetchall()

    kb = [[InlineKeyboardButton(t, callback_data=f"vac:{i}")] for i, t in rows]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])

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
    kb = vacancy_kb(vid, v[0], c.from_user.id == ADMIN_ID)

    if v[3]:
        await c.message.answer_photo(v[3], caption=text, parse_mode="HTML", reply_markup=kb)
    else:
        await c.message.answer(text, parse_mode="HTML", reply_markup=kb)

# ================= ARCHIVE =================

@dp.callback_query(F.data.startswith("archive:"))
async def archive(c: CallbackQuery):
    await c.answer()
    vid = int(c.data.split(":")[1])
    with db() as conn:
        conn.execute("UPDATE vacancies SET archived=1 WHERE id=?", (vid,))
        conn.commit()

    await c.message.answer("🗄 Вакансия отправлена в архив", reply_markup=admin_kb())

# ================= ADD VACANCY =================

@dp.callback_query(F.data == "add_vacancy")
async def add_start(c: CallbackQuery, state: FSMContext):
    await c.answer()
    await state.set_state(AddVacancy.photo)
    await c.message.answer("Фото или -")

@dp.message(AddVacancy.photo)
async def add_photo(m: Message, state: FSMContext):
    if m.text == "-":
        await state.update_data(image_id=None)
    elif m.photo:
        await state.update_data(image_id=m.photo[-1].file_id)
    else:
        return

    await state.set_state(AddVacancy.title)
    await m.answer("Название")

@dp.message(AddVacancy.title)
async def add_title(m: Message, state: FSMContext):
    await state.update_data(title=m.text)
    await state.set_state(AddVacancy.description)
    await m.answer("Описание")

@dp.message(AddVacancy.description)
async def add_desc(m: Message, state: FSMContext):
    await state.update_data(description=m.text)
    await state.set_state(AddVacancy.link)
    await m.answer("Ссылка")

@dp.message(AddVacancy.link)
async def add_link(m: Message, state: FSMContext):
    data = await state.get_data()

    with db() as c:
        c.execute(
            "INSERT INTO vacancies VALUES (NULL,?,?,?,?,0)",
            (data["title"], data["description"], m.text, data["image_id"])
        )
        c.commit()

    # уведомления
    if notify_enabled():
        with db() as c:
            users = c.execute("SELECT user_id FROM subscriptions").fetchall()

        text = f"🔥 Новая вакансия\n\n{data['title']}\n\n{data['description']}\n\n{m.text}"

        for (uid,) in users:
            if uid == ADMIN_ID:
                continue
            try:
                await bot.send_message(uid, text)
                await asyncio.sleep(0.05)
            except:
                pass

    await state.clear()
    await m.answer("✅ Вакансия добавлена", reply_markup=main_kb(m.from_user.id))

# ================= MAIN =================

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
