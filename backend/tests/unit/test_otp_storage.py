from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete

from src.auth.otp_storage import cleanup_expired_otps, save_otp, verify_otp
from src.migrate import create_all
from src.db import session_scope
from src.models import Otp


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all()
    async with session_scope() as session:
        await session.execute(delete(Otp))
    yield


@pytest.mark.asyncio
async def test_verify_otp_not_found():
    assert await verify_otp("test@example.com", "123456", "login") is False


@pytest.mark.asyncio
async def test_save_and_verify_otp_valid():
    await save_otp("test@example.com", "123456", "login", expire_seconds=300)
    assert await verify_otp("test@example.com", "123456", "login") is True
    # One-time use
    assert await verify_otp("test@example.com", "123456", "login") is False


@pytest.mark.asyncio
async def test_verify_otp_expired():
    await save_otp("test@example.com", "123456", "login", expire_seconds=-1)
    assert await verify_otp("test@example.com", "123456", "login") is False


@pytest.mark.asyncio
async def test_cleanup_expired_otps():
    # Insert an expired otp directly.
    await create_all()
    async with session_scope() as session:
        session.add(
            Otp(
                email="test@example.com",
                purpose="login",
                otp="123456",
                expire_at=datetime.now(timezone.utc) - timedelta(minutes=5),
                created_at=datetime.now(timezone.utc),
            )
        )
    await cleanup_expired_otps()
    assert await verify_otp("test@example.com", "123456", "login") is False

