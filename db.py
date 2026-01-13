import sqlite3

conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    tags TEXT
)
""")

conn.commit()

def save_user_tags(user_id: int, tags: list[str]):
    cursor.execute(
        "REPLACE INTO users (user_id, tags) VALUES (?, ?)",
        (user_id, ",".join(tags))
    )
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id, tags FROM users")
    return cursor.fetchall()
