
import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    tag TEXT,
    UNIQUE(user_id, tag)
)
""")
conn.commit()

def add_user_tag(user_id: int, tag: str):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, tag) VALUES (?, ?)",
        (user_id, tag)
    )
    conn.commit()

def get_users_by_tag(tag: str):
    cursor.execute(
        "SELECT user_id FROM users WHERE tag = ?",
        (tag,)
    )
    return [row[0] for row in cursor.fetchall()]
