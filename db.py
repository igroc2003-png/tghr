import sqlite3

DB = "bot.db"

def init_db():
    with sqlite3.connect(DB) as c:
        c.execute("CREATE TABLE IF NOT EXISTS interests (user_id INTEGER, tag TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS stats (user_id INTEGER, delivered INTEGER DEFAULT 0)")

def get_users_by_interests(tags):
    if not tags:
        return []
    q = "SELECT DISTINCT user_id FROM interests WHERE tag IN ({})".format(",".join("?"*len(tags)))
    with sqlite3.connect(DB) as c:
        return [r[0] for r in c.execute(q, tags)]

def get_all_users():
    with sqlite3.connect(DB) as c:
        return [r[0] for r in c.execute("SELECT DISTINCT user_id FROM interests")]

def save_stat_delivery(uid):
    with sqlite3.connect(DB) as c:
        c.execute("INSERT OR IGNORE INTO stats (user_id) VALUES (?)", (uid,))
        c.execute("UPDATE stats SET delivered = delivered + 1 WHERE user_id=?", (uid,))
