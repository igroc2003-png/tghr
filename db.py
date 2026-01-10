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
            image_id TEXT
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

    cursor.execute("SELECT id, title FROM vacancies ORDER BY id DESC")
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_vacancy_by_id(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT title, description, link, image_id FROM vacancies WHERE id = ?",
        (vacancy_id,)
    )
    row = cursor.fetchone()

    conn.close()
    return row


def update_vacancy(vacancy_id, title, description, link, image_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE vacancies
        SET title = ?, description = ?, link = ?, image_id = ?
        WHERE id = ?
    """, (title, description, link, image_id, vacancy_id))

    conn.commit()
    conn.close()


def delete_vacancy(vacancy_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM vacancies WHERE id = ?", (vacancy_id,))
    conn.commit()
    conn.close()
