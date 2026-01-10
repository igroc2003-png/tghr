import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hr_bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            link TEXT,
            image_id TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            joined_at TEXT
        )
    """)

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


# ================= ВАКАНСИИ =================

def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute(
        "SELECT id, title FROM vacancies ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return rows


def get_vacancy(vacancy_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute(
        "SELECT title, description, link, image_id FROM vacancies WHERE id = ?",
        (vacancy_id,)
    ).fetchone()
    conn.close()
    return row


def add_vacancy(title, description, link, image_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vacancies (title, description, link, image_id) VALUES (?, ?, ?, ?)",
        (title, description, link, image_id)
    )
    conn.commit()
    conn.close()


def update_vacancy(vacancy_id, title, description, link, image_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE vacancies
        SET title = ?, description = ?, link = ?, image_id = ?
        WHERE id = ?
    """, (title, description, link, image_id, vacancy_id))
    conn.commit()
    conn.close()


def delete_vacancy(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )
    conn.commit()
    conn.close()


# ================= ПОЛЬЗОВАТЕЛИ =================

def add_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_users_stats():
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)

    total = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
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

def notifications_enabled():
    conn = get_connection()
    cursor = conn.cursor()
    val = cursor.execute(
        "SELECT value FROM settings WHERE key='notifications'"
    ).fetchone()[0]
    conn.close()
    return val == "on"


def toggle_notifications():
    conn = get_connection()
    cursor = conn.cursor()
    cur = cursor.execute(
        "SELECT value FROM settings WHERE key='notifications'"
    ).fetchone()[0]
    new = "off" if cur == "on" else "on"
    cursor.execute(
        "UPDATE settings SET value=? WHERE key='notifications'",
        (new,)
    )
    conn.commit()
    conn.close()
