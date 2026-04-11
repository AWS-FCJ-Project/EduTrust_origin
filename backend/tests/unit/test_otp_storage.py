from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from src.auth import otp_storage as otp_module


@pytest.fixture
def mock_otp_repo():
    return AsyncMock()


@pytest.fixture
def otp_repo_getter(mock_otp_repo):
    otp_module._set_otp_repo_getter(lambda: mock_otp_repo)
    yield mock_otp_repo
    # Reset to default after test
    otp_module._otp_repo_getter = None


@pytest.mark.asyncio
async def test_verify_otp_not_found(otp_repo_getter):
    otp_repo_getter.get_otp = AsyncMock(return_value=None)

    result = await otp_module.verify_otp("test@example.com", "123456", "login")
    assert result is False
    otp_repo_getter.get_otp.assert_awaited_once_with(
        "test@example.com", "login", "123456"
    )


@pytest.mark.asyncio
async def test_verify_otp_expired(otp_repo_getter):
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_doc = {
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
        "expire_at": expired_time,
    }
    otp_repo_getter.get_otp = AsyncMock(return_value=mock_doc)
    otp_repo_getter.delete_otp = AsyncMock()

    result = await otp_module.verify_otp("test@example.com", "123456", "login")
    assert result is False
    otp_repo_getter.delete_otp.assert_awaited_once_with("test@example.com", "login")


@pytest.mark.asyncio
async def test_verify_otp_valid_no_tz(otp_repo_getter):
    future_time = datetime.now() + timedelta(minutes=5)  # naive datetime
    mock_doc = {
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
        "expire_at": future_time,
    }
    otp_repo_getter.get_otp = AsyncMock(return_value=mock_doc)
    otp_repo_getter.delete_otp = AsyncMock()

    result = await otp_module.verify_otp("test@example.com", "123456", "login")
    assert result is True
    otp_repo_getter.delete_otp.assert_awaited_once_with("test@example.com", "login")


@pytest.mark.asyncio
async def test_verify_otp_valid_with_tz(otp_repo_getter):
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    mock_doc = {
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
        "expire_at": future_time,
    }
    otp_repo_getter.get_otp = AsyncMock(return_value=mock_doc)
    otp_repo_getter.delete_otp = AsyncMock()

    result = await otp_module.verify_otp("test@example.com", "123456", "login")
    assert result is True
    otp_repo_getter.delete_otp.assert_awaited_once_with("test@example.com", "login")


@pytest.mark.asyncio
async def test_save_otp(otp_repo_getter):
    otp_repo_getter.save_otp = AsyncMock()

    await otp_module.save_otp("test@example.com", "123456", "login", expire_seconds=300)

    otp_repo_getter.save_otp.assert_awaited_once_with(
        "test@example.com", "login", "123456", 300
    )


@pytest.mark.asyncio
async def test_cleanup_expired_otps(otp_repo_getter):
    otp_repo_getter.delete_expired_otps = AsyncMock()

    await otp_module.cleanup_expired_otps()

    otp_repo_getter.delete_expired_otps.assert_awaited_once()
