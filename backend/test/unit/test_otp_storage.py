from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_save_otp(mocker):
    mock_update_one = AsyncMock()
    mocker.patch(
        "src.auth.otp_storage.otp_collection.update_one", side_effect=mock_update_one
    )

    from src.auth.otp_storage import save_otp

    await save_otp("test@example.com", "123456", "register")

    mock_update_one.assert_called_once()
    args, kwargs = mock_update_one.call_args
    assert args[0] == {"email": "test@example.com", "purpose": "register"}
    assert "$set" in args[1]
    assert args[1]["$set"]["otp"] == "123456"
    assert kwargs.get("upsert") is True


@pytest.mark.asyncio
async def test_verify_otp_valid(mocker):
    future_time = datetime.now(timezone.utc) + timedelta(minutes=5)
    mock_find_one = AsyncMock(
        return_value={"_id": "mocked_id", "expire_at": future_time}
    )
    mock_delete_one = AsyncMock()

    mocker.patch(
        "src.auth.otp_storage.otp_collection.find_one", side_effect=mock_find_one
    )
    mocker.patch(
        "src.auth.otp_storage.otp_collection.delete_one", side_effect=mock_delete_one
    )

    from src.auth.otp_storage import verify_otp

    is_valid = await verify_otp("test@example.com", "123456", "register")

    assert is_valid is True
    mock_delete_one.assert_called_once_with({"_id": "mocked_id"})


@pytest.mark.asyncio
async def test_verify_otp_not_found(mocker):
    mock_find_one = AsyncMock(return_value=None)
    mocker.patch(
        "src.auth.otp_storage.otp_collection.find_one", side_effect=mock_find_one
    )

    from src.auth.otp_storage import verify_otp

    is_valid = await verify_otp("test@example.com", "123456", "register")

    assert is_valid is False


@pytest.mark.asyncio
async def test_verify_otp_expired(mocker):
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_find_one = AsyncMock(return_value={"_id": "mocked_id", "expire_at": past_time})
    mock_delete_one = AsyncMock()

    mocker.patch(
        "src.auth.otp_storage.otp_collection.find_one", side_effect=mock_find_one
    )
    mocker.patch(
        "src.auth.otp_storage.otp_collection.delete_one", side_effect=mock_delete_one
    )

    from src.auth.otp_storage import verify_otp

    is_valid = await verify_otp("test@example.com", "123456", "register")

    assert is_valid is False
    mock_delete_one.assert_called_once_with({"_id": "mocked_id"})


@pytest.mark.asyncio
async def test_cleanup_expired_otps(mocker):
    mock_delete_many = AsyncMock()
    mocker.patch(
        "src.auth.otp_storage.otp_collection.delete_many", side_effect=mock_delete_many
    )

    from src.auth.otp_storage import cleanup_expired_otps

    await cleanup_expired_otps()

    mock_delete_many.assert_called_once()
