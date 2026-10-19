from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class User(BaseModel):
    id: int
    full_name: str
    profession: str
    department: str
    salary: int
    created_at: str

class UserCreate(BaseModel):
    id: Optional[int] = None
    full_name: str
    profession: str
    department: Optional[str] = "IT"
    salary: Optional[int] = 100000

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    profession: Optional[str] = None
    department: Optional[str] = None
    salary: Optional[int] = None

class OperationLog(BaseModel):
    id: str
    timestamp: float
    time_str: str
    db_name: str
    operation: str  # INSERT, SELECT, UPDATE, DELETE, SEED
    duration_ms: float
    affected_rows: int
    details: str
    success: bool = True
    error: Optional[str] = None

class BenchmarkRunRequest(BaseModel):
    iterations: int = Field(default=10, ge=1, le=100)
    databases: Optional[List[str]] = None  # None means all 6

class DatabaseStatus(BaseModel):
    name: str
    display_name: str
    connected: bool
    latency_ms: Optional[float] = None
    records_count: int = 0
    error: Optional[str] = None
