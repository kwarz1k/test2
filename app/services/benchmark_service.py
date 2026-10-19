import time
import random
from typing import Dict, Any, List
from app.databases.manager import db_manager
from app.models import User, UserUpdate
from app.services.stats_service import stats_service
from app.services.seed_service import PROFESSIONS

class BenchmarkService:
    def run_suite(self, iterations: int = 10) -> Dict[str, Any]:
        """
        Runs standardized benchmark test suite on all connected databases:
        - `iterations` SELECT queries (by profession / name)
        - `iterations` INSERT queries
        - `iterations` UPDATE queries
        - `iterations` DELETE queries
        """
        all_dbs = ["sqlite", "postgres", "mysql", "mongodb", "mssql", "oracle"]
        results: Dict[str, Dict[str, Any]] = {}

        for db_name in all_dbs:
            db = db_manager.get_db(db_name)
            if not db or not (db.is_ready or db.connect()):
                results[db_name] = {
                    "connected": False,
                    "error": "Database not reachable"
                }
                continue

            select_times = []
            insert_times = []
            update_times = []
            delete_times = []

            # 1. Benchmark SELECT
            for _ in range(iterations):
                sample_profession = random.choice(PROFESSIONS)
                start = time.perf_counter()
                found = db.search(query=sample_profession, limit=20)
                dur = (time.perf_counter() - start) * 1000.0
                select_times.append(dur)
                stats_service.log_operation(
                    db_name=db.name,
                    operation="SELECT",
                    duration_ms=dur,
                    affected_rows=len(found),
                    details=f"Бенчмарк: поиск '{sample_profession}'"
                )

            # Base ID for bench temp users to avoid conflicts
            base_temp_id = 90000 + random.randint(100, 999)

            # 2. Benchmark INSERT
            for i in range(iterations):
                temp_user = User(
                    id=base_temp_id + i,
                    full_name=f"Тестовый Пользователь {i}",
                    profession="Тестировщик производительности",
                    department="Бенчмарк",
                    salary=150000,
                    created_at=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                start = time.perf_counter()
                ok = db.insert(temp_user)
                dur = (time.perf_counter() - start) * 1000.0
                insert_times.append(dur)
                stats_service.log_operation(
                    db_name=db.name,
                    operation="INSERT",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Бенчмарк: вставка id={temp_user.id}"
                )

            # 3. Benchmark UPDATE
            for i in range(iterations):
                target_id = base_temp_id + i
                update_data = UserUpdate(
                    profession=f"Обновленный Тестировщик {i}",
                    salary=180000 + i * 1000
                )
                start = time.perf_counter()
                ok = db.update(target_id, update_data)
                dur = (time.perf_counter() - start) * 1000.0
                update_times.append(dur)
                stats_service.log_operation(
                    db_name=db.name,
                    operation="UPDATE",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Бенчмарк: обновление id={target_id}"
                )

            # 4. Benchmark DELETE
            for i in range(iterations):
                target_id = base_temp_id + i
                start = time.perf_counter()
                ok = db.delete(target_id)
                dur = (time.perf_counter() - start) * 1000.0
                delete_times.append(dur)
                stats_service.log_operation(
                    db_name=db.name,
                    operation="DELETE",
                    duration_ms=dur,
                    affected_rows=1 if ok else 0,
                    details=f"Бенчмарк: удаление id={target_id}"
                )

            def avg(lst):
                return round(sum(lst) / len(lst), 2) if lst else 0.0

            results[db_name] = {
                "connected": True,
                "display_name": db.display_name,
                "iterations": iterations,
                "avg_select_ms": avg(select_times),
                "avg_insert_ms": avg(insert_times),
                "avg_update_ms": avg(update_times),
                "avg_delete_ms": avg(delete_times),
                "total_time_ms": round(sum(select_times + insert_times + update_times + delete_times), 2)
            }

        return {
            "iterations": iterations,
            "results": results,
            "aggregated_stats": stats_service.get_aggregated_stats()
        }

benchmark_service = BenchmarkService()
