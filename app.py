import asyncio
import os
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from db import *

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018

logging.basicConfig(level=logging.INFO)

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ---------- FSM ----------

class AddVacancyFSM(StatesGroup):
    title = State()
    desc = State()
    link = State()


class EditVacancyFSM(StatesGroup):
    vid = State()
    title = State()
    desc = State()
    link = State()


# ---------- KEYBOARDS ----------

def main_kb(uid):
    kb = [[InlineKeyboardButton(text="📋 Вакансии", callback_data="vacancies")]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton(text="🛠 Админ-панель", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def admin_kb():
    notif = "🔔 ВКЛ" if notifications_enabled() else "🔕 ВЫКЛ"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text=f"Уведомления {notif}", callback_data="toggle")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back")]
    ])


def vacancies_kb():
    kb = [[InlineKeyboardButton(text=t, callback_data=f"vac:{i}")] for i, t in all_vacancies()]
    kb.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def vacancy_admin_kb(v_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{v_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"del:{v_id}")
        ]
    ])


def confirm_kb(v_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{v_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="admin")
        ]
    ])


# ---------- START ----------

@dp.message(CommandStart())
async def start(m: Message):
    add_user(m.from_user.id)
    await m.answer("👋 Добро пожаловать", reply_markup=main_kb(m.from_user.id))


# ---------- NAV ----------

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.message.answer("Главное меню", reply_markup=main_kb(c.from_user.id))
    await c.answer()


@dp.callback_query(F.data == "admin")
async def admin(c: CallbackQuery):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа")
        return
    await c.message.answer("🛠 Админ-панель", reply_markup=admin_kb())
    await c.answer()


# ---------- VACANCIES ----------

@dp.callback_query(F.data == "vacancies")
async def vacancies(c: CallbackQuery):
    await c.message.answer("📋 Вакансии", reply_markup=vacancies_kb())
    await c.answer()


@dp.callback_query(F.data.startswith("vac:"))
async def show_vacancy(c: CallbackQuery):
    v_id = int(c.data.split(":")[1])
    v = get_vacancy(v_id)
    if not v:
        await c.answer("Не найдено")
        return
    text = f"<b>{v[0]}</b>\n\n{v[1]}\n\n🔗 {v[2]}"
    await c.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=vacancy_admin_kb(v_id) if c.from_user.id == ADMIN_ID else None
    )
    await c.answer()


# ---------- ADD ----------

@dp.callback_query(F.data == "add")
async def add_start(c: CallbackQuery, state: FSMContext):
    if c.from_user.id != ADMIN_ID:
        await c.answer("⛔ Нет доступа")
        return
    await state.clear()
    await state.set_state(AddVacancyFSM.title)
    await c.message.answer("✏️ Введите название вакансии:")
    await c.answer()


@dp.message(AddVacancyFSM.title)
async def add_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(AddVacancyFSM.desc)
    await m.answer("📝 Введите описание вакансии:")


@dp.message(AddVacancyFSM.desc)
async def add_desc(m: Message, s: FSMContext):
    await s.update_data(desc=m.text)
    await s.set_state(AddVacancyFSM.link)
    await m.answer("🔗 Введите ссылку:")


@dp.message(AddVacancyFSM.link)
async def add_link(m: Message, s: FSMContext):
    data = await s.get_data()
    add_vacancy(data["title"], data["desc"], m.text)
    await s.clear()
    await m.answer("✅ Вакансия добавлена", reply_markup=admin_kb())


# ---------- EDIT ----------

@dp.callback_query(F.data.startswith("edit:"))
async def edit_start(c: CallbackQuery, s: FSMContext):
    v_id = int(c.data.split(":")[1])
    v = get_vacancy(v_id)
    await s.clear()
    await s.update_data(vid=v_id)
    await s.set_state(EditVacancyFSM.title)
    await c.message.answer(f"Новое название:\n(было: {v[0]})")
    await c.answer()


@dp.message(EditVacancyFSM.title)
async def edit_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(EditVacancyFSM.desc)
    await m.answer("Новое описание:")


@dp.message(EditVacancyFSM.desc)
async def edit_desc(m: Message, s: FSMContext):
    await s.update_data(desc=m.text)
    await s.set_state(EditVacancyFSM.link)
    await m.answer("Новая ссылка:")


@dp.message(EditVacancyFSM.link)
async def edit_link(m: Message, s: FSMContext):
    d = await s.get_data()
    update_vacancy(d["vid"], d["title"], d["desc"], m.text)
    await s.clear()
    await m.answer("✏️ Вакансия обновлена", reply_markup=admin_kb())


# ---------- DELETE ----------

@dp.callback_query(F.data.startswith("del:"))
async def delete_ask(c: CallbackQuery):
    await c.message.answer(
        "Удалить вакансию?",
        reply_markup=confirm_kb(int(c.data.split(":")[1]))
    )
    await c.answer()


@dp.callback_query(F.data.startswith("confirm:"))
async def delete_confirm(c: CallbackQuery):
    delete_vacancy(int(c.data.split(":")[1]))  # ← ИСПРАВЛЕНО
    await c.message.answer("🗑 Удалено", reply_markup=admin_kb())
    await c.answer()


# ---------- STATS ----------

@dp.callback_query(F.data == "stats")
async def stats(c: CallbackQuery):
    s = user_stats()
    await c.message.answer(
        f"📊 Статистика:\n\n"
        f"Сегодня: {s['today']}\n"
        f"7 дней: {s['week']}\n"
        f"30 дней: {s['month']}\n"
        f"Всего: {s['total']}",
        reply_markup=admin_kb()
    )
    await c.answer()


# ---------- TOGGLE ----------

@dp.callback_query(F.data == "toggle")
async def toggle(c: CallbackQuery):
    toggle
