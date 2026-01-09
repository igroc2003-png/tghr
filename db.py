import sqlite3

DB_NAME = "hr_bot.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER,
            user_id INTEGER,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def add_vacancy(title, description, link):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO vacancies (title, description, link) VALUES (?, ?, ?)",
        (title, description, link)
    )

    conn.commit()
    conn.close()


def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title FROM vacancies ORDER BY created_at DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_vacancy_by_id(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, link FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return row


def add_response(vacancy_id, user_id, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO responses (vacancy_id, user_id, username) VALUES (?, ?, ?)",
        (vacancy_id, user_id, username)
    )

    conn.commit()
    conn.close()

def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title FROM vacancies")
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_vacancy_by_id(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, link FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return row
