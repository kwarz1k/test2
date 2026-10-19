import time
import random
from typing import List, Dict, Any, Optional
from faker import Faker
from app.models import User
from app.databases.manager import db_manager
from app.services.stats_service import stats_service

PROFESSIONS = [
    "Backend-разработчик",
    "Frontend-разработчик",
    "Fullstack-разработчик",
    "DevOps-инженер",
    "Системный аналитик",
    "Data Scientist",
    "Data Engineer",
    "Инженер по тестированию (QA)",
    "Архитектор решений",
    "Администратор баз данных (DBA)",
    "Специалист по информационной безопасности",
    "UI/UX Дизайнер",
    "Product Manager",
    "Project Manager",
    "Team Lead",
    "ML-инженер",
    "Системный администратор",
    "Бизнес-аналитик",
    "Инженер технической поддержки",
    "Scrum-мастер"
]

DEPARTMENTS = [
    "Разработка",
    "Инфраструктура и Cloud",
    "Аналитика и Big Data",
    "Контроль качества",
    "Информационная безопасность",
    "Дизайн и исследования",
    "Управление проектами",
    "Операционная деятельность"
]

class SeedService:
    def __init__(self):
        self._cached_dataset: Optional[List[User]] = None

    def generate_users(self, count: int = 1000, seed: int = 42) -> List[User]:
        """
        Generates deterministic dataset of `count` users using ru_RU Faker.
        Same seed guarantees identical 1000 rows across all databases.
        """
        if self._cached_dataset and len(self._cached_dataset) == count:
            return self._cached_dataset

        fake = Faker("ru_RU")
        Faker.seed(seed)
        random.seed(seed)

        users: List[User] = []
        base_time = 1704067200  # 2024-01-01 00:00:00

        for i in range(1, count + 1):
            name = fake.name()
            profession = random.choice(PROFESSIONS)
            department = random.choice(DEPARTMENTS)
            salary = random.randint(80, 400) * 1000
            created_timestamp = base_time + (i * 3600)
            created_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(created_timestamp))

            users.append(User(
                id=i,
                full_name=name,
                profession=profession,
                department=department,
                salary=salary,
                created_at=created_at
            ))

        self._cached_dataset = users
        return users

    def seed_single_db(self, db_name: str, count: int = 1000) -> Dict[str, Any]:
        db = db_manager.get_db(db_name)
        if not db:
            return {"db": db_name, "success": False, "error": "Database not found"}

        if not db.connect():
            return {"db": db_name, "success": False, "error": "Cannot connect to database"}

        users = self.generate_users(count)
        start = time.perf_counter()
        try:
            inserted = db.insert_many(users)
            dur = round((time.perf_counter() - start) * 1000.0, 2)
            stats_service.log_operation(
                db_name=db.name,
                operation="SEED",
                duration_ms=dur,
                affected_rows=inserted,
                details=f"Загрузка {inserted} записей"
            )
            return {
                "db": db.name,
                "display_name": db.display_name,
                "success": True,
                "count": inserted,
                "duration_ms": dur
            }
        except Exception as e:
            dur = round((time.perf_counter() - start) * 1000.0, 2)
            stats_service.log_operation(
                db_name=db.name,
                operation="SEED",
                duration_ms=dur,
                affected_rows=0,
                details=f"Ошибка сидинга: {str(e)}",
                success=False,
                error=str(e)
            )
            return {
                "db": db.name,
                "display_name": db.display_name,
                "success": False,
                "count": 0,
                "duration_ms": dur,
                "error": str(e)
            }

    def seed_all(self, count: int = 1000) -> Dict[str, Any]:
        users = self.generate_users(count)
        results = {}
        for name in ["sqlite", "postgres", "mysql", "mongodb", "mssql", "oracle"]:
            res = self.seed_single_db(name, count)
            results[name] = res

        return {
            "total_users": count,
            "results": results
        }

seed_service = SeedService()
