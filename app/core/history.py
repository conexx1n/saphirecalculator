import os
import sqlite3
import time

from app.core.paths import data_dir


class HistoryService:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = str(data_dir() / "history.db")
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                calc_type TEXT,
                input TEXT,
                result TEXT,
                created_at REAL
            )
        """)
        self.conn.commit()

    def add(self, calc_type, input_str, result):
        self.conn.execute(
            "INSERT INTO history(calc_type,input,result,created_at) VALUES(?,?,?,?)",
            (calc_type, input_str, result, time.time()),
        )
        self.conn.commit()

    def all(self, query="", calc_type=""):
        sql = "SELECT id,calc_type,input,result,created_at FROM history WHERE 1=1"
        params = []
        if query:
            sql += " AND (input LIKE ? OR result LIKE ?)"
            params += [f"%{query}%", f"%{query}%"]
        if calc_type:
            sql += " AND calc_type=?"
            params.append(calc_type)
        sql += " ORDER BY created_at DESC"
        return self.conn.execute(sql, params).fetchall()

    def clear(self):
        self.conn.execute("DELETE FROM history")
        self.conn.commit()

    def delete(self, eid):
        self.conn.execute("DELETE FROM history WHERE id=?", (eid,))
        self.conn.commit()
