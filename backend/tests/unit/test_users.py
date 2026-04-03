from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from src.auth.dependencies import get_current_user
from src.main import app

client = TestClient(app)


@pytest.fixture
def mock_user_session():
    def _mock(role="admin"):
        user = {"email": f"{role}@example.com", "role": role}
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _mock
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def mock_user_db():
    with patch("src.routers.auth.login.users_collection") as mock_users, patch(
        "src.routers.auth.login.classes_collection"
    ) as mock_classes:

        # Mock users.find()
        mock_cursor_users = AsyncMock()
        mock_users.find.return_value = mock_cursor_users

        # Mock classes.find()
        mock_cursor_classes = AsyncMock()
        mock_classes.find.return_value = mock_cursor_classes

        yield mock_users, mock_classes


def test_list_teachers_permission_denied(mock_user_session):
    mock_user_session(role="student")
    response = client.get("/users/teachers")
    assert response.status_code == 403


def test_list_teachers_success(mock_user_session, mock_user_db):
    mock_user_session(role="admin")
    mock_users, mock_classes = mock_user_db

    # Mock teacher entries
    mock_users.find.return_value.__aiter__.return_value = [
        {
            "_id": "teacher1",
            "name": "Teacher One",
            "email": "t1@example.com",
            "subjects": ["Math"],
        }
    ]

    # Mock class sequences (Homeroom then Subject)
    mock_hr_cursor = AsyncMock()
    mock_hr_cursor.__aiter__.return_value = [{"_id": "class1", "name": "10A1"}]

    mock_st_cursor = AsyncMock()
    mock_st_cursor.__aiter__.return_value = [
        {
            "_id": "class2",
            "name": "11B1",
            "subject_teachers": [{"teacher_id": "teacher1", "subject": "Math"}],
        }
    ]

    mock_classes.find.side_effect = [mock_hr_cursor, mock_st_cursor]

    response = client.get("/users/teachers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    roles = [c["role"] for c in data[0]["assigned_classes"]]
    assert "Giáo viên Chủ nhiệm" in roles
    assert "Giáo viên Bộ môn (Math)" in roles


def test_list_admins_success(mock_user_session, mock_user_db):
    mock_user_session(role="admin")
    mock_users, _ = mock_user_db

    mock_users.find.return_value.__aiter__.return_value = [
        {"_id": "admin1", "name": "Admin One", "email": "a1@example.com"}
    ]

    response = client.get("/users/admins")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Admin One"
