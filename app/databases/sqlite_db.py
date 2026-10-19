import sqlite3
import os
from pathlib import Path
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class SQLiteDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("sqlite", "SQLite")
        self.db_path = config.SQLITE_PATH
        self._ensure_dir()

    def _ensure_dir(self):
        parent = Path(self.db_path).parent
        parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def connect(self) -> bool:
        try:
            self._ensure_dir()
            with self._get_connection() as conn:
                conn.execute("SELECT 1")
            self.init_schema()
            self.is_ready = True
            return True
        except Exception as e:
            self.is_ready = False
            return False

    def disconnect(self):
        pass

    def init_schema(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    profession TEXT NOT NULL,
                    department TEXT,
                    salary INTEGER,
                    created_at TEXT
                )
            """)
            conn.commit()

    def count(self) -> int:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            return cur.fetchone()[0]

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            if query:
                pattern = f"%{query}%"
                cur.execute(
                    "SELECT id, full_name, profession, department, salary, created_at FROM users "
                    "WHERE full_name LIKE ? OR profession LIKE ? "
                    "ORDER BY id ASC LIMIT ?",
                    (pattern, pattern, limit)
                )
            else:
                cur.execute(
                    "SELECT id, full_name, profession, department, salary, created_at FROM users "
                    "ORDER BY id ASC LIMIT ?",
                    (limit,)
                )
            rows = cur.fetchall()
            return [
                User(
                    id=r["id"],
                    full_name=r["full_name"],
                    profession=r["profession"],
                    department=r["department"] or "",
                    salary=r["salary"] or 0,
                    created_at=r["created_at"] or ""
                ) for r in rows
            ]

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, full_name, profession, department, salary, created_at FROM users WHERE id = ?", (user_id,))
            r = cur.fetchone()
            if not r:
                return None
            return User(
                id=r["id"],
                full_name=r["full_name"],
                profession=r["profession"],
                department=r["department"] or "",
                salary=r["salary"] or 0,
                created_at=r["created_at"] or ""
            )

    def insert(self, user: User) -> bool:
        with self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO users (id, full_name, profession, department, salary, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user.id, user.full_name, user.profession, user.department, user.salary, user.created_at)
            )
            conn.commit()
            return True

    def insert_many(self, users: List[User]) -> int:
        with self._get_connection() as conn:
            data = [(u.id, u.full_name, u.profession, u.department, u.salary, u.created_at) for u in users]
            conn.executemany(
                "INSERT OR REPLACE INTO users (id, full_name, profession, department, salary, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                data
            )
            conn.commit()
            return len(users)

    def update(self, user_id: int, data: UserUpdate) -> bool:
        with self._get_connection() as conn:
            updates = []
            params = []
            if data.full_name is not None:
                updates.append("full_name = ?")
                params.append(data.full_name)
            if data.profession is not None:
                updates.append("profession = ?")
                params.append(data.profession)
            if data.department is not None:
                updates.append("department = ?")
                params.append(data.department)
            if data.salary is not None:
                updates.append("salary = ?")
                params.append(data.salary)

            if not updates:
                return False

            params.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount > 0

    def delete(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_max_id(self) -> int:
        with self._get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT COALESCE(MAX(id), 0) FROM users")
            return cur.fetchone()[0]
