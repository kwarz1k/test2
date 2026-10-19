import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Config:
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "app_user")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "app_password")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "benchmark_db")

    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "app_user")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "app_password")
    MYSQL_DB = os.getenv("MYSQL_DB", "benchmark_db")

    # MongoDB
    MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
    MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
    MONGO_USER = os.getenv("MONGO_USER", "app_user")
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "app_password")
    MONGO_DB = os.getenv("MONGO_DB", "benchmark_db")

    # MsSQL
    MSSQL_HOST = os.getenv("MSSQL_HOST", "mssql")
    MSSQL_PORT = int(os.getenv("MSSQL_PORT", "1433"))
    MSSQL_USER = os.getenv("MSSQL_USER", "sa")
    MSSQL_PASSWORD = os.getenv("MSSQL_PASSWORD", "StrongPassword123!")
    MSSQL_DB = os.getenv("MSSQL_DB", "benchmark_db")

    # Oracle
    ORACLE_HOST = os.getenv("ORACLE_HOST", "oracle")
    ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
    ORACLE_SERVICE = os.getenv("ORACLE_SERVICE", "FREEPDB1")
    ORACLE_USER = os.getenv("ORACLE_USER", "SYSTEM")
    ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "OraclePassword123!")

    # SQLite
    SQLITE_PATH = os.getenv("SQLITE_PATH", str(BASE_DIR / "data" / "benchmark.db"))

config = Config()
