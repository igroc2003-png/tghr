import sqlite3

# ================== ПОДКЛЮЧЕНИЕ К БД ==================

conn = sqlite3.connect("data.db", check_same_thread=False)
cur = conn.cursor()

# ================== ТАБЛИЦА ==================

cur.execute("""
CREATE TABLE IF NOT EXISTS user_tags (
    user_id INTEGER,
    tag TEXT,
    UNIQUE(user_id, tag)
)
""")
conn.commit()

# ================== ДОБАВИТЬ ИНТЕРЕС ==================

def add_user_tag(user_id: int, tag: str):
    try:
        cur.execute(
            "INSERT OR IGNORE INTO user_tags (user_id, tag) VALUES (?, ?)",
            (user_id, tag)
        )
        conn.commit()
    except Exception as e:
        print("DB add_user_tag error:", e)

# ================== ПОЛУЧИТЬ ПОЛЬЗОВАТЕЛЕЙ ПО ТЕГУ ==================

def get_users_by_tag(tag: str):
    cur.execute(
        "SELECT DISTINCT user_id FROM user_tags WHERE tag = ?",
        (tag,)
    )
    return [row[0] for row in cur.fetchall()]

# ================== УДАЛИТЬ ВСЕ ИНТЕРЕСЫ ПОЛЬЗОВАТЕЛЯ ==================

def remove_user_tags(user_id: int):
    cur.execute(
        "DELETE FROM user_tags WHERE user_id = ?",
        (user_id,)
    )
    conn.commit()

# ================== УДАЛИТЬ ОДИН ИНТЕРЕС (ОТПИСКА) ==================

def remove_user_tag(user_id: int, tag: str):
    cur.execute(
        "DELETE FROM user_tags WHERE user_id = ? AND tag = ?",
        (user_id, tag)
    )
    conn.commit()
