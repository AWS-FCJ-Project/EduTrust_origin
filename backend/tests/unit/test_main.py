from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.auth.jwt_handler import create_access_token
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_persistence(client):
    users = SimpleNamespace(get_by_email=AsyncMock())
    persistence = SimpleNamespace(users=users)
    app.state.persistence = persistence
    yield persistence


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
    token = create_access_token(data={"sub": "me@example.com"})

    mock_persistence.users.get_by_email.return_value = {
        "_id": "user-id-1",
        "email": "me@example.com",
        "is_verified": True,
        "name": "Me",
        "role": "admin",
    }

    response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert data["id"] == "user-id-1"
    assert data["name"] == "Me"
    assert data["role"] == "admin"


def test_me_404_when_user_missing(client, mock_persistence):
    token = create_access_token(data={"sub": "missing@example.com"})

    mock_persistence.users.get_by_email.return_value = None

    response = client.get("/user-info", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
