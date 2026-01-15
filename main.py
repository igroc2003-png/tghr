import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db import add_user_tag, remove_user_tags, get_user_tags

bot = Bot(BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)


class Form(StatesGroup):
    choosing_interests = State()


INTERESTS = {
    "Курьеры": "🚚 Доставка / Курьеры",
    "Магазины": "🏪 Магазины / Склады",
    "Фастфуд": "🍔 Фастфуд",
    "Коллцентр": "📞 Call-центр",
    "Клининг": "🧹 Клининг",
    "Мастер": "🏗 Мастер / Отделка",
    "Офис": "💼 Офис / Продажи",
    "Финансы": "🏦 Банк / Финансы",
    "Учитель": "👨‍🏫 Преподаватель",
    "Водитель": "🚗 Водитель / Такси",
    "Удаленка": "💻 Удалёнка",
    "Подработка": "⏱️ Подработка",
}


def interests_kb(selected: set):
    kb = []
    row = []

    for tag, title in INTERESTS.items():
        mark = "✅" if tag in selected else "❌"
        row.append(
            InlineKeyboardButton(
                text=f"{mark} {title}",
                callback_data=f"tag_{tag}"
            )
        )
        if len(row) == 2:
            kb.append(row)
            row = []

    if row:
        kb.append(row)

    kb.append([
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear"),
        InlineKeyboardButton(text="✅ Готово", callback_data="done")
    ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    tags = get_user_tags(message.from_user.id)
    await state.set_state(Form.choosing_interests)
    await state.update_data(selected=tags)

    await message.answer(
        "📂 Выбери интересы:",
        reply_markup=interests_kb(tags)
    )


@router.callback_query(F.data.startswith("tag_"))
async def toggle(cb: CallbackQuery, state: FSMContext):
    tag = cb.data.replace("tag_", "")
    data = await state.get_data()
    selected = set(data.get("selected", set()))

    if tag in selected:
        selected.remove(tag)
    else:
        selected.add(tag)

    await state.update_data(selected=selected)
    await cb.message.edit_reply_markup(reply_markup=interests_kb(selected))
    await cb.answer()


@router.callback_query(F.data == "clear")
async def clear(cb: CallbackQuery, state: FSMContext):
    remove_user_tags(cb.from_user.id)
    await state.update_data(selected=set())
    await cb.message.edit_reply_markup(reply_markup=interests_kb(set()))
    await cb.answer("Очищено")


@router.callback_query(F.data == "done")
async def done(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", set())

    remove_user_tags(cb.from_user.id)
    for tag in selected:
        add_user_tag(cb.from_user.id, tag)

    tags_text = " ".join(f"#{t}" for t in selected) if selected else "—"
    await state.clear()

    await cb.message.answer(f"✅ Интересы сохранены:\n{tags_text}")
    await cb.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())