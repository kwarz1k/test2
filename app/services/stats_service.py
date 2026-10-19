import time
import uuid
from typing import List, Dict, Any, Optional
from collections import deque
from app.models import OperationLog

class StatsService:
    def __init__(self, max_logs: int = 500):
        self.logs: deque = deque(maxlen=max_logs)

    def log_operation(
        self,
        db_name: str,
        operation: str,
        duration_ms: float,
        affected_rows: int = 1,
        details: str = "",
        success: bool = True,
        error: Optional[str] = None
    ) -> OperationLog:
        now = time.time()
        time_str = time.strftime("%H:%M:%S", time.localtime(now))
        log_entry = OperationLog(
            id=str(uuid.uuid4())[:8],
            timestamp=now,
            time_str=time_str,
            db_name=db_name,
            operation=operation.upper(),
            duration_ms=round(duration_ms, 3),
            affected_rows=affected_rows,
            details=details,
            success=success,
            error=error
        )
        self.logs.appendleft(log_entry)
        return log_entry

    def get_recent_logs(self, limit: int = 100) -> List[OperationLog]:
        return list(self.logs)[:limit]

    def clear_logs(self):
        self.logs.clear()

    def get_aggregated_stats(self) -> Dict[str, Any]:
        """
        Computes average latency per operation type for each database.
        Returns data structured for Chart.js.
        """
        all_dbs = ["sqlite", "postgres", "mysql", "mongodb", "mssql", "oracle"]
        ops = ["SELECT", "INSERT", "UPDATE", "DELETE"]

        # structure: {db: {op: [durations]}}
        db_metrics: Dict[str, Dict[str, List[float]]] = {
            db: {op: [] for op in ops} for db in all_dbs
        }

        for log in self.logs:
            if not log.success or log.duration_ms <= 0:
                continue
            db = log.db_name.lower()
            op = log.operation.upper()
            if db in db_metrics and op in db_metrics[db]:
                db_metrics[db][op].append(log.duration_ms)

        # Calculate averages
        averages: Dict[str, Dict[str, float]] = {}
        for db in all_dbs:
            averages[db] = {}
            for op in ops:
                times = db_metrics[db][op]
                avg = round(sum(times) / len(times), 2) if times else 0.0
                averages[db][op] = avg

        # Chart.js datasets format
        # labels: ['PostgreSQL', 'SQLite', 'MySQL', 'MongoDB', 'MsSQL', 'Oracle']
        display_names = {
            "postgres": "PostgreSQL",
            "sqlite": "SQLite",
            "mysql": "MySQL",
            "mongodb": "MongoDB",
            "mssql": "MsSQL",
            "oracle": "Oracle"
        }

        chart_labels = [display_names[db] for db in all_dbs]

        colors = {
            "SELECT": "rgba(59, 130, 246, 0.8)",    # Blue
            "INSERT": "rgba(16, 185, 129, 0.8)",    # Green
            "UPDATE": "rgba(245, 158, 11, 0.8)",    # Amber
            "DELETE": "rgba(239, 68, 68, 0.8)"      # Red
        }

        datasets = []
        for op in ops:
            data = [averages[db][op] for db in all_dbs]
            datasets.append({
                "label": op,
                "data": data,
                "backgroundColor": colors[op]
            })

        return {
            "averages": averages,
            "chart_labels": chart_labels,
            "datasets": datasets,
            "total_logs": len(self.logs)
        }

stats_service = StatsService()
