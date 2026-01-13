import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

from config import BOT_TOKEN, CHANNEL_ID
from states import VacancyForm
import keyboards as kb
from db import save_user_tags
from matcher import match_users

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# -------------------- /start --------------------
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Я помогу подобрать подходящую вакансию за 30 секунд 👇",
        reply_markup=kb.start_kb()
    )


# -------------------- START FORM --------------------
@dp.callback_query(F.data == "start_form")
async def start_form(call: CallbackQuery, state: FSMContext):
    await state.set_state(VacancyForm.format)
    await call.message.edit_text(
        "💼 Какой формат работы тебе подходит?",
        reply_markup=kb.format_kb()
    )


# -------------------- FORMAT --------------------
@dp.callback_query(F.data.startswith("format_"))
async def set_format(call: CallbackQuery, state: FSMContext):
    await state.update_data(format=call.data)
    await state.set_state(VacancyForm.experience)

    await call.message.edit_text(
        "📊 Есть ли у тебя опыт?",
        reply_markup=kb.experience_kb()
    )


# -------------------- EXPERIENCE --------------------
@dp.callback_query(F.data.startswith("exp_"))
async def set_experience(call: CallbackQuery, state: FSMContext):
    await state.update_data(experience=call.data)
    await state.set_state(VacancyForm.salary)

    await call.message.edit_text(
        "💰 Желаемый доход:",
        reply_markup=kb.salary_kb()
    )


# -------------------- SALARY + SAVE TAGS --------------------
@dp.callback_query(F.data.startswith("sal_"))
async def set_salary(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    # формируем теги пользователя
    tags = [
        data["format"].replace("format_", ""),
        data["experience"].replace("exp_", ""),
        call.data.replace("sal_", "")
    ]

    save_user_tags(call.from_user.id, tags)

    await call.message.edit_text(
        "✅ Отлично!\n\n"
        "Я буду автоматически присылать тебе подходящие вакансии 🔔\n\n"
        "Чтобы продолжить — подпишись на канал 👇",
        reply_markup=kb.subscribe_kb(
            f"https://t.me/{CHANNEL_ID.lstrip('@')}"
        )
    )


# -------------------- CHECK SUBSCRIPTION --------------------
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)

        if member.status in ("member", "administrator", "creator"):
            await call.message.edit_text(
                "🔥 Готово!\n\n"
                "Подходящие вакансии уже в канале.\n"
                "📌 Включи уведомления — лучшие варианты быстро разбирают.",
                reply_markup=kb.result_kb(
                    f"https://t.me/{CHANNEL_ID.lstrip('@')}"
                )
            )
        else:
            await call.answer(
                "❌ Подписка не найдена. Подпишись и нажми ещё раз.",
                show_alert=True
            )

    except TelegramBadRequest:
        await call.answer(
            "⚠️ Не могу проверить подписку.\n"
            "Подпишись на канал и нажми «Я подписался».",
            show_alert=True
        )


# -------------------- AUTO SEND VACANCY (UTIL) --------------------
async def send_vacancy(vacancy_text: str, vacancy_tags: list[str]):
    """
    vacancy_tags пример:
    ["офис", "без_опыта", "80_120"]
    """

    users = match_users(vacancy_tags)

    for user_id in users:
        try:
            await bot.send_message(user_id, vacancy_text)
        except:
            pass


# -------------------- MAIN --------------------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
