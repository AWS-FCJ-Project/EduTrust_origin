from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.db import session_scope
from src.main import app
from src.models import User
from src.migrate import create_all


client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all()
    yield


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the AWS-FCJ-Backend API"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_me_requires_bearer_token():
    response = client.get("/user-info")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_returns_user_profile():
    async with session_scope() as session:
        session.add(
            User(
                id="user-id-1",
                cognito_sub="cognito-sub-1",
                email="me@example.com",
                hashed_password="x",
                is_verified=True,
                name="Me",
                role="admin",
            )
        )

    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={"email": "me@example.com", "sub": "cognito-sub-1", "token_use": "id"},
    ):
        response = client.get("/user-info", headers={"Authorization": "Bearer token"})
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["id"] == "user-id-1"
        assert data["name"] == "Me"
        assert data["role"] == "admin"


def test_me_404_when_user_missing():
    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={"email": "missing@example.com", "sub": "cognito-sub-2", "token_use": "id"},
    ):
        response = client.get("/user-info", headers={"Authorization": "Bearer token"})
        assert response.status_code == 404

