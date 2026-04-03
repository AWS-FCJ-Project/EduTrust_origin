from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select, update

from src.db import session_scope
from src.models import Otp


async def save_otp(email: str, otp: str, purpose: str, expire_seconds: int = 300):
    expire_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)

    async with session_scope() as session:
        existing = await session.execute(
            select(Otp).where(Otp.email == email, Otp.purpose == purpose)
        )
        row = existing.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if row is None:
            session.add(
                Otp(
                    email=email,
                    purpose=purpose,
                    otp=otp,
                    expire_at=expire_at,
                    created_at=now,
                )
            )
        else:
            await session.execute(
                update(Otp)
                .where(Otp.id == row.id)
                .values(otp=otp, expire_at=expire_at, created_at=now)
            )


async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    async with session_scope() as session:
        result = await session.execute(
            select(Otp).where(Otp.email == email, Otp.purpose == purpose, Otp.otp == otp)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False

        expire_at = row.expire_at
        if expire_at.tzinfo is None:
            expire_at = expire_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        await session.execute(delete(Otp).where(Otp.id == row.id))

        if expire_at < now:
            return False

        return True


async def cleanup_expired_otps():
    async with session_scope() as session:
        await session.execute(
            delete(Otp).where(Otp.expire_at < datetime.now(timezone.utc))
        )

