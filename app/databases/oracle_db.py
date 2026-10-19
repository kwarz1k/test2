import oracledb
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class OracleDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("oracle", "Oracle Database")

    def _get_connection(self):
        dsn = f"{config.ORACLE_HOST}:{config.ORACLE_PORT}/{config.ORACLE_SERVICE}"
        return oracledb.connect(
            user=config.ORACLE_USER,
            password=config.ORACLE_PASSWORD,
            dsn=dsn,
            tcp_connect_timeout=3.0
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
                    BEGIN
                        EXECUTE IMMEDIATE 'CREATE TABLE users (
                            id NUMBER PRIMARY KEY,
                            full_name VARCHAR2(255) NOT NULL,
                            profession VARCHAR2(255) NOT NULL,
                            department VARCHAR2(100),
                            salary NUMBER,
                            created_at VARCHAR2(50)
                        )';
                    EXCEPTION
                        WHEN OTHERS THEN
                            IF SQLCODE != -955 THEN
                                RAISE;
                            END IF;
                    END;
                """)
            conn.commit()
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM users")
                row = cur.fetchone()
                return row[0] if row else 0
        finally:
            conn.close()

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                if query:
                    pattern = f"%{query.lower()}%"
                    cur.execute(
                        "SELECT id, full_name, profession, department, salary, created_at FROM users "
                        "WHERE LOWER(full_name) LIKE :1 OR LOWER(profession) LIKE :2 "
                        "ORDER BY id ASC FETCH FIRST :3 ROWS ONLY",
                        (pattern, pattern, limit)
                    )
                else:
                    cur.execute(
                        "SELECT id, full_name, profession, department, salary, created_at FROM users "
                        "ORDER BY id ASC FETCH FIRST :1 ROWS ONLY",
                        (limit,)
                    )
                rows = cur.fetchall()
                return [
                    User(
                        id=int(r[0]),
                        full_name=r[1],
                        profession=r[2],
                        department=r[3] or "",
                        salary=int(r[4]) if r[4] is not None else 0,
                        created_at=r[5] or ""
                    ) for r in rows
                ]
        finally:
            conn.close()

    def get_by_id(self, user_id: int) -> Optional[User]:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, full_name, profession, department, salary, created_at FROM users WHERE id = :1",
                    (user_id,)
                )
                r = cur.fetchone()
                if not r:
                    return None
                return User(
                    id=int(r[0]),
                    full_name=r[1],
                    profession=r[2],
                    department=r[3] or "",
                    salary=int(r[4]) if r[4] is not None else 0,
                    created_at=r[5] or ""
                )
        finally:
            conn.close()

    def insert(self, user: User) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    MERGE INTO users t
                    USING (SELECT :1 AS id, :2 AS full_name, :3 AS profession, :4 AS department, :5 AS salary, :6 AS created_at FROM dual) s
                    ON (t.id = s.id)
                    WHEN MATCHED THEN
                        UPDATE SET t.full_name = s.full_name, t.profession = s.profession,
                                   t.department = s.department, t.salary = s.salary, t.created_at = s.created_at
                    WHEN NOT MATCHED THEN
                        INSERT (id, full_name, profession, department, salary, created_at)
                        VALUES (s.id, s.full_name, s.profession, s.department, s.salary, s.created_at)
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
                    MERGE INTO users t
                    USING (SELECT :1 AS id, :2 AS full_name, :3 AS profession, :4 AS department, :5 AS salary, :6 AS created_at FROM dual) s
                    ON (t.id = s.id)
                    WHEN MATCHED THEN
                        UPDATE SET t.full_name = s.full_name, t.profession = s.profession,
                                   t.department = s.department, t.salary = s.salary, t.created_at = s.created_at
                    WHEN NOT MATCHED THEN
                        INSERT (id, full_name, profession, department, salary, created_at)
                        VALUES (s.id, s.full_name, s.profession, s.department, s.salary, s.created_at)
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
                idx = 1
                if data.full_name is not None:
                    updates.append(f"full_name = :{idx}")
                    params.append(data.full_name)
                    idx += 1
                if data.profession is not None:
                    updates.append(f"profession = :{idx}")
                    params.append(data.profession)
                    idx += 1
                if data.department is not None:
                    updates.append(f"department = :{idx}")
                    params.append(data.department)
                    idx += 1
                if data.salary is not None:
                    updates.append(f"salary = :{idx}")
                    params.append(data.salary)
                    idx += 1

                if not updates:
                    return False

                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = :{idx}"
                cur.execute(query, params)
                affected = cur.rowcount
            conn.commit()
            return affected > 0
        finally:
            conn.close()

    def delete(self, user_id: int) -> bool:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id = :1", (user_id,))
                affected = cur.rowcount
            conn.commit()
            return affected > 0
        finally:
            conn.close()

    def get_max_id(self) -> int:
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT NVL(MAX(id), 0) FROM users")
                row = cur.fetchone()
                return int(row[0]) if row else 0
        finally:
            conn.close()
