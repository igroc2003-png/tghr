import sqlite3
from datetime import datetime, date, timedelta

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
            joined_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ================== USERS ==================

def add_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, joined_at) VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )

    conn.commit()
    conn.close()


def get_users_stats_extended():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    today = date.today().isoformat()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?",
        (f"{today}%",)
    )
    today_count = cursor.fetchone()[0]

    week_date = (date.today() - timedelta(days=7)).isoformat()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (week_date,)
    )
    week_count = cursor.fetchone()[0]

    month_date = (date.today() - timedelta(days=30)).isoformat()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at >= ?",
        (month_date,)
    )
    month_count = cursor.fetchone()[0]

    conn.close()
    return total, today_count, week_count, month_count


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

    cursor.execute("SELECT id, title FROM vacancies ORDER BY id DESC")
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

    cursor.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
    conn.commit()
    conn.close()
