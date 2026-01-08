import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
import openai

from config import BOT_TOKEN, OPENAI_API_KEY
from hr_prompt import SYSTEM_PROMPT

openai.api_key = OPENAI_API_KEY

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

sessions = {}  # user_id → context


def vacancy_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Менеджер по продажам", callback_data="sales")],
        [InlineKeyboardButton(text="Маркетолог", callback_data="marketing")],
        [InlineKeyboardButton(text="Оператор", callback_data="operator")]
    ])


async def ask_gpt(user_id, text):
    session = sessions[user_id]

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *session["dialog"],
        {"role": "user", "content": text}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.2
    )

    answer = response.choices[0].message.content
    session["dialog"].append({"role": "assistant", "content": answer})
    return answer


@dp.message(CommandStart())
async def start(message: Message):
    sessions[message.from_user.id] = {
        "vacancy": None,
        "dialog": []
    }

    await message.answer(
        "Здравствуйте! На какую вакансию вы откликаетесь?",
        reply_markup=vacancy_keyboard()
    )


@dp.callback_query()
async def select_vacancy(callback):
    user_id = callback.from_user.id
    vacancy_map = {
        "sales": "Менеджер по продажам",
        "marketing": "Маркетолог",
        "operator": "Оператор колл-центра"
    }

    vacancy = vacancy_map.get(callback.data)
    sessions[user_id]["vacancy"] = vacancy
    sessions[user_id]["dialog"].append({
        "role": "user",
        "content": f"Я откликаюсь на вакансию {vacancy}"
    })

    await callback.message.answer("Как вас зовут?")


@dp.message(F.text)
async def dialog(message: Message):
    user_id = message.from_user.id

    if user_id not in sessions:
        return

    sessions[user_id]["dialog"].append({
        "role": "user",
        "content": message.text
    })

    answer = await ask_gpt(user_id, message.text)

    await message.answer(answer)

    if "КАНДИДАТ:" in answer:
        del sessions[user_id]


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
