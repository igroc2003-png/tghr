import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hr_bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # пользователи
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TEXT
        )
    """)

    # настройки
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('notifications', 'on')"
    )

    conn.commit()
    conn.close()


# ================= ПОЛЬЗОВАТЕЛИ =================

def add_user(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()

    if exists:
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO users (user_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()
    return True


def get_users_stats():
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)

    total = cursor.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    today_count = cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (today.isoformat(),)
    ).fetchone()[0]

    week_count = cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (week.isoformat(),)
    ).fetchone()[0]

    month_count = cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (month.isoformat(),)
    ).fetchone()[0]

    conn.close()
    return total, today_count, week_count, month_count


# ================= УВЕДОМЛЕНИЯ =================

def notifications_enabled() -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    value = cursor.execute(
        "SELECT value FROM settings WHERE key = 'notifications'"
    ).fetchone()[0]

    conn.close()
    return value == "on"


def toggle_notifications():
    conn = get_connection()
    cursor = conn.cursor()

    current = cursor.execute(
        "SELECT value FROM settings WHERE key = 'notifications'"
    ).fetchone()[0]

    new = "off" if current == "on" else "on"

    cursor.execute(
        "UPDATE settings SET value = ? WHERE key = 'notifications'",
        (new,)
    )

    conn.commit()
    conn.close()
