import sqlite3

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

# ================== ТАБЛИЦА ==================

cur.execute("""
CREATE TABLE IF NOT EXISTS user_tags (
    user_id INTEGER,
    tag TEXT
)
""")
conn.commit()

# ================== ФУНКЦИИ ==================

def add_user_tag(user_id: int, tag: str):
    cur.execute(
        "INSERT INTO user_tags (user_id, tag) VALUES (?, ?)",
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
    return [row[0] for row in cur.fetchall()]


def get_users_by_tag(tag: str):
    cur.execute(
        "SELECT DISTINCT user_id FROM user_tags WHERE tag = ?",
        (tag,)
    )
    return [row[0] for row in cur.fetchall()]
