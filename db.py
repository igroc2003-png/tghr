import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS user_tags (
    user_id INTEGER,
    tag TEXT,
    UNIQUE(user_id, tag)
)
""")
conn.commit()


def add_user_tag(user_id: int, tag: str):
    cur.execute(
        "INSERT OR IGNORE INTO user_tags (user_id, tag) VALUES (?, ?)",
        (user_id, tag)
    )
    conn.commit()


def remove_user_tags(user_id: int):
    cur.execute(
        "DELETE FROM user_tags WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()


def get_user_tags(user_id: int):
    cur.execute(
        "SELECT tag FROM user_tags WHERE user_id = ?",
        (user_id,)
    )
    return {row[0] for row in cur.fetchall()}