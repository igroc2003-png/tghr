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
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        link TEXT NOT NULL,
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

    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES ('notifications', '1')
    """)

    conn.commit()
    conn.close()


# ================== USERS ==================

def add_user(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cursor.fetchone():
        conn.close()
        return False

    cursor.execute(
        "INSERT INTO users (user_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat())
    )

    conn.commit()
    conn.close()
    return True


def get_users_stats():
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow()
    today = now.date().isoformat()
    week = (now - timedelta(days=7)).isoformat()
    month = (now - timedelta(days=30)).isoformat()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE date(joined_at) = ?",
        (today,)
    )
    today_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (week,)
    )
    week_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (month,)
    )
    month_count = cursor.fetchone()[0]

    conn.close()
    return total, today_count, week_count, month_count


# ================== SETTINGS ==================

def notifications_enabled() -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT value FROM settings WHERE key = 'notifications'"
    )
    value = cursor.fetchone()[0]

    conn.close()
    return value == "1"


def toggle_notifications():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE settings
        SET value = CASE value
            WHEN '1' THEN '0'
            ELSE '1'
        END
        WHERE key = 'notifications'
    """)

    conn.commit()
    conn.close()


# ================== VACANCIES ==================

def add_vacancy(title, description, link, image_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO vacancies (title, description, link, image_id) VALUES (?, ?, ?, ?)",
        (title, description, link, image_id)
    )

    conn.commit()
    conn.close()


def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, title FROM vacancies ORDER BY id DESC"
    )
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_vacancy_by_id(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, link, image_id FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )
    row = cursor.fetchone()

    conn.close()
    return row


def delete_vacancy(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )

    conn.commit()
    conn.close()
