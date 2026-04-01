from typing import Any, Optional

from pymongo.collection import Collection
from pymongo.database import Database


class DBHandler:
    """Base class for MongoDB document handlers."""

    def __init__(self, database: Database, collection_name: str):
        self._database = database
        self._collection_name = collection_name

    @property
    def collection(self) -> Collection:
        """Get the collection for this handler."""
        return self._database[self._collection_name]

    def find_one(
        self, query: dict, projection: Optional[dict] = None, **kwargs
    ) -> Optional[dict]:
        """Find a single document."""
        return self.collection.find_one(query, projection, **kwargs)

    def insert_one(self, document: dict) -> Any:
        """Insert a single document."""
        return self.collection.insert_one(document)

    def update_one(
        self, query: dict, update: dict, upsert: bool = False, **kwargs
    ) -> Any:
        """Update a single document."""
        return self.collection.update_one(query, update, upsert=upsert, **kwargs)

    def update_many(self, query: dict, update: dict, **kwargs) -> Any:
        """Update multiple documents."""
        return self.collection.update_many(query, update, **kwargs)

    def delete_one(self, query: dict, **kwargs) -> Any:
        """Delete a single document."""
        return self.collection.delete_one(query, **kwargs)

    def delete_many(self, query: dict, **kwargs) -> Any:
        """Delete multiple documents."""
        return self.collection.delete_many(query, **kwargs)

    def find_many(
        self,
        query: dict,
        projection: Optional[dict] = None,
        sort: Optional[list] = None,
        limit: Optional[int] = None,
        skip: Optional[int] = None,
        **kwargs,
    ) -> list:
        """Find multiple documents."""
        cursor = self.collection.find(query, projection, **kwargs)
        if sort:
            cursor = cursor.sort(sort)
        if skip is not None:
            cursor = cursor.skip(skip)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    def count_documents(self, query: dict, **kwargs) -> int:
        """Count documents matching query."""
        return self.collection.count_documents(query, **kwargs)

    def create_index(self, keys: list, **kwargs) -> str:
        """Create an index on the collection."""
        return self.collection.create_index(keys, **kwargs)

    def aggregate(self, pipeline: list) -> list:
        """Run an aggregation pipeline."""
        return list(self.collection.aggregate(pipeline))
