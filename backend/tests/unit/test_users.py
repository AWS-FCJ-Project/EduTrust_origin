from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from src.auth.dependencies import get_current_user
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_user_session():
    def _mock(role="admin"):
        user = {"email": f"{role}@example.com", "role": role}
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _mock
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_persistence(client):
    users = SimpleNamespace(
        list_by_role=AsyncMock(),
    )
    classes = SimpleNamespace(
        list_by_homeroom_teacher=AsyncMock(),
        list_all=AsyncMock(),
    )
    persistence = SimpleNamespace(users=users, classes=classes)
    app.state.persistence = persistence
    yield persistence


def test_list_teachers_permission_denied(client, mock_user_session):
    mock_user_session(role="student")
    response = client.get("/users/teachers")
    assert response.status_code == 403


def test_list_teachers_success(client, mock_user_session, mock_persistence):
    mock_user_session(role="admin")

    mock_persistence.users.list_by_role.return_value = [
        {
            "_id": "teacher1",
            "name": "Teacher One",
            "email": "t1@example.com",
            "subjects": ["Math"],
        }
    ]

    mock_persistence.classes.list_by_homeroom_teacher.return_value = [
        {"_id": "class1", "name": "10A1"}
    ]
    mock_persistence.classes.list_all.return_value = [
        {
            "_id": "class2",
            "name": "11B1",
            "subject_teachers": [{"teacher_id": "teacher1", "subject": "Math"}],
        }
    ]

    response = client.get("/users/teachers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    roles = [c["role"] for c in data[0]["assigned_classes"]]
    assert "Homeroom Teacher" in roles
    assert "Subject Teacher (Math)" in roles


def test_list_admins_success(client, mock_user_session, mock_persistence):
    mock_user_session(role="admin")
    mock_persistence.users.list_by_role.return_value = [
        {"_id": "admin1", "name": "Admin One", "email": "a1@example.com"}
    ]

    response = client.get("/users/admins")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Admin One"
