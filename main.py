import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_NUMERIC_ID, ADMIN_ID
from db import (
    save_user_tags,
    get_all_users,
    count_users,
    can_send,
    block_user
)

# ================= INIT =================
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ================= KEYBOARDS =================
def start_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔍 Подобрать вакансию",
                callback_data="start_form"
            )]
        ]
    )


def format_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Удалёнка", callback_data="format_remote"),
                InlineKeyboardButton(text="🏢 Офис", callback_data="format_office")
            ]
        ]
    )


def experience_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🆕 Без опыта", callback_data="exp_no"),
                InlineKeyboardButton(text="💼 С опытом", callback_data="exp_yes")
            ]
        ]
    )


def salary_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 до 80k", callback_data="sal_80"),
                InlineKeyboardButton(text="💰 100k+", callback_data="sal_100")
            ]
        ]
    )


def subscribe_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="📢 Перейти в канал",
                url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"
            )],
            [InlineKeyboardButton(
                text="✅ Я подписался",
                callback_data="check_sub"
            )]
        ]
    )


def admin_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📢 Рассылка всем", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="🎯 Рассылка по тегу", callback_data="admin_tag")]
        ]
    )


# ================= HELPERS =================
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ================= FSM STATES =================
FORM_FORMAT = "form_format"
FORM_EXP = "form_exp"
FORM_SALARY = "form_salary"

BROADCAST_TEXT = "broadcast_text"
TAG_NAME = "tag_name"
TAG_TEXT = "tag_text"


# ================= USER FLOW =================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет!\nЯ подберу тебе вакансии автоматически 👇",
        reply_markup=start_kb()
    )


@dp.callback_query(F.data == "start_form")
async def start_form(call: CallbackQuery, state: FSMContext):
    await state.set_state(FORM_FORMAT)
    await call.message.edit_text(
        "💼 Формат работы:",
        reply_markup=format_kb()
    )


@dp.callback_query(StateFilter(FORM_FORMAT), F.data.startswith("format_"))
async def set_format(call: CallbackQuery, state: FSMContext):
    await state.update_data(format=call.data.replace("format_", ""))
    await state.set_state(FORM_EXP)
    await call.message.edit_text(
        "📊 Есть ли опыт?",
        reply_markup=experience_kb()
    )


@dp.callback_query(StateFilter(FORM_EXP), F.data.startswith("exp_"))
async def set_experience(call: CallbackQuery, state: FSMContext):
    await state.update_data(exp=call.data.replace("exp_", ""))
    await state.set_state(FORM_SALARY)
    await call.message.edit_text(
        "💰 Желаемый доход:",
        reply_markup=salary_kb()
    )


@dp.callback_query(StateFilter(FORM_SALARY), F.data.startswith("sal_"))
async def set_salary(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tags = [data["format"], data["exp"], call.data.replace("sal_", "")]
    save_user_tags(call.from_user.id, tags)

    await state.clear()
    await call.message.edit_text(
        "✅ Готово!\nЯ буду присылать подходящие вакансии.\nПодпишись на канал 👇",
        reply_markup=subscribe_kb()
    )


# ================= ADMIN =================
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return

    await message.answer("🔥 Админ-панель", reply_markup=admin_kb())


@dp.callback_query(F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    total = count_users()
    await call.message.edit_text(
        f"📊 Пользователей: {total}",
        reply_markup=admin_kb()
    )


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state(BROADCAST_TEXT)
    await call.message.edit_text("📢 Введи текст рассылки:")


@dp.message(StateFilter(BROADCAST_TEXT), F.text)
async def send_broadcast(message: Message, state: FSMContext):
    users = get_all_users()
    sent = 0

    for user_id, _ in users:
        try:
            await bot.send_message(user_id, message.text)
            sent += 1
            await asyncio.sleep(0.5)
        except:
            block_user(user_id)

    await state.clear()
    await message.answer(f"✅ Рассылка завершена\nОтправлено: {sent}")


@dp.callback_query(F.data == "admin_tag")
async def admin_tag(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state(TAG_NAME)
    await call.message.edit_text("🎯 Введи тег:")


@dp.message(StateFilter(TAG_NAME), F.text)
async def tag_name(message: Message, state: FSMContext):
    await state.update_data(tag=message.text.lower())
    await state.set_state(TAG_TEXT)
    await message.answer("✍️ Введи текст рассылки:")


@dp.message(StateFilter(TAG_TEXT), F.text)
async def send_tag(message: Message, state: FSMContext):
    data = await state.get_data()
    tag = data["tag"]
    users = get_all_users()
    sent = 0

    for user_id, tags in users:
        if tag not in tags:
            continue
        try:
            await bot.send_message(user_id, message.text)
            sent += 1
            await asyncio.sleep(0.6)
        except:
            block_user(user_id)

    await state.clear()
    await message.answer(f"✅ Отправлено по тегу «{tag}»: {sent}")


# ================= CHANNEL → USERS =================
@dp.channel_post()
async def channel_post(message: Message):
    if message.chat.id != CHANNEL_NUMERIC_ID:
        return

    text = message.text or message.caption
    if not text:
        return

    text_lower = text.lower()

    for user_id, tags in get_all_users():
        if not all(tag in text_lower for tag in tags.split(",")):
            continue

        if not can_send(user_id):
            continue

        try:
            await bot.send_message(
                user_id,
                "🔥 Новая вакансия:\n\n" + text
            )
            await asyncio.sleep(1)
        except:
            block_user(user_id)


# ================= RUN =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
