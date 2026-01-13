import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN, CHANNEL_ID, CHANNEL_NUMERIC_ID
from db import save_user_tags, get_all_users, can_send


# ================== INIT ==================
bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# ================== KEYBOARDS ==================
def start_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Подобрать вакансию", callback_data="start_form")]
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
            [InlineKeyboardButton(text="📢 Перейти в канал", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}")],
            [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
        ]
    )


# ================== FSM STATES ==================
class VacancyForm:
    format = "format"
    experience = "experience"
    salary = "salary"


# ================== /start ==================
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Я подберу для тебя вакансии автоматически 👇",
        reply_markup=start_kb()
    )


# ================== FORM ==================
@dp.callback_query(F.data == "start_form")
async def start_form(call: CallbackQuery, state: FSMContext):
    await state.set_state(VacancyForm.format)
    await call.message.edit_text(
        "💼 Выбери формат работы:",
        reply_markup=format_kb()
    )


@dp.callback_query(F.data.startswith("format_"))
async def set_format(call: CallbackQuery, state: FSMContext):
    await state.update_data(format=call.data.replace("format_", ""))
    await state.set_state(VacancyForm.experience)
    await call.message.edit_text(
        "📊 Есть ли опыт?",
        reply_markup=experience_kb()
    )


@dp.callback_query(F.data.startswith("exp_"))
async def set_experience(call: CallbackQuery, state: FSMContext):
    await state.update_data(experience=call.data.replace("exp_", ""))
    await state.set_state(VacancyForm.salary)
    await call.message.edit_text(
        "💰 Желаемый доход:",
        reply_markup=salary_kb()
    )


@dp.callback_query(F.data.startswith("sal_"))
async def set_salary(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    tags = [
        data["format"],
        data["experience"],
        call.data.replace("sal_", "")
    ]

    save_user_tags(call.from_user.id, tags)

    await call.message.edit_text(
        "✅ Готово!\n\n"
        "Я буду присылать тебе подходящие вакансии.\n"
        "Подпишись на канал 👇",
        reply_markup=subscribe_kb()
    )


# ================== SUB CHECK ==================
@dp.callback_query(F.data == "check_sub")
async def check_sub(call: CallbackQuery):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)

        if member.status in ("member", "administrator", "creator"):
            await call.message.edit_text(
                "🔥 Отлично!\n\n"
                "Теперь ты будешь получать вакансии автоматически."
            )
        else:
            await call.answer("❌ Подписка не найдена", show_alert=True)

    except TelegramBadRequest:
        await call.answer(
            "⚠️ Не удалось проверить подписку.\nПодпишись на канал.",
            show_alert=True
        )


# ================== CHANNEL → USERS ==================
@dp.channel_post()
async def channel_post_handler(message: Message):
    if message.chat.id != CHANNEL_NUMERIC_ID:
        return

    text = message.text or message.caption
    if not text:
        return

    text_lower = text.lower()

    users = get_all_users()

    for user_id, tags_str in users:
        tags = tags_str.split(",")

        if not all(tag in text_lower for tag in tags):
            continue

        if not can_send(user_id, limit=3):
            continue

        try:
            await bot.send_message(
                user_id,
                "🔥 Вакансия по твоим параметрам:\n\n" + text
            )
            await asyncio.sleep(1.2)
        except:
            pass


# ================== RUN ==================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
