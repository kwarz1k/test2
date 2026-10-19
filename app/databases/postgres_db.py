import psycopg2
from psycopg2.extras import RealDictCursor, execute_values
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class PostgresDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("postgres", "PostgreSQL")

    def _get_connection(self):
        return psycopg2.connect(
            host=config.POSTGRES_HOST,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            dbname=config.POSTGRES_DB,
            connect_timeout=3
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
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY,
                        full_name VARCHAR(255) NOT NULL,
                        profession VARCHAR(255) NOT NULL,
                        department VARCHAR(100),
                        salary INT,
                        created_at VARCHAR(50)
                    );
                """)
            conn.commit()

    def count(self) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users;")
                return cur.fetchone()[0]

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if query:
                    pattern = f"%{query}%"
                    cur.execute(
                        "SELECT id, full_name, profession, department, salary, created_at FROM users "
                        "WHERE full_name ILIKE %s OR profession ILIKE %s "
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

    def get_by_id(self, user_id: int) -> Optional[User]:
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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

    def insert(self, user: User) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (id, full_name, profession, department, salary, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        profession = EXCLUDED.profession,
                        department = EXCLUDED.department,
                        salary = EXCLUDED.salary,
                        created_at = EXCLUDED.created_at;
                    """,
                    (user.id, user.full_name, user.profession, user.department, user.salary, user.created_at)
                )
            conn.commit()
            return True

    def insert_many(self, users: List[User]) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                data = [(u.id, u.full_name, u.profession, u.department, u.salary, u.created_at) for u in users]
                execute_values(
                    cur,
                    """
                    INSERT INTO users (id, full_name, profession, department, salary, created_at)
                    VALUES %s
                    ON CONFLICT (id) DO UPDATE SET
                        full_name = EXCLUDED.full_name,
                        profession = EXCLUDED.profession,
                        department = EXCLUDED.department,
                        salary = EXCLUDED.salary,
                        created_at = EXCLUDED.created_at;
                    """,
                    data
                )
            conn.commit()
            return len(users)

    def update(self, user_id: int, data: UserUpdate) -> bool:
        with self._get_connection() as conn:
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

    def delete(self, user_id: int) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = %s;", (user_id,))
                conn.commit()
                return cur.rowcount > 0

    def get_max_id(self) -> int:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COALESCE(MAX(id), 0) FROM users;")
                return cur.fetchone()[0]
