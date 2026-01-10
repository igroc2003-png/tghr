import asyncio, os
from aiogram import Bot, Dispatcher, F
from aiogram.types import *
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from db import *

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 5108587018

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# FSM

class AddVacancyFSM(StatesGroup):
    photo = State()
    title = State()
    desc = State()
    link = State()

class EditVacancyFSM(StatesGroup):
    vid = State()
    photo = State()
    title = State()
    desc = State()
    link = State()

# KEYBOARDS

def main_kb(uid):
    kb = [[InlineKeyboardButton("📋 Вакансии", callback_data="vacancies")]]
    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 Админ", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("➕ Добавить вакансию", callback_data="add")],
        [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton("🔔 Уведомления о пользователях", callback_data="notify_users")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back")]
    ])

def vacancy_admin_kb(v_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✏️ Редактировать", callback_data=f"edit:{v_id}"),
            InlineKeyboardButton("🗑 Удалить", callback_data=f"del:{v_id}")
        ],
        [InlineKeyboardButton("⬅️ Назад", callback_data="vacancies")]
    ])

def confirm_delete_kb(v_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Да", callback_data=f"del_yes:{v_id}"),
            InlineKeyboardButton("❌ Нет", callback_data=f"vac:{v_id}")
        ]
    ])

# START

@dp.message(CommandStart())
async def start(m: Message):
    add_user(m.from_user.id)

    if m.from_user.id != ADMIN_ID and notify_users_enabled():
        await bot.send_message(ADMIN_ID, f"👤 Новый пользователь: {m.from_user.id}")

    await m.answer("Добро пожаловать", reply_markup=main_kb(m.from_user.id))

# ADMIN

@dp.callback_query(F.data == "admin")
async def admin(c: CallbackQuery):
    await c.message.answer("🛠 Админ-панель", reply_markup=admin_kb())
    await c.answer()

@dp.callback_query(F.data == "notify_users")
async def notify_users(c: CallbackQuery):
    toggle_notify_users()
    await c.message.answer(
        f"🔔 Уведомления о пользователях {'ВКЛ' if notify_users_enabled() else 'ВЫКЛ'}",
        reply_markup=admin_kb()
    )
    await c.answer()

# STATS

@dp.callback_query(F.data == "stats")
async def stats(c: CallbackQuery):
    text = (
        f"📊 Статистика\n\n"
        f"Сегодня: {today_users()}\n"
        f"7 дней: {users_count(7)}\n"
        f"30 дней: {users_count(30)}\n"
        f"Всего: {users_count()}"
    )
    await c.message.answer(text, reply_markup=admin_kb())
    await c.answer()

# VACANCIES

@dp.callback_query(F.data == "vacancies")
async def vacancies(c: CallbackQuery):
    kb = [[InlineKeyboardButton(t, callback_data=f"vac:{i}")] for i, t in all_vacancies()]
    kb.append([InlineKeyboardButton("⬅️ Назад", callback_data="back")])
    await c.message.answer("📋 Вакансии:", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))
    await c.answer()

@dp.callback_query(F.data.startswith("vac:"))
async def vacancy(c: CallbackQuery):
    v_id = int(c.data.split(":")[1])
    v = get_vacancy(v_id)
    if not v:
        await c.answer("Не найдено")
        return

    text = f"<b>{v[0]}</b>\n\n{v[1]}\n\n🔗 {v[2]}"

    if v[3]:
        await c.message.answer_photo(v[3], caption=text, parse_mode="HTML", reply_markup=vacancy_admin_kb(v_id))
    else:
        await c.message.answer(text, parse_mode="HTML", reply_markup=vacancy_admin_kb(v_id))

    await c.answer()

# ADD VACANCY

@dp.callback_query(F.data == "add")
async def add_start(c: CallbackQuery, s: FSMContext):
    await s.clear()
    await s.set_state(AddVacancyFSM.photo)
    await c.message.answer("🖼 Отправьте фото или `-`")
    await c.answer()

@dp.message(AddVacancyFSM.photo)
async def add_photo(m: Message, s: FSMContext):
    if m.text == "-":
        await s.update_data(photo=None)
    elif m.photo:
        await s.update_data(photo=m.photo[-1].file_id)
    else:
        await m.answer("Отправь фото или `-`")
        return

    await s.set_state(AddVacancyFSM.title)
    await m.answer("Название вакансии:")

@dp.message(F.text, AddVacancyFSM.title)
async def add_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(AddVacancyFSM.desc)
    await m.answer("Описание:")

@dp.message(F.text, AddVacancyFSM.desc)
async def add_desc(m: Message, s: FSMContext):
    await s.update_data(desc=m.text)
    await s.set_state(AddVacancyFSM.link)
    await m.answer("Ссылка:")

@dp.message(F.text, AddVacancyFSM.link)
async def add_link(m: Message, s: FSMContext):
    d = await s.get_data()
    add_vacancy(d["title"], d["desc"], m.text, d["photo"])
    await s.clear()
    await m.answer("✅ Вакансия добавлена", reply_markup=admin_kb())

# EDIT VACANCY

@dp.callback_query(F.data.startswith("edit:"))
async def edit_start(c: CallbackQuery, s: FSMContext):
    v_id = int(c.data.split(":")[1])
    v = get_vacancy(v_id)
    if not v:
        await c.answer("Не найдено")
        return

    await s.clear()
    await s.update_data(vid=v_id, photo=v[3])
    await s.set_state(EditVacancyFSM.photo)
    await c.message.answer("🖼 Новое фото или `-` (оставить текущее)")
    await c.answer()

@dp.message(EditVacancyFSM.photo)
async def edit_photo(m: Message, s: FSMContext):
    if m.text == "-":
        pass
    elif m.photo:
        await s.update_data(photo=m.photo[-1].file_id)
    else:
        await m.answer("Отправь фото или `-`")
        return

    await s.set_state(EditVacancyFSM.title)
    await m.answer("Новое название:")

@dp.message(F.text, EditVacancyFSM.title)
async def edit_title(m: Message, s: FSMContext):
    await s.update_data(title=m.text)
    await s.set_state(EditVacancyFSM.desc)
    await m.answer("Новое описание:")

@dp.message(F.text, EditVacancyFSM.desc)
async def edit_desc(m: Message, s: FSMContext):
    await s.update_data(desc=m.text)
    await s.set_state(EditVacancyFSM.link)
    await m.answer("Новая ссылка:")

@dp.message(F.text, EditVacancyFSM.link)
async def edit_link(m: Message, s: FSMContext):
    d = await s.get_data()
    update_vacancy(d["vid"], d["title"], d["desc"], m.text, d["photo"])
    await s.clear()
    await m.answer("✏️ Вакансия обновлена", reply_markup=admin_kb())

# DELETE

@dp.callback_query(F.data.startswith("del:"))
async def del_confirm(c: CallbackQuery):
    v_id = int(c.data.split(":")[1])
    await c.message.answer("Точно удалить?", reply_markup=confirm_delete_kb(v_id))
    await c.answer()

@dp.callback_query(F.data.startswith("del_yes:"))
async def del_yes(c: CallbackQuery):
    delete_vacancy(int(c.data.split(":")[1]))
    await c.message.answer("🗑 Удалено", reply_markup=admin_kb())
    await c.answer()

# BACK

@dp.callback_query(F.data == "back")
async def back(c: CallbackQuery):
    await c.message.answer("Главное меню", reply_markup=main_kb(c.from_user.id))
    await c.answer()

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
