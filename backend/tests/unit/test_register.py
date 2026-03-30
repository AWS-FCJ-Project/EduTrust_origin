import io
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch("src.main.ConversationHandler"), \
         patch("src.extensions.limiter.limit", side_effect=lambda *args, **kwargs: lambda f: f):
        yield

from src.main import app
from src.auth.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_db():
    with patch("src.routers.auth.register.users_collection") as mock_users, \
         patch("src.routers.auth.register.classes_collection") as mock_classes:
        mock_users.insert_many = AsyncMock(return_value=AsyncMock())
        mock_users.insert_one = AsyncMock(return_value=AsyncMock())
        mock_users.find_one = AsyncMock(return_value=None)
        mock_classes.insert_one = AsyncMock(return_value=AsyncMock())
        mock_classes.find_one = AsyncMock(return_value=None)
        
        # Mock find().to_list()
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_users.find.return_value = mock_cursor
        
        yield mock_users, mock_classes

def test_multi_register_csv(mock_db):
    mock_users, _ = mock_db
    csv_content = (
        b"email,password,role\n"
        b"testcsv1@example.com,Pass@word1,teacher\n"
        b"testcsv2@example.com,Pass@word2,teacher"
    )

    # Mock finding existing user to simulate one success and one failure
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=[{"email": "testcsv1@example.com"}])
    mock_users.find.return_value = mock_cursor

    files = {"file": ("users.csv", csv_content, "text/csv")}
    response = client.post("/multi-register", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "Successfully registered 1 users." in data["message"]
    assert len(data["errors"]) == 1
    
    # Verify password_plain is NOT in the documents to be inserted
    args, _ = mock_users.insert_many.call_args
    docs = args[0]
    for doc in docs:
        assert "password_plain" not in doc
        assert "hashed_password" in doc

def test_multi_register_excel(mock_db):
    mock_users, _ = mock_db
    df = pd.DataFrame({
        "email": ["testexcel1@example.com", "testexcel2@example.com"],
        "password": ["Pass@word1", "Pass@word2"],
        "role": ["teacher", "teacher"],
    })

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
    
    args, _ = mock_users.insert_many.call_args
    for doc in args[0]:
        assert "password_plain" not in doc

def test_multi_register_invalid_format():
    files = {"file": ("users.txt", b"invalid", "text/plain")}
    response = client.post("/multi-register", files=files)
    assert response.status_code == 400

def test_register_single_security(mock_db):
    mock_users, mock_classes = mock_db
    user_data = {
        "email": "testsingle@example.com",
        "password": "SecurePassword123#",
        "name": "Test User",
        "role": "student",
        "class_name": "10A1",
        "grade": 10,
    }
    mock_classes.find_one.return_value = {"name": "10A1"}

    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    
    args, _ = mock_users.insert_one.call_args
    doc = args[0]
    assert "password_plain" not in doc
    assert "hashed_password" in doc
