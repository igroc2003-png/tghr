import sqlite3

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    interest TEXT,
    active INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS vacancies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT,
    tags TEXT
)
""")

conn.commit()

def save_user(user_id: int, interest: str):
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, interest, active) VALUES (?, ?, 1)",
        (user_id, interest)
    )
    conn.commit()

def get_users():
    cursor.execute("SELECT user_id, interest FROM users WHERE active=1")
    return cursor.fetchall()

def save_vacancy(text: str, tags: str):
    cursor.execute(
        "INSERT INTO vacancies (text, tags) VALUES (?, ?)",
        (text, tags)
    )
    conn.commit()

def count_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def count_vacancies():
    cursor.execute("SELECT COUNT(*) FROM vacancies")
    return cursor.fetchone()[0]
