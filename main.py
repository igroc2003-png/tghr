import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, CHANNEL_ID
from states import VacancyForm
import keyboards as kb

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# /start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Привет!\n\nЯ помогу подобрать подходящую вакансию за 30 секунд 👇",
        reply_markup=kb.start_kb()
    )

# start form
@dp.callback_query(F.data == "start_form")
async def start_form(call: CallbackQuery, state: FSMContext):
    await state.set_state(VacancyForm.format)
    await call.message.edit_text(
        "💼 Какой формат работы тебе подходит?",
        reply_markup=kb.format_kb()
    )

# format
@dp.callback_query(F.data.startswith("format_"))
async def set_format(call: CallbackQuery, state: FSMContext):
    await state.update_data(format=call.data)
    await state.set_state(VacancyForm.experience)
    await call.message.edit_text(
        "📊 Есть ли у тебя опыт?",
        reply_markup=kb.experience_kb()
    )

# experience
@dp.callback_query(F.data.startswith("exp_"))
async def set_experience(call: CallbackQuery, state: FSMContext):
    await state.update_data(experience=call.data)
    await state.set_state(VacancyForm.salary)
    await call.message.edit_text(
        "💰 Желаемый доход:",
        reply_markup=kb.salary_kb()
    )

# salary
@dp.callback_query(F.data.startswith("sal_"))
async def set_salary(call: CallbackQuery, state: FSMContext):
    await state.update_data(salary=call.data)

    await call.message.edit_text(
        "✅ Отлично!\n\n"
        "Чтобы прислать вакансии — подпишись на канал 👇",
        reply_markup=kb.subscribe_kb(f"https://t.me/{CHANNEL_ID.lstrip('@')}")
    )

# check subscription
@dp.callback_query(F.data == "check_sub")
async def check_subscription(call: CallbackQuery):
    member = await bot.get_chat_member(CHANNEL_ID, call.from_user.id)

    if member.status in ["member", "administrator", "creator"]:
        await call.message.edit_text(
            "🔥 Подходящие вакансии уже в канале!\n\n"
            "📌 Совет: включи уведомления — хорошие варианты разбирают быстро.",
            reply_markup=kb.result_kb(f"https://t.me/{CHANNEL_ID.lstrip('@')}")
        )
    else:
        await call.answer("❌ Подписка не найдена", show_alert=True)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
