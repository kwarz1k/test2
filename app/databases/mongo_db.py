from pymongo import MongoClient, ReplaceOne
from typing import List, Optional
from app.databases.base import BaseDatabase
from app.models import User, UserUpdate
from app.config import config

class MongoDatabase(BaseDatabase):
    def __init__(self):
        super().__init__("mongodb", "MongoDB")
        self.client: Optional[MongoClient] = None

    def _get_collection(self):
        if not self.client:
            uri = f"mongodb://{config.MONGO_USER}:{config.MONGO_PASSWORD}@{config.MONGO_HOST}:{config.MONGO_PORT}/?authSource=admin&serverSelectionTimeoutMS=3000"
            self.client = MongoClient(uri)
        db = self.client[config.MONGO_DB]
        return db["users"]

    def connect(self) -> bool:
        try:
            coll = self._get_collection()
            # Ping command
            coll.database.command("ping")
            self.init_schema()
            self.is_ready = True
            return True
        except Exception:
            self.is_ready = False
            return False

    def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None

    def init_schema(self):
        coll = self._get_collection()
        coll.create_index("id", unique=True)
        coll.create_index("full_name")
        coll.create_index("profession")

    def count(self) -> int:
        coll = self._get_collection()
        return coll.count_documents({})

    def search(self, query: str = "", limit: int = 50) -> List[User]:
        coll = self._get_collection()
        if query:
            filter_query = {
                "$or": [
                    {"full_name": {"$regex": query, "$options": "i"}},
                    {"profession": {"$regex": query, "$options": "i"}}
                ]
            }
        else:
            filter_query = {}

        cursor = coll.find(filter_query, {"_id": 0}).sort("id", 1).limit(limit)
        return [
            User(
                id=doc["id"],
                full_name=doc.get("full_name", ""),
                profession=doc.get("profession", ""),
                department=doc.get("department", ""),
                salary=doc.get("salary", 0),
                created_at=doc.get("created_at", "")
            ) for doc in cursor
        ]

    def get_by_id(self, user_id: int) -> Optional[User]:
        coll = self._get_collection()
        doc = coll.find_one({"id": user_id}, {"_id": 0})
        if not doc:
            return None
        return User(
            id=doc["id"],
            full_name=doc.get("full_name", ""),
            profession=doc.get("profession", ""),
            department=doc.get("department", ""),
            salary=doc.get("salary", 0),
            created_at=doc.get("created_at", "")
        )

    def insert(self, user: User) -> bool:
        coll = self._get_collection()
        doc = {
            "id": user.id,
            "full_name": user.full_name,
            "profession": user.profession,
            "department": user.department,
            "salary": user.salary,
            "created_at": user.created_at
        }
        coll.replace_one({"id": user.id}, doc, upsert=True)
        return True

    def insert_many(self, users: List[User]) -> int:
        coll = self._get_collection()
        operations = [
            ReplaceOne(
                {"id": u.id},
                {
                    "id": u.id,
                    "full_name": u.full_name,
                    "profession": u.profession,
                    "department": u.department,
                    "salary": u.salary,
                    "created_at": u.created_at
                },
                upsert=True
            )
            for u in users
        ]
        if operations:
            res = coll.bulk_write(operations, ordered=False)
            return len(users)
        return 0

    def update(self, user_id: int, data: UserUpdate) -> bool:
        coll = self._get_collection()
        update_fields = {}
        if data.full_name is not None:
            update_fields["full_name"] = data.full_name
        if data.profession is not None:
            update_fields["profession"] = data.profession
        if data.department is not None:
            update_fields["department"] = data.department
        if data.salary is not None:
            update_fields["salary"] = data.salary

        if not update_fields:
            return False

        res = coll.update_one({"id": user_id}, {"$set": update_fields})
        return res.modified_count > 0 or res.matched_count > 0

    def delete(self, user_id: int) -> bool:
        coll = self._get_collection()
        res = coll.delete_one({"id": user_id})
        return res.deleted_count > 0

    def get_max_id(self) -> int:
        coll = self._get_collection()
        doc = coll.find_one({}, sort=[("id", -1)], projection={"id": 1, "_id": 0})
        return doc["id"] if doc and "id" in doc else 0
