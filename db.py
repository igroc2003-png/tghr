import sqlite3
from datetime import datetime, timedelta

DB_NAME = "hr_bot.db"


def conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    c = conn()
    cur = c.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        joined_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS vacancies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT,
        link TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cur.execute("""
    INSERT OR IGNORE INTO settings VALUES ('notifications', '1')
    """)

    c.commit()
    c.close()


# ---------- USERS ----------

def add_user(user_id: int) -> bool:
    c = conn()
    cur = c.cursor()

    cur.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
    if cur.fetchone():
        c.close()
        return False

    cur.execute(
        "INSERT INTO users VALUES (?, ?)",
        (user_id, datetime.now().isoformat())
    )
    c.commit()
    c.close()
    return True


def user_stats():
    c = conn()
    cur = c.cursor()

    now = datetime.now()
    today = now.replace(hour=0, minute=0, second=0)
    week = now - timedelta(days=7)
    month = now - timedelta(days=30)

    def count(date=None):
        if date:
            cur.execute("SELECT COUNT(*) FROM users WHERE joined_at >= ?", (date.isoformat(),))
        else:
            cur.execute("SELECT COUNT(*) FROM users")
        return cur.fetchone()[0]

    stats = {
        "today": count(today),
        "week": count(week),
        "month": count(month),
        "total": count()
    }

    c.close()
    return stats


# ---------- SETTINGS ----------

def notifications_enabled():
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT value FROM settings WHERE key='notifications'")
    val = cur.fetchone()[0]
    c.close()
    return val == "1"


def toggle_notifications():
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT value FROM settings WHERE key='notifications'")
    current = cur.fetchone()[0]
    new = "0" if current == "1" else "1"
    cur.execute("UPDATE settings SET value=? WHERE key='notifications'", (new,))
    c.commit()
    c.close()


# ---------- VACANCIES ----------

def add_vacancy(title, desc, link):
    c = conn()
    cur = c.cursor()
    cur.execute(
        "INSERT INTO vacancies (title, description, link) VALUES (?, ?, ?)",
        (title, desc, link)
    )
    c.commit()
    c.close()


def update_vacancy(v_id, title, desc, link):
    c = conn()
    cur = c.cursor()
    cur.execute("""
    UPDATE vacancies
    SET title=?, description=?, link=?
    WHERE id=?
    """, (title, desc, link, v_id))
    c.commit()
    c.close()


def delete_vacancy(v_id):
    c = conn()
    cur = c.cursor()
    cur.execute("DELETE FROM vacancies WHERE id=?", (v_id,))
    c.commit()
    c.close()


def all_vacancies():
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT id, title FROM vacancies ORDER BY id DESC")
    res = cur.fetchall()
    c.close()
    return res


def get_vacancy(v_id):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT title, description, link FROM vacancies WHERE id=?", (v_id,))
    row = cur.fetchone()
    c.close()
    return row
