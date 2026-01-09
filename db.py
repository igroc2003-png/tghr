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
            image_id TEXT,
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


def add_vacancy(title, description, link, image_id=None):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO vacancies (title, description, link, image_id) VALUES (?, ?, ?, ?)",
        (title, description, link, image_id)
    )

    conn.commit()
    conn.close()


def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title FROM vacancies ORDER BY created_at DESC")
    data = cursor.fetchall()

    conn.close()
    return data


def get_vacancy_by_id(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, link, image_id FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )
    data = cursor.fetchone()

    conn.close()
    return data


def save_response(vacancy_id, user_id, username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO responses (vacancy_id, user_id, username) VALUES (?, ?, ?)",
        (vacancy_id, user_id, username)
    )

    conn.commit()
    conn.close()
