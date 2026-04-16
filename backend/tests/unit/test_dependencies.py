from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from src.auth.cognito_auth import CognitoAuthError
from src.auth.dependencies import (
    get_current_auth_claims,
    get_current_user,
    get_current_user_email,
)


@pytest.mark.asyncio
async def test_get_current_auth_claims_returns_verified_claims(monkeypatch):
    claims = {"email": "teacher@example.com", "token_use": "id"}
    monkeypatch.setattr(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        lambda token: claims,
    )

    result = await get_current_auth_claims(
        auth=SimpleNamespace(credentials="valid-token")
    )

    assert result == claims


@pytest.mark.asyncio
async def test_get_current_auth_claims_maps_cognito_error_to_http_exception(
    monkeypatch,
):
    def raise_auth_error(token: str):
        raise CognitoAuthError("token invalid", status_code=403)

    monkeypatch.setattr(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        raise_auth_error,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_auth_claims(auth=SimpleNamespace(credentials="bad-token"))

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "token invalid"
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.asyncio
async def test_get_current_auth_claims_defaults_to_401_when_status_code_missing(
    monkeypatch,
):
    def raise_auth_error(token: str):
        raise CognitoAuthError("invalid token", status_code=None)

    monkeypatch.setattr(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        raise_auth_error,
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_auth_claims(auth=SimpleNamespace(credentials="bad-token"))

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "invalid token"


@pytest.mark.asyncio
async def test_get_current_user_email_returns_email():
    result = await get_current_user_email(claims={"email": "student@example.com"})

    assert result == "student@example.com"


@pytest.mark.asyncio
async def test_get_current_user_email_raises_when_email_missing():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user_email(claims={})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_raises_when_email_missing():
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(persistence=None))
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request=request, claims={})

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"


@pytest.mark.asyncio
async def test_get_current_user_raises_when_user_not_found():
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=None))
    persistence = SimpleNamespace(users=users)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(persistence=persistence))
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(
            request=request,
            claims={"email": "missing@example.com"},
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
    users.get_by_email.assert_awaited_once_with("missing@example.com")


@pytest.mark.asyncio
async def test_get_current_user_backfills_role_and_id():
    stored_user = {
        "user_id": "user-123",
        "email": "admin@example.com",
        "name": "Admin",
    }
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=stored_user))
    persistence = SimpleNamespace(users=users)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(persistence=persistence))
    )

    result = await get_current_user(
        request=request,
        claims={
            "email": "admin@example.com",
            "cognito:groups": ["admin"],
        },
    )

    assert result["role"] == "admin"
    assert result["_id"] == "user-123"
    users.get_by_email.assert_awaited_once_with("admin@example.com")


@pytest.mark.asyncio
async def test_get_current_user_keeps_existing_role_and_id():
    stored_user = {
        "_id": "existing-id",
        "user_id": "user-123",
        "email": "teacher@example.com",
        "name": "Teacher",
        "role": "teacher",
    }
    users = SimpleNamespace(get_by_email=AsyncMock(return_value=stored_user))
    persistence = SimpleNamespace(users=users)
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(persistence=persistence))
    )

    result = await get_current_user(
        request=request,
        claims={
            "email": "teacher@example.com",
            "cognito:groups": ["admin"],
        },
    )

    assert result["role"] == "teacher"
    assert result["_id"] == "existing-id"
