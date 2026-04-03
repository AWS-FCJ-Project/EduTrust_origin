from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from src.auth.jwt_handler import create_access_token
from src.main import app

client = TestClient(app)


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


def test_me_returns_user_profile():
    token = create_access_token(data={"sub": "me@example.com"})

    with patch(
        "src.routers.auth.login.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one:
        mock_find_one.return_value = {
            "_id": "user-id-1",
            "email": "me@example.com",
            "is_verified": True,
            "name": "Me",
            "role": "admin",
        }

        response = client.get(
            "/user-info", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["id"] == "user-id-1"
        assert data["name"] == "Me"
        assert data["role"] == "admin"


def test_me_404_when_user_missing():
    token = create_access_token(data={"sub": "missing@example.com"})

    with patch(
        "src.routers.auth.login.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one:
        mock_find_one.return_value = None

        response = client.get(
            "/user-info", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404
