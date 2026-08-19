"""
Database access layer.

Two backends are supported behind the same tiny async interface
(`find_one`, `find`, `insert_one`, `update_one`, `delete_one`, `count`):

  1. `InMemoryCollection` -- a dict/list backed store used by default so the
     API runs with zero setup (no MongoDB required) and so backend tests are
     fast and hermetic.
  2. Real MongoDB via Motor -- used when `USE_IN_MEMORY_DB=false`.

Routers/services never talk to Mongo or memory directly -- they always go
through `get_collection(name)`, so swapping the backend never touches
business logic.
"""
from __future__ import annotations

import itertools
from typing import Any, Optional

from app.config import settings


class InMemoryCollection:
    """A minimal async, MongoDB-flavored in-memory collection."""

    _id_counter = itertools.count(1)

    def __init__(self, name: str):
        self.name = name
        self._docs: dict[str, dict[str, Any]] = {}

    async def insert_one(self, doc: dict[str, Any]) -> dict[str, Any]:
        doc = dict(doc)
        if "_id" not in doc or doc["_id"] is None:
            doc["_id"] = f"{self.name}_{next(self._id_counter)}"
        self._docs[doc["_id"]] = doc
        return doc

    async def find_one(self, query: dict[str, Any]) -> Optional[dict[str, Any]]:
        for doc in self._docs.values():
            if _matches(doc, query):
                return doc
        return None

    async def find(
        self, query: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        query = query or {}
        return [doc for doc in self._docs.values() if _matches(doc, query)]

    async def update_one(
        self, query: dict[str, Any], update: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        doc = await self.find_one(query)
        if doc is None:
            return None
        fields = update.get("$set", update)
        doc.update(fields)
        self._docs[doc["_id"]] = doc
        return doc

    async def delete_one(self, query: dict[str, Any]) -> bool:
        doc = await self.find_one(query)
        if doc is None:
            return False
        del self._docs[doc["_id"]]
        return True

    async def count(self, query: Optional[dict[str, Any]] = None) -> int:
        return len(await self.find(query))

    def clear(self) -> None:
        """Test helper: wipe all documents."""
        self._docs.clear()


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(doc.get(k) == v for k, v in query.items())


class MotorCollectionAdapter:
    """Thin adapter so a real Motor collection matches our tiny interface."""

    def __init__(self, collection):
        self._collection = collection

    async def insert_one(self, doc: dict[str, Any]) -> dict[str, Any]:
        result = await self._collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def find_one(self, query: dict[str, Any]) -> Optional[dict[str, Any]]:
        return await self._collection.find_one(query)

    async def find(
        self, query: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        cursor = self._collection.find(query or {})
        return [doc async for doc in cursor]

    async def update_one(
        self, query: dict[str, Any], update: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        payload = update if "$set" in update else {"$set": update}
        await self._collection.update_one(query, payload)
        return await self.find_one(query)

    async def delete_one(self, query: dict[str, Any]) -> bool:
        result = await self._collection.delete_one(query)
        return result.deleted_count > 0

    async def count(self, query: Optional[dict[str, Any]] = None) -> int:
        return await self._collection.count_documents(query or {})


_in_memory_store: dict[str, InMemoryCollection] = {}
_motor_client = None
_motor_db = None

COLLECTION_NAMES = [
    "users",
    "subjects",
    "topics",
    "notes",
    "questions",
    "reviews",
    "study_sessions",
    "feynman_explanations",
]


def get_collection(name: str):
    """Return the collection adapter for `name`, honoring USE_IN_MEMORY_DB."""
    if settings.use_in_memory_db:
        if name not in _in_memory_store:
            _in_memory_store[name] = InMemoryCollection(name)
        return _in_memory_store[name]

    global _motor_client, _motor_db
    if _motor_db is None:
        from motor.motor_asyncio import AsyncIOMotorClient

        _motor_client = AsyncIOMotorClient(settings.mongo_uri)
        _motor_db = _motor_client[settings.mongo_db_name]
    return MotorCollectionAdapter(_motor_db[name])


def reset_in_memory_db() -> None:
    """Test helper: clear every in-memory collection between test cases."""
    for collection in _in_memory_store.values():
        collection.clear()
