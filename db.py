import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hr_bot.db"

def conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vacancies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        link TEXT,
        photo TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("INSERT OR IGNORE INTO settings VALUES ('notify_users', '1')")

    c.commit()
    c.close()

# USERS

def add_user(user_id):
    c = conn()
    cur = c.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO users VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    c.commit()
    c.close()

def users_count(days=None):
    c = conn()
    cur = c.cursor()

    if days:
        since = (datetime.now() - timedelta(days=days)).isoformat()
        cur.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (since,))
    else:
        cur.execute("SELECT COUNT(*) FROM users")

    res = cur.fetchone()[0]
    c.close()
    return res

def today_users():
    today = datetime.now().date().isoformat()
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM users WHERE joined_at LIKE ?", (today + "%",))
    res = cur.fetchone()[0]
    c.close()
    return res

# SETTINGS

def notify_users_enabled():
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT value FROM settings WHERE key='notify_users'")
    val = cur.fetchone()[0]
    c.close()
    return val == "1"

def toggle_notify_users():
    c = conn()
    cur = c.cursor()
    cur.execute("""
        UPDATE settings
        SET value = CASE value WHEN '1' THEN '0' ELSE '1' END
        WHERE key='notify_users'
    """)
    c.commit()
    c.close()

# VACANCIES

def add_vacancy(title, desc, link, photo):
    c = conn()
    cur = c.cursor()
    cur.execute("""
        INSERT INTO vacancies (title, description, link, photo, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (title, desc, link, photo, datetime.now().isoformat()))
    c.commit()
    c.close()

def all_vacancies():
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT id, title FROM vacancies ORDER BY id DESC")
    rows = cur.fetchall()
    c.close()
    return rows

def get_vacancy(v_id):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT title, description, link, photo FROM vacancies WHERE id=?", (v_id,))
    row = cur.fetchone()
    c.close()
    return row

def update_vacancy(v_id, title, desc, link, photo):
    c = conn()
    cur = c.cursor()
    cur.execute("""
        UPDATE vacancies
        SET title=?, description=?, link=?, photo=?
        WHERE id=?
    """, (title, desc, link, photo, v_id))
    c.commit()
    c.close()

def delete_vacancy(v_id):
    c = conn()
    cur = c.cursor()
    cur.execute("DELETE FROM vacancies WHERE id=?", (v_id,))
    c.commit()
    c.close()
