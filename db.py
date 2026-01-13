import sqlite3
from datetime import date

DB_NAME = "bot.db"

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# ---------- TABLES ----------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    tags TEXT,
    is_blocked INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS sent_log (
    user_id INTEGER,
    send_date TEXT,
    count INTEGER,
    PRIMARY KEY (user_id, send_date)
)
""")

conn.commit()


# ---------- USERS ----------
def save_user_tags(user_id: int, tags: list[str]):
    cursor.execute(
        "REPLACE INTO users (user_id, tags) VALUES (?, ?)",
        (user_id, ",".join(tags))
    )
    conn.commit()


def get_all_users():
    cursor.execute(
        "SELECT user_id, tags FROM users WHERE is_blocked = 0"
    )
    return cursor.fetchall()


def count_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


def block_user(user_id: int):
    cursor.execute(
        "UPDATE users SET is_blocked = 1 WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()


# ---------- ANTISPAM ----------
def can_send(user_id: int, limit: int = 3) -> bool:
    today = date.today().isoformat()

    cursor.execute(
        "SELECT count FROM sent_log WHERE user_id=? AND send_date=?",
        (user_id, today)
    )
    row = cursor.fetchone()

    if row is None:
        cursor.execute(
            "INSERT INTO sent_log (user_id, send_date, count) VALUES (?, ?, 1)",
            (user_id, today)
        )
        conn.commit()
        return True

    if row[0] >= limit:
        return False

    cursor.execute(
        "UPDATE sent_log SET count = count + 1 WHERE user_id=? AND send_date=?",
        (user_id, today)
    )
    conn.commit()
    return True
