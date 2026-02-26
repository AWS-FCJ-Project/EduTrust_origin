import pytest
from fastapi import HTTPException
from src.auth.dependencies import get_current_user


@pytest.mark.asyncio
async def test_get_current_user_no_token():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization=None, token=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated."


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(mocker):
    mocker.patch("src.auth.dependencies.decode_token", return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer invalid_token", token=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token."


@pytest.mark.asyncio
async def test_get_current_user_wrong_token_type(mocker):
    mocker.patch(
        "src.auth.dependencies.decode_token",
        return_value={"type": "refresh", "sub": "test@example.com"},
    )
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer refresh_token", token=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired token."


@pytest.mark.asyncio
async def test_get_current_user_no_subject(mocker):
    mocker.patch("src.auth.dependencies.decode_token", return_value={"type": "access"})
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(authorization="Bearer token_without_sub", token=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Token is missing subject."


@pytest.mark.asyncio
async def test_get_current_user_valid(mocker):
    mocker.patch(
        "src.auth.dependencies.decode_token",
        return_value={"type": "access", "sub": "test@example.com"},
    )
    email = await get_current_user(authorization="Bearer valid_token", token=None)
    assert email == "test@example.com"


@pytest.mark.asyncio
async def test_get_current_user_with_query_token(mocker):
    mocker.patch(
        "src.auth.dependencies.decode_token",
        return_value={"type": "access", "sub": "test@example.com"},
    )
    email = await get_current_user(authorization=None, token="valid_query_token")
    assert email == "test@example.com"
