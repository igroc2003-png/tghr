import os
import requests
from flask import Flask, request

BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВАШ_BOT_TOKEN"
BOT_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")

        if text == "/start":
            send_message(chat_id, "Привет! Я простой Telegram-бот 🤖")
        else:
            send_message(chat_id, f"Ты написал: {text}")

    return "ok"

def send_message(chat_id, text):
    url = f"{BOT_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)
