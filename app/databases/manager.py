import time
from typing import Dict, List, Optional, Tuple, Any
from app.databases.base import BaseDatabase
from app.databases.sqlite_db import SQLiteDatabase
from app.databases.postgres_db import PostgresDatabase
from app.databases.mysql_db import MySQLDatabase
from app.databases.mongo_db import MongoDatabase
from app.databases.mssql_db import MSSQLDatabase
from app.databases.oracle_db import OracleDatabase
from app.models import User, UserCreate, UserUpdate, DatabaseStatus
from app.services.stats_service import stats_service

class DatabaseManager:
    def __init__(self):
        self.databases: Dict[str, BaseDatabase] = {
            "sqlite": SQLiteDatabase(),
            "postgres": PostgresDatabase(),
            "mysql": MySQLDatabase(),
            "mongodb": MongoDatabase(),
            "mssql": MSSQLDatabase(),
            "oracle": OracleDatabase()
        }

    def get_db(self, name: str) -> Optional[BaseDatabase]:
        return self.databases.get(name.lower())

    def check_statuses(self) -> List[DatabaseStatus]:
        statuses = []
        for name, db in self.databases.items():
            start = time.perf_counter()
            connected = False
            count = 0
            err_msg = None
            try:
                connected = db.connect()
                if connected:
                    count = db.count()
            except Exception as e:
                connected = False
                err_msg = str(e)

            elapsed = round((time.perf_counter() - start) * 1000.0, 2)
            statuses.append(DatabaseStatus(
                name=name,
                display_name=db.display_name,
                connected=connected,
                latency_ms=elapsed if connected else None,
                records_count=count,
                error=err_msg
            ))
        return statuses

    def get_active_dbs(self, target: Optional[str] = None) -> List[BaseDatabase]:
        if target and target.lower() != "all":
            db = self.get_db(target)
            return [db] if db else []
        return [db for db in self.databases.values() if db.is_ready or db.connect()]

    def search(self, query: str = "", target_db: Optional[str] = None, limit: int = 50) -> Dict[str, Any]:
        dbs = self.get_active_dbs(target_db)
        if not dbs:
            return {"users": [], "timings": {}, "target": target_db}

        results = {}
        users = []
        timings = {}

        for db in dbs:
            try:
                start = time.perf_counter()
                db_users = db.search(query=query, limit=limit)
                dur = round((time.perf_counter() - start) * 1000.0, 3)
                timings[db.name] = dur
                stats_service.log_operation(
                    db_name=db.name,
                    operation="SELECT",
                    duration_ms=dur,
                    affected_rows=len(db_users),
                    details=f"Поиск '{query}', найдено {len(db_users)}"
                )
                if not users:
                    users = db_users
            except Exception as e:
                timings[db.name] = -1
                stats_service.log_operation(
                    db_name=db.name,
                    operation="SELECT",
                    duration_ms=0,
                    affected_rows=0,
                    details=f"Ошибка поиска: {str(e)}",
                    success=False,
                    error=str(e)
                )

        return {
            "users": users,
            "timings": timings,
            "target": target_db or "all",
            "query": query
        }

    def insert_user(self, data: UserCreate, target_db: Optional[str] = None) -> Dict[str, Any]:
        dbs = self.get_active_dbs(target_db)
        # Determine ID if not provided
        user_id = data.id
        if user_id is None:
            max_id = 0
            for db in self.databases.values():
                try:
                    m = db.get_max_id()
                    if m > max_id:
                        max_id = m
                except Exception:
                    pass
            user_id = max_id + 1

        now_str = time.strftime("%Y-%m-%d %H:%M:%S")
        user = User(
            id=user_id,
            full_name=data.full_name,
            profession=data.profession,
            department=data.department or "IT",
            salary=data.salary or 100000,
            created_at=now_str
        )

        timings = {}
        for db in dbs:
            try:
                start = time.perf_counter()
                ok = db.insert(user)
                dur = round((time.perf_counter() - start) * 1000.0, 3)
                timings[db.name] = dur
                stats_service.log_operation(
                    db_name=db.name,
                    operation="INSERT",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Добавлен пользователь id={user.id} ({user.full_name})"
                )
            except Exception as e:
                timings[db.name] = -1
                stats_service.log_operation(
                    db_name=db.name,
                    operation="INSERT",
                    duration_ms=0,
                    affected_rows=0,
                    details=f"Ошибка вставки: {str(e)}",
                    success=False,
                    error=str(e)
                )

        return {
            "user": user,
            "timings": timings,
            "target": target_db or "all"
        }

    def update_user(self, user_id: int, data: UserUpdate, target_db: Optional[str] = None) -> Dict[str, Any]:
        dbs = self.get_active_dbs(target_db)
        timings = {}
        for db in dbs:
            try:
                start = time.perf_counter()
                ok = db.update(user_id, data)
                dur = round((time.perf_counter() - start) * 1000.0, 3)
                timings[db.name] = dur
                stats_service.log_operation(
                    db_name=db.name,
                    operation="UPDATE",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Обновлен пользователь id={user_id}"
                )
            except Exception as e:
                timings[db.name] = -1
                stats_service.log_operation(
                    db_name=db.name,
                    operation="UPDATE",
                    duration_ms=0,
                    affected_rows=0,
                    details=f"Ошибка обновления: {str(e)}",
                    success=False,
                    error=str(e)
                )

        return {
            "user_id": user_id,
            "timings": timings,
            "target": target_db or "all"
        }

    def delete_user(self, user_id: int, target_db: Optional[str] = None) -> Dict[str, Any]:
        dbs = self.get_active_dbs(target_db)
        timings = {}
        for db in dbs:
            try:
                start = time.perf_counter()
                ok = db.delete(user_id)
                dur = round((time.perf_counter() - start) * 1000.0, 3)
                timings[db.name] = dur
                stats_service.log_operation(
                    db_name=db.name,
                    operation="DELETE",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Удален пользователь id={user_id}"
                )
            except Exception as e:
                timings[db.name] = -1
                stats_service.log_operation(
                    db_name=db.name,
                    operation="DELETE",
                    duration_ms=0,
                    affected_rows=0,
                    details=f"Ошибка удаления: {str(e)}",
                    success=False,
                    error=str(e)
                )

        return {
            "user_id": user_id,
            "timings": timings,
            "target": target_db or "all"
        }

db_manager = DatabaseManager()
