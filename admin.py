from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import sqlite3

DB_PATH = "db.sqlite3"

app = FastAPI()


def db():
    return sqlite3.connect(DB_PATH)


@app.get("/", response_class=HTMLResponse)
def dashboard():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM vacancies")
    vacancies = cur.fetchone()[0]

    conn.close()

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
            a {{ color:#38bdf8; text-decoration:none; }}
        </style>
    </head>
    <body>
        <h1>👑 HR Admin Panel</h1>

        <div class="card">👥 Пользователей: <b>{users}</b></div>
        <div class="card">📄 Вакансий: <b>{vacancies}</b></div>

        <div class="card">
            <a href="/users">👥 Пользователи</a><br><br>
            <a href="/vacancies">📄 Вакансии</a>
        </div>
    </body>
    </html>
    """


@app.get("/users", response_class=HTMLResponse)
def users():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT user_id, interest, active FROM users")
    rows = cur.fetchall()
    conn.close()

    table = ""
    for uid, interest, active in rows:
        table += f"""
        <tr>
            <td>{uid}</td>
            <td>{interest}</td>
            <td>{'✅' if active else '❌'}</td>
        </tr>
        """

    return f"""
    <h2>👥 Пользователи</h2>
    <table border="1" cellpadding="8">
        <tr><th>ID</th><th>Интерес</th><th>Активен</th></tr>
        {table}
    </table>
    <br><a href="/">← Назад</a>
    """


@app.get("/vacancies", response_class=HTMLResponse)
def vacancies():
    conn = db()
    cur = conn.cursor()
    cur.execute("SELECT id, text, tags FROM vacancies ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()

    blocks = ""
    for vid, text, tags in data:
        blocks += f"""
        <div style="border:1px solid #ccc;padding:10px;margin:10px">
            <b>ID:</b> {vid}<br><br>
            <pre>{text}</pre>
            <small>{tags}</small>
        </div>
        """

    return f"""
    <h2>📄 Вакансии</h2>
    {blocks}
    <br><a href="/">← Назад</a>
    """
