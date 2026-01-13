from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def start_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Начать подбор", callback_data="start_form")]
    ])

def format_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏢 Офис", callback_data="format_office")],
        [InlineKeyboardButton(text="🏬 Магазин", callback_data="format_shop")],
        [InlineKeyboardButton(text="🏠 Удалёнка", callback_data="format_remote")],
        [InlineKeyboardButton(text="⏱ Подработка", callback_data="format_part")],
        [InlineKeyboardButton(text="🔥 Всё подходит", callback_data="format_any")]
    ])

def experience_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👶 Без опыта", callback_data="exp_no")],
        [InlineKeyboardButton(text="💼 Есть опыт", callback_data="exp_yes")],
        [InlineKeyboardButton(text="🎓 Неважно", callback_data="exp_any")]
    ])

def salary_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="до 50 000 ₽", callback_data="sal_50")],
        [InlineKeyboardButton(text="50–80 000 ₽", callback_data="sal_80")],
        [InlineKeyboardButton(text="80–120 000 ₽", callback_data="sal_120")],
        [InlineKeyboardButton(text="120 000 ₽+", callback_data="sal_120plus")]
    ])

def subscribe_kb(channel_url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Подписаться", url=channel_url)],
        [InlineKeyboardButton(text="✅ Я подписался", callback_data="check_sub")]
    ])

def result_kb(channel_url):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👉 Смотреть вакансии", url=channel_url)],
        [InlineKeyboardButton(text="🔔 Включить уведомления", url=channel_url)]
    ])
