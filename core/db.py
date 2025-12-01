# core/db.py
import sqlite3
from typing import Iterable, Any
from .paths import DB_PATH

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    with get_conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS recordings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battery_name TEXT,
                battery_code TEXT,
                log_id TEXT,
                battery_no TEXT,
                operator_name TEXT,
                datetime TEXT,
                remarks TEXT,
                video_path TEXT,
                duration_ms INTEGER DEFAULT NULL,
                created_at TEXT
            )
        """)
        con.commit()

def query(sql: str, params: Iterable[Any] = ()):
    with get_conn() as con:
        return con.execute(sql, params).fetchall()

def execute(sql: str, params: Iterable[Any] = ()):
    with get_conn() as con:
        cur = con.execute(sql, params)
        con.commit()
        return cur.lastrowid
