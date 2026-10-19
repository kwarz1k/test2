import pymysql
from pymysql.cursors import DictCursor
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class MySQLDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("mysql", "MySQL")

    def _get_connection(self):
        return pymysql.connect(
            host=config.MYSQL_HOST,
            port=config.MYSQL_PORT,
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            database=config.MYSQL_DB,
            charset="utf8mb4",
            cursorclass=DictCursor,
            connect_timeout=3,
            autocommit=False
        )

    def connect(self) -> bool:
        try:
            conn = self._get_connection()
            conn.close()
            self.init_schema()
            self.is_ready = True
            return True
        except Exception:
            self.is_ready = False
            return False

    def disconnect(self):
        pass

    def init_schema(self):
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY,
                        full_name VARCHAR(255) NOT NULL,
                        profession VARCHAR(255) NOT NULL,
                        department VARCHAR(100),
                        salary INT,
                        created_at VARCHAR(50)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
            conn.commit()
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS cnt FROM users;")
                row = cur.fetchone()
                return row["cnt"] if row else 0
        finally:
            conn.close()

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                if query:
                    pattern = f"%{query}%"
                    cur.execute(
                        "SELECT id, full_name, profession, department, salary, created_at FROM users "
                        "WHERE full_name LIKE %s OR profession LIKE %s "
                        "ORDER BY id ASC LIMIT %s;",
                        (pattern, pattern, limit)
                    )
                else:
                    cur.execute(
                        "SELECT id, full_name, profession, department, salary, created_at FROM users "
                        "ORDER BY id ASC LIMIT %s;",
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
        finally:
            conn.close()

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, full_name, profession, department, salary, created_at FROM users WHERE id = %s;", (user_id,))
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
        finally:
            conn.close()

    def insert(self, user: User) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (id, full_name, profession, department, salary, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        profession = VALUES(profession),
                        department = VALUES(department),
                        salary = VALUES(salary),
                        created_at = VALUES(created_at);
                    """,
                    (user.id, user.full_name, user.profession, user.department, user.salary, user.created_at)
                )
            conn.commit()
            return True
        finally:
            conn.close()

    def insert_many(self, users: List[User]) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                data = [(u.id, u.full_name, u.profession, u.department, u.salary, u.created_at) for u in users]
                cur.executemany(
                    """
                    INSERT INTO users (id, full_name, profession, department, salary, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        profession = VALUES(profession),
                        department = VALUES(department),
                        salary = VALUES(salary),
                        created_at = VALUES(created_at);
                    """,
                    data
                )
            conn.commit()
            return len(users)
        finally:
            conn.close()

    def update(self, user_id: int, data: UserUpdate) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                updates = []
                params = []
                if data.full_name is not None:
                    updates.append("full_name = %s")
                    params.append(data.full_name)
                if data.profession is not None:
                    updates.append("profession = %s")
                    params.append(data.profession)
                if data.department is not None:
                    updates.append("department = %s")
                    params.append(data.department)
                if data.salary is not None:
                    updates.append("salary = %s")
                    params.append(data.salary)

                if not updates:
                    return False

                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s;"
                cur.execute(query, params)
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def delete(self, user_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()

    def get_max_id(self) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM users;")
                row = cur.fetchone()
                return row["max_id"] if row else 0
        finally:
            conn.close()
