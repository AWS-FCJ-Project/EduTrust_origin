from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from src.app_config import app_config

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Missing dependency: sqlalchemy") from exc

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global _engine, _sessionmaker
    if _engine is not None:
        return _engine

    database_url = (app_config.DATABASE_URL or "").strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is required.")

    _engine = create_async_engine(database_url, echo=bool(app_config.SQL_ECHO))
    _sessionmaker = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def ping_db() -> dict[str, Any]:
    from sqlalchemy import text

    async with session_scope() as session:
        result = await session.execute(text("SELECT 1"))
        return {"ok": bool(result.scalar() == 1)}

