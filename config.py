import os

# 🔐 Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 📢 Канал
CHANNEL_ID = "@HR_JOB_s"
CHANNEL_NUMERIC_ID = -1001652876751  # numeric ID канала

# 👑 Администратор
ADMIN_ID = 5108587018  # твой Telegram user_id

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения")
