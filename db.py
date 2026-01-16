import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_tags (
    user_id INTEGER,
    tag TEXT
)
""")
conn.commit()

def add_user_tag(user_id: int, tag: str):
    cursor.execute(
        "INSERT INTO user_tags (user_id, tag) VALUES (?, ?)",
        (user_id, tag)
    )
    conn.commit()

def remove_user_tags(user_id: int):
    cursor.execute(
        "DELETE FROM user_tags WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()

def get_user_tags(user_id: int):
    cursor.execute(
        "SELECT tag FROM user_tags WHERE user_id = ?",
        (user_id,)
    )
    return [row[0] for row in cursor.fetchall()]

def get_users_by_tag(tag: str):
    cursor.execute(
        "SELECT DISTINCT user_id FROM user_tags WHERE tag = ?",
        (tag,)
    )
    return [row[0] for row in cursor.fetchall()]

def get_all_users():
    cursor.execute(
        "SELECT DISTINCT user_id FROM user_tags"
    )
    return {row[0] for row in cursor.fetchall()}