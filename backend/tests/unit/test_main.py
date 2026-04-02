from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch("src.main.ConversationHandler"):
        yield


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
    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={
            "email": "me@example.com",
            "sub": "cognito-sub-1",
            "token_use": "id",
        },
    ), patch(
        "src.auth.dependencies.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one:
        mock_find_one.return_value = {
            "_id": "user-id-1",
            "cognito_sub": "cognito-sub-1",
            "email": "me@example.com",
            "is_verified": True,
            "name": "Me",
            "role": "admin",
        }

        response = client.get(
            "/user-info", headers={"Authorization": "Bearer cognito-id-token"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["id"] == "user-id-1"
        assert data["name"] == "Me"
        assert data["role"] == "admin"


def test_me_404_when_user_missing():
    with patch(
        "src.auth.dependencies.cognito_auth_service.verify_token",
        return_value={
            "email": "missing@example.com",
            "sub": "cognito-sub-2",
            "token_use": "id",
        },
    ), patch(
        "src.auth.dependencies.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one:
        mock_find_one.return_value = None

        response = client.get(
            "/user-info", headers={"Authorization": "Bearer missing-id-token"}
        )
        assert response.status_code == 404
