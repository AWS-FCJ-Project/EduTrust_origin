from __future__ import annotations

from src.db import get_engine
from src.models import Base


async def create_all() -> None:
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

