import io
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_persistence(client):
    users = SimpleNamespace(
        get_by_email=AsyncMock(),
        insert_one=AsyncMock(),
    )
    classes = SimpleNamespace(
        get_by_name_grade=AsyncMock(),
        insert_one=AsyncMock(),
    )
    persistence = SimpleNamespace(users=users, classes=classes)
    app.state.persistence = persistence
    yield persistence


def test_multi_register_csv(client, mock_persistence):
    csv_content = (
        b"email,password,role\n"
        b"testcsv1@example.com,Pass@word1,teacher\n"
        b"testcsv2@example.com,Pass@word2,teacher"
    )

    mock_persistence.users.get_by_email.side_effect = [
        {"_id": "u1", "email": "testcsv1@example.com"},
        None,
    ]

    files = {"file": ("users.csv", csv_content, "text/csv")}
    response = client.post("/multi-register", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "Successfully registered 1 users." in data["message"]
    assert len(data["errors"]) == 1

    # Verify password_plain is NOT in the documents to be inserted
    assert mock_persistence.users.insert_one.await_count == 1
    doc = mock_persistence.users.insert_one.call_args.args[0]
    assert "password_plain" not in doc
    assert "hashed_password" in doc


def test_multi_register_excel(client, mock_persistence):
    mock_persistence.users.get_by_email.return_value = None

    df = pd.DataFrame(
        {
            "email": ["testexcel1@example.com", "testexcel2@example.com"],
            "password": ["Pass@word1", "Pass@word2"],
            "role": ["teacher", "teacher"],
        }
    )

    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    files = {
        "file": (
            "users.xlsx",
            excel_file.read(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }
    response = client.post("/multi-register", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "Successfully registered 2 users." in data["message"]

    assert mock_persistence.users.insert_one.await_count == 2
    for call in mock_persistence.users.insert_one.call_args_list:
        doc = call.args[0]
        assert "password_plain" not in doc
        assert "hashed_password" in doc


def test_multi_register_invalid_format(client):
    files = {"file": ("users.txt", b"invalid", "text/plain")}
    response = client.post("/multi-register", files=files)
    assert response.status_code == 400
    assert "Invalid file format." in response.json()["detail"]


def test_multi_register_missing_columns(client):
    csv_content = b"email,role\ntest@example.com,teacher"
    files = {"file": ("users.csv", csv_content, "text/csv")}
    response = client.post("/multi-register", files=files)
    assert response.status_code == 400
    assert "must contain 'email' and 'password' columns" in response.json()["detail"]


def test_register_single_security(client, mock_persistence):
    user_data = {
        "email": "testsingle@example.com",
        "password": "SecurePassword123#",
        "name": "Test User",
        "role": "student",
        "class_name": "10A1",
        "grade": 10,
    }
    mock_persistence.users.get_by_email.return_value = None
    mock_persistence.classes.get_by_name_grade.return_value = None

    response = client.post("/register", json=user_data)
    assert response.status_code == 200

    assert mock_persistence.classes.insert_one.await_count == 1
    assert mock_persistence.users.insert_one.await_count == 1

    doc = mock_persistence.users.insert_one.call_args.args[0]
    assert "password_plain" not in doc
    assert "hashed_password" in doc
