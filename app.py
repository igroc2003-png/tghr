import os
import logging
import asyncio

from flask import Flask, request

from aiogram import Bot, Dispatcher
from aiogram.types import Update, Message
from aiogram.filters import CommandStart

# =========================
# НАСТРОЙКИ
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
HR_CHAT_ID = 5108587018  # ТВОЙ TELEGRAM ID
PORT = 3000

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # например: https://bot_xxx.bothost.run/webhook

# =========================
# ПРОВЕРКИ
# =========================

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN не задан в переменных окружения")

if not WEBHOOK_URL:
    raise RuntimeError("WEBHOOK_URL не задан в переменных окружения")

# =========================
# ИНИЦИАЛИЗАЦИЯ
# =========================

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# =========================
# HANDLERS
# =========================

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("👋 HR-бот запущен и работает!")

@dp.message()
async def echo_handler(message: Message):
    await message.answer(f"Вы написали: {message.text}")

# =========================
# WEBHOOK
# =========================

@app.route(WEBHOOK_PATH, methods=["POST"])
def telegram_webhook():
    update = Update.model_validate(request.json)
    asyncio.run(dp.feed_update(bot, update))
    return "ok"

# =========================
# STARTUP
# =========================

async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

if __name__ == "__main__":
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=PORT)
