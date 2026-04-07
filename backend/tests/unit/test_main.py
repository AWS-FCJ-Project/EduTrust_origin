from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_persistence():
    users = SimpleNamespace(get_by_email=AsyncMock())
    persistence = SimpleNamespace(users=users)
    app.state.persistence = persistence
    return persistence


def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the AWS-FCJ-Backend API"}


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_me_requires_bearer_token(client):
    response = client.get("/user-info")
    assert response.status_code in (401, 403)


def test_me_returns_user_profile(client, mock_persistence):
    mock_persistence.users.get_by_email.return_value = {
        "_id": "user-id-1",
        "user_id": "user-id-1",
        "email": "me@example.com",
        "is_verified": True,
        "name": "Me",
        "role": "admin",
    }

    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={
            "email": "me@example.com",
            "sub": "cognito-sub-1",
            "token_use": "id",
        },
    ):
        response = client.get(
            "/user-info", headers={"Authorization": "Bearer id-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["id"] == "user-id-1"
        assert data["name"] == "Me"
        assert data["role"] == "admin"


def test_me_401_when_user_missing(client, mock_persistence):
    mock_persistence.users.get_by_email.return_value = None

    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={
            "email": "missing@example.com",
            "sub": "cognito-sub-2",
            "token_use": "id",
        },
    ):
        response = client.get(
            "/user-info", headers={"Authorization": "Bearer missing-id-token"}
        )
        assert response.status_code == 404
