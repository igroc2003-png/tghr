from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from db import get_users
import sqlite3

app = FastAPI()

DB_PATH = "db.sqlite3"


def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vacancies")
    vacancies = cur.fetchone()[0]

    conn.close()
    return users, vacancies


@app.get("/", response_class=HTMLResponse)
def dashboard():
    users, vacancies = get_stats()

    return f"""
    <html>
    <head>
        <title>HR Admin</title>
        <style>
            body {{
                font-family: Arial;
                background: #0f172a;
                color: white;
                padding: 40px;
            }}
            .card {{
                background: #1e293b;
                padding: 20px;
                border-radius: 12px;
                margin-bottom: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>👑 HR Admin Panel</h1>

        <div class="card">👥 Пользователей: <b>{users}</b></div>
        <div class="card">📄 Вакансий: <b>{vacancies}</b></div>

        <div class="card">
            <a href="/users" style="color:#38bdf8">Пользователи</a> |
            <a href="/vacancies" style="color:#38bdf8">Вакансии</a>
        </div>
    </body>
    </html>
    """
