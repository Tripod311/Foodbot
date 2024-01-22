import sqlite3
import json


def setup():
    conn = sqlite3.connect("users.sql")
    conn.execute("CREATE TABLE IF NOT EXISTS users (chat_id BIGINT PRIMARY_KEY, last_list TEXT, exclusions TEXT)")
    conn.commit()
    conn.close()


def get_exclusions(chat_id):
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT exclusions FROM users WHERE chat_id=?", [chat_id])
    row = cur.fetchone()
    if row is None:
        return []
    else:
        try:
            ex = json.loads(row[0])
            return ex
        except Exception as e:
            return []


def set_exclusions(chat_id, ex):
    str_data = json.dumps(ex)
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id=?", [chat_id])
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.execute("UPDATE users SET exclusions=? WHERE chat_id=?", [str_data, chat_id])
    else:
        cur.close()
        conn.execute("INSERT INTO users (chat_id, exclusions) VALUES (?, ?)", [chat_id, str_data])
    conn.commit()
    conn.close()


def get_list(chat_id):
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT last_list FROM users WHERE chat_id=?", [chat_id])
    row = cur.fetchone()
    if row is None:
        return None
    else:
        try:
            ex = json.loads(row[0])
            return ex
        except Exception as e:
            return None


def set_list(chat_id, ll):
    str_data = json.dumps(ll)
    conn = sqlite3.connect("users.sql")
    cur = conn.execute("SELECT COUNT(*) FROM users WHERE chat_id=?", [chat_id])
    if cur.fetchone()[0] > 0:
        cur.close()
        conn.execute("UPDATE users SET last_list=? WHERE chat_id=?", [str_data, chat_id])
    else:
        cur.close()
        conn.execute("INSERT INTO users (chat_id, last_list) VALUES (?, ?)", [chat_id, str_data])
    conn.commit()
    conn.close()
