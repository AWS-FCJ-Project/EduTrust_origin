from typing import Any, Optional


class BaseRepository:
    """Base class for all repositories."""

    async def get_by_id(self, id: str) -> Optional[dict]:
        raise NotImplementedError

    async def create(self, doc: dict) -> str:
        raise NotImplementedError

    async def update(self, id: str, fields: dict) -> bool:
        raise NotImplementedError

    async def delete(self, id: str) -> bool:
        raise NotImplementedError

    async def find_one(self, query: dict) -> Optional[dict]:
        raise NotImplementedError

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        raise NotImplementedError

    async def insert_one(self, doc: dict) -> Any:
        raise NotImplementedError

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> Any:
        raise NotImplementedError

    async def delete_one(self, query: dict) -> Any:
        raise NotImplementedError
