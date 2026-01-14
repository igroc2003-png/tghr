import asyncio
import re
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ChatMemberStatus

from config import BOT_TOKEN, CHANNEL_USERNAME, ADMIN_ID
from db import add_user_tag, get_users_by_tag, remove_user_tags

bot = Bot(BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ================== СОСТОЯНИЕ ==================

state = {
    "mode": None,
    "text": None,
    "photo": None,
    "tags": set(),
    "user_tags": set()
}

def reset_state(keep_user_tags=True):
    user_tags = state["user_tags"] if keep_user_tags else set()
    state.clear()
    state.update({
        "mode": None,
        "text": None,
        "photo": None,
        "tags": set(),
        "user_tags": user_tags
    })

# ================== АВТО-ТЕГИ ==================

AUTO_TAGS = {
    "Продажи": ["продав", "продаж"],
    "БезОпыта": ["без опыта", "обуч"],
    "Подработка": ["смен", "подработ"],
    "Удаленка": ["удален", "онлайн"],
    "Курьер": ["курьер", "достав"],
    "Офис": ["офис"],

    # 🔥 НОВЫЕ
    "Магазин": ["магазин", "продавец", "касс", "торгов", "ритейл", "супермаркет"],
    "Мастер": ["мастер", "монтаж", "установ", "сборк", "ремонт", "электрик", "сантехник", "техник"],
}

def extract_auto_tags(text: str):
    text = text.lower()
    tags = set()
    for tag, keys in AUTO_TAGS.items():
        if any(k in text for k in keys):
            tags.add(tag)
    return tags

# ================== ФОРМАТ ВАКАНСИИ ==================

def format_job(raw: str):
    raw_l = raw.lower()
    title = raw.split("\n")[0].strip().title()

    salary = re.search(r"\d{3,6}", raw)
    salary_text = f"{salary.group()} ₽" if salary else "по договорённости"

    schedule = re.search(r"\d+/\d+", raw)
    schedule_text = schedule.group() if schedule else "обсуждается"

    link = re.search(r"https?://\S+", raw)
    link_text = link.group() if link else "написать в личные сообщения"

    experience = "не требуется (обучение)" if "без опыта" in raw_l else "желателен"

    auto_tags = extract_auto_tags(raw)
    manual_tags = {w[1:] for w in raw.split() if w.startswith("#")}
    tags = auto_tags | manual_tags

    text = (
        f"🔥 {title.upper()}\n\n"
        f"👷 Должность:\n— {title}\n\n"
        f"💰 Доход:\n— {salary_text}\n\n"
        f"⏱ График:\n— {schedule_text}\n\n"
        f"🎓 Опыт:\n— {experience}\n\n"
        f"✍️ Отклик:\n👉 {link_text}\n"
    )

    if tags:
        text += "\n" + " ".join(f"#{t}" for t in sorted(tags))

    return text, tags

# ================== КЛАВИАТУРЫ ==================

def admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить вакансию", callback_data="add_job")],
        [InlineKeyboardButton(text="📝 Опубликовать пост", callback_data="add_post")],
        [InlineKeyboardButton(text="📂 Выбрать интересы", callback_data="user_menu")]
    ])

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
        ]
    ])

def interests_kb():
    def btn(tag):
        mark = "✅" if tag in state["user_tags"] else "❌"
        return InlineKeyboardButton(text=f"{mark} {tag}", callback_data=f"tag_{tag}")

    return InlineKeyboardMarkup(inline_keyboard=[
        [btn("Курьер"), btn("Удаленка")],
        [btn("Продажи"), btn("Офис")],
        [btn("Магазин"), btn("Мастер")],
        [
            InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_interests"),
            InlineKeyboardButton(text="✅ Готово", callback_data="save_interests")
        ]
    ])

# ================== ПОДПИСКА ==================

async def is_subscribed(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        )
    except:
        return False

# ================== START ==================

@router.message(CommandStart())
async def start(message: Message):
    if not await is_subscribed(message.from_user.id):
        await message.answer(
            "🔒 Подпишись на канал:\n"
            f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
        )
        return

    if message.from_user.id == ADMIN_ID:
        await message.answer("👑 Админ-панель", reply_markup=admin_kb())
    else:
        await message.answer("📂 Выбери интересы:", reply_markup=interests_kb())

# ================== ИНТЕРЕСЫ ==================

@router.callback_query(F.data == "user_menu")
async def user_menu(cb: CallbackQuery):
    await cb.message.answer("📂 Выбери интересы:", reply_markup=interests_kb())
    await cb.answer()

@router.callback_query(F.data.startswith("tag_"))
async def toggle_tag(cb: CallbackQuery):
    tag = cb.data.replace("tag_", "")
    if tag in state["user_tags"]:
        state["user_tags"].remove(tag)
    else:
        state["user_tags"].add(tag)

    await cb.message.edit_reply_markup(reply_markup=interests_kb())
    await cb.answer()

@router.callback_query(F.data == "save_interests")
async def save_interests(cb: CallbackQuery):
    if not state["user_tags"]:
        await cb.answer("❗ Ничего не выбрано", show_alert=True)
        return

    for tag in state["user_tags"]:
        add_user_tag(cb.from_user.id, tag)

    tags_text = " ".join(f"#{t}" for t in state["user_tags"])
    state["user_tags"].clear()

    await cb.message.answer(f"✅ Интересы сохранены:\n{tags_text}", reply_markup=admin_kb())
    await cb.answer()

@router.callback_query(F.data == "clear_interests")
async def clear_interests(cb: CallbackQuery):
    remove_user_tags(cb.from_user.id)
    state["user_tags"].clear()
    await cb.message.answer("🗑 Интересы очищены")
    await cb.answer()

# ================== ДОБАВЛЕНИЕ ==================

@router.callback_query(F.data == "add_job")
async def add_job(cb: CallbackQuery):
    reset_state()
    state["mode"] = "job"
    await cb.message.answer("✏️ Напиши вакансию простым текстом")
    await cb.answer()

@router.callback_query(F.data == "add_post")
async def add_post(cb: CallbackQuery):
    reset_state()
    state["mode"] = "post"
    await cb.message.answer("📝 Отправь пост")
    await cb.answer()

# ================== ПРИЁМ ==================

@router.message(F.from_user.id == ADMIN_ID)
async def receive(message: Message):
    if not state.get("mode"):
        return

    raw = message.text or message.caption
    if not raw:
        await message.answer("❌ Нужно добавить текст")
        return

    photo = message.photo[-1].file_id if message.photo else None

    if state["mode"] == "job":
        text, tags = format_job(raw)
    else:
        text = raw
        tags = extract_auto_tags(raw)

    state["text"] = text
    state["photo"] = photo
    state["tags"] = tags

    if photo:
        await message.answer_photo(photo, caption=text, reply_markup=confirm_kb())
    else:
        await message.answer(text, reply_markup=confirm_kb())

# ================== ПУБЛИКАЦИЯ ==================

@router.callback_query(F.data == "publish")
async def publish(cb: CallbackQuery):
    text = state["text"]
    photo = state["photo"]
    tags = state["tags"]

    if photo:
        await bot.send_photo(CHANNEL_USERNAME, photo, caption=text)
    else:
        await bot.send_message(CHANNEL_USERNAME, text)

    sent = 0
    for tag in tags:
        for uid in get_users_by_tag(tag):
            try:
                if photo:
                    await bot.send_photo(uid, photo, caption=text)
                else:
                    await bot.send_message(uid, text)
                sent += 1
            except:
                pass

    reset_state()
    await cb.message.answer(f"✅ Опубликовано\n📩 Рассылка: {sent}", reply_markup=admin_kb())
    await cb.answer()

@router.callback_query(F.data == "cancel")
async def cancel(cb: CallbackQuery):
    reset_state()
    await cb.message.answer("❌ Отменено", reply_markup=admin_kb())
    await cb.answer()

# ================== ЗАПУСК ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())