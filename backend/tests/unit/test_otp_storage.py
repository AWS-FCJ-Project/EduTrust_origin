from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from backend.src.auth.otp_storage import cleanup_expired_otps, save_otp, verify_otp


@pytest.fixture
def mock_otp_collection():
    with patch("backend.src.auth.otp_storage.otp_collection") as mock_col:
        yield mock_col


@pytest.mark.asyncio
async def test_verify_otp_not_found(mock_otp_collection):
    mock_otp_collection.find_one = AsyncMock(return_value=None)

    result = await verify_otp("test@example.com", "123456", "login")
    assert result is False
    mock_otp_collection.find_one.assert_awaited_once_with(
        {"email": "test@example.com", "purpose": "login", "otp": "123456"}
    )


@pytest.mark.asyncio
async def test_verify_otp_expired(mock_otp_collection):
    expired_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_doc = {
        "_id": "doc_id",
        "expire_at": expired_time,
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
    }
    mock_otp_collection.find_one = AsyncMock(return_value=mock_doc)
    mock_otp_collection.delete_one = AsyncMock()

    result = await verify_otp("test@example.com", "123456", "login")
    assert result is False
    mock_otp_collection.delete_one.assert_awaited_once_with({"_id": "doc_id"})


@pytest.mark.asyncio
async def test_verify_otp_valid_no_tz(mock_otp_collection):
    future_time = datetime.now() + timedelta(minutes=5)  # naive datetime
    mock_doc = {
        "_id": "doc_id",
        "expire_at": future_time,
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
    }
    mock_otp_collection.find_one = AsyncMock(return_value=mock_doc)
    mock_otp_collection.delete_one = AsyncMock()

    result = await verify_otp("test@example.com", "123456", "login")
    assert result is True
    mock_otp_collection.delete_one.assert_awaited_once_with({"_id": "doc_id"})


@pytest.mark.asyncio
async def test_verify_otp_valid_with_tz(mock_otp_collection):
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    mock_doc = {
        "_id": "doc_id",
        "expire_at": future_time,
        "email": "test@example.com",
        "purpose": "login",
        "otp": "123456",
    }
    mock_otp_collection.find_one = AsyncMock(return_value=mock_doc)
    mock_otp_collection.delete_one = AsyncMock()

    result = await verify_otp("test@example.com", "123456", "login")
    assert result is True
    mock_otp_collection.delete_one.assert_awaited_once_with({"_id": "doc_id"})


@pytest.mark.asyncio
async def test_save_otp(mock_otp_collection):
    mock_otp_collection.update_one = AsyncMock()

    await save_otp("test@example.com", "123456", "login", expire_seconds=300)

    mock_otp_collection.update_one.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanup_expired_otps(mock_otp_collection):
    mock_otp_collection.delete_many = AsyncMock()

    await cleanup_expired_otps()

    mock_otp_collection.delete_many.assert_awaited_once()

