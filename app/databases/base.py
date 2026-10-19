import time
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Any, Dict
from app.models import User, UserUpdate

class BaseDatabase(ABC):
    def __init__(self, name: str, display_name: str):
        self.name = name
        self.display_name = display_name
        self.is_ready = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close connection."""
        pass

    @abstractmethod
    def init_schema(self):
        """Create table/collection if not exists."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total count of users."""
        pass

    @abstractmethod
    def search(self, query: str = "", limit: int = 50) -> List[User]:
        """Search users by full_name or profession."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Fetch user by id."""
        pass

    @abstractmethod
    def insert(self, user: User) -> bool:
        """Insert a single user."""
        pass

    @abstractmethod
    def insert_many(self, users: List[User]) -> int:
        """Bulk insert users (e.g. 1000 items)."""
        pass

    @abstractmethod
    def update(self, user_id: int, data: UserUpdate) -> bool:
        """Update user by id."""
        pass

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Delete user by id."""
        pass

    @abstractmethod
    def get_max_id(self) -> int:
        """Get current maximum ID for incremental generation."""
        pass

    def measure(self, func, *args, **kwargs) -> Tuple[Any, float]:
        """
        Executes func and measures elapsed time in milliseconds with microsecond precision.
        Returns: (result, duration_ms)
        """
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return result, round(elapsed_ms, 3)
