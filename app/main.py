from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Query, HTTPException, Path as PathParam
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.models import UserCreate, UserUpdate, BenchmarkRunRequest
from app.databases.manager import db_manager
from app.services.seed_service import seed_service
from app.services.stats_service import stats_service
from app.services.benchmark_service import benchmark_service

app = FastAPI(
    title="Database Benchmark & CRUD Dashboard",
    description="Сравнение производительности 6 СУБД: PostgreSQL, SQLite, MySQL, MongoDB, MsSQL, Oracle",
    version="1.0.0"
)

# Enable CORS for convenience
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_dashboard():
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse({"status": "Dashboard frontend file not ready yet"}, status_code=404)
    return FileResponse(index_file)

@app.get("/api/status")
def get_database_status():
    """Returns connectivity and records count for each of the 6 databases."""
    return db_manager.check_statuses()

@app.post("/api/seed")
def seed_databases(db: Optional[str] = Query("all", description="Target database (all, sqlite, postgres, mysql, mongodb, mssql, oracle)")):
    """Seeds 1000 identical Russian user records into databases."""
    if db.lower() == "all":
        return seed_service.seed_all(count=1000)
    else:
        return seed_service.seed_single_db(db.lower(), count=1000)

@app.get("/api/users")
def search_users(
    q: Optional[str] = Query("", description="Search term for full_name or profession"),
    db: Optional[str] = Query("all", description="Database name or 'all'"),
    limit: Optional[int] = Query(50, ge=1, le=500)
):
    """Searches users and measures SELECT latency across databases."""
    return db_manager.search(query=q, target_db=db, limit=limit)

@app.post("/api/users")
def create_user(
    user_data: UserCreate,
    db: Optional[str] = Query("all", description="Database to insert user to, or 'all'")
):
    """Inserts a new user and records INSERT latency across databases."""
    return db_manager.insert_user(data=user_data, target_db=db)

@app.put("/api/users/{user_id}")
def update_user(
    user_id: int = PathParam(..., description="ID of the user to update"),
    user_data: UserUpdate = ...,
    db: Optional[str] = Query("all", description="Database to update user in, or 'all'")
):
    """Updates user information and records UPDATE latency across databases."""
    return db_manager.update_user(user_id=user_id, data=user_data, target_db=db)

@app.delete("/api/users/{user_id}")
def delete_user(
    user_id: int = PathParam(..., description="ID of the user to delete"),
    db: Optional[str] = Query("all", description="Database to delete user from, or 'all'")
):
    """Deletes a user and records DELETE latency across databases."""
    return db_manager.delete_user(user_id=user_id, target_db=db)

@app.get("/api/stats")
def get_stats(limit: Optional[int] = Query(50, ge=5, le=200)):
    """Returns aggregated performance metrics and recent operation logs."""
    return {
        "aggregated": stats_service.get_aggregated_stats(),
        "recent_logs": stats_service.get_recent_logs(limit=limit)
    }

@app.post("/api/stats/clear")
def clear_stats():
    """Clears history logs."""
    stats_service.clear_logs()
    return {"status": "ok", "message": "Статистика очищена"}

@app.post("/api/benchmark")
def run_benchmark(req: BenchmarkRunRequest = BenchmarkRunRequest()):
    """Executes comparative benchmark suite on all connected databases."""
    return benchmark_service.run_suite(iterations=req.iterations)
