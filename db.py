import sqlite3
from typing import List

DB_NAME = "database.db"


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_tags (
            user_id INTEGER NOT NULL,
            tag TEXT NOT NULL,
            UNIQUE(user_id, tag)
        )
    """)

    conn.commit()
    conn.close()


# ================= ТЕГИ ПОЛЬЗОВАТЕЛЯ =================

def add_user_tag(user_id: int, tag: str):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT OR IGNORE INTO user_tags (user_id, tag)
        VALUES (?, ?)
    """, (user_id, tag))

    conn.commit()
    conn.close()


def remove_user_tags(user_id: int):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM user_tags WHERE user_id = ?
    """, (user_id,))

    conn.commit()
    conn.close()


def get_user_tags(user_id: int) -> List[str]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT tag FROM user_tags WHERE user_id = ?
    """, (user_id,))

    tags = [row[0] for row in cur.fetchall()]

    conn.close()
    return tags


# ================= РАССЫЛКА =================

def get_users_by_tag(tag: str) -> List[int]:
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT user_id FROM user_tags WHERE tag = ?
    """, (tag,))

    users = [row[0] for row in cur.fetchall()]

    conn.close()
    return users