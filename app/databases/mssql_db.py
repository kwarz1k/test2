import pymssql
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class MSSQLDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("mssql", "Microsoft SQL Server")

    def _get_connection(self, database: Optional[str] = None):
        db_name = database if database else config.MSSQL_DB
        return pymssql.connect(
            server=config.MSSQL_HOST,
            port=config.MSSQL_PORT,
            user=config.MSSQL_USER,
            password=config.MSSQL_PASSWORD,
            database=db_name,
            login_timeout=3,
            as_dict=True,
            autocommit=True
        )

    def connect(self) -> bool:
        try:
            # First ensure benchmark_db exists by connecting to master
            master_conn = self._get_connection(database="master")
            cursor = master_conn.cursor()
            cursor.execute(f"IF DB_ID('{config.MSSQL_DB}') IS NULL CREATE DATABASE {config.MSSQL_DB};")
            master_conn.close()

            # Now connect to benchmark_db and init table
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
            cursor = conn.cursor()
            cursor.execute("""
                IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='users' AND xtype='U')
                CREATE TABLE users (
                    id INT PRIMARY KEY,
                    full_name NVARCHAR(255) NOT NULL,
                    profession NVARCHAR(255) NOT NULL,
                    department NVARCHAR(100),
                    salary INT,
                    created_at NVARCHAR(50)
                );
            """)
        finally:
            conn.close()

    def count(self) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS cnt FROM users;")
            row = cursor.fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if query:
                pattern = f"%{query}%"
                cursor.execute(
                    f"SELECT TOP {limit} id, full_name, profession, department, salary, created_at FROM users "
                    "WHERE full_name LIKE %s OR profession LIKE %s ORDER BY id ASC;",
                    (pattern, pattern)
                )
            else:
                cursor.execute(
                    f"SELECT TOP {limit} id, full_name, profession, department, salary, created_at FROM users "
                    "ORDER BY id ASC;"
                )
            rows = cursor.fetchall()
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
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name, profession, department, salary, created_at FROM users WHERE id = %s;", (user_id,))
            r = cursor.fetchone()
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
            cursor = conn.cursor()
            cursor.execute(
                """
                MERGE users AS target
                USING (SELECT %s AS id, %s AS full_name, %s AS profession, %s AS department, %s AS salary, %s AS created_at) AS src
                ON (target.id = src.id)
                WHEN MATCHED THEN
                    UPDATE SET target.full_name = src.full_name, target.profession = src.profession,
                               target.department = src.department, target.salary = src.salary, target.created_at = src.created_at
                WHEN NOT MATCHED THEN
                    INSERT (id, full_name, profession, department, salary, created_at)
                    VALUES (src.id, src.full_name, src.profession, src.department, src.salary, src.created_at);
                """,
                (user.id, user.full_name, user.profession, user.department, user.salary, user.created_at)
            )
            return True
        finally:
            conn.close()

    def insert_many(self, users: List[User]) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            data = [(u.id, u.full_name, u.profession, u.department, u.salary, u.created_at) for u in users]
            cursor.executemany(
                """
                MERGE users AS target
                USING (SELECT %s AS id, %s AS full_name, %s AS profession, %s AS department, %s AS salary, %s AS created_at) AS src
                ON (target.id = src.id)
                WHEN MATCHED THEN
                    UPDATE SET target.full_name = src.full_name, target.profession = src.profession,
                               target.department = src.department, target.salary = src.salary, target.created_at = src.created_at
                WHEN NOT MATCHED THEN
                    INSERT (id, full_name, profession, department, salary, created_at)
                    VALUES (src.id, src.full_name, src.profession, src.department, src.salary, src.created_at);
                """,
                data
            )
            return len(users)
        finally:
            conn.close()

    def update(self, user_id: int, data: UserUpdate) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
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
            cursor.execute(query, params)
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, user_id: int) -> bool:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_max_id(self) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(MAX(id), 0) AS max_id FROM users;")
            row = cursor.fetchone()
            return row["max_id"] if row else 0
        finally:
            conn.close()
