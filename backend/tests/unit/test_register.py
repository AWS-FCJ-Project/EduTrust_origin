import io
from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from src.db import session_scope
from src.main import app
from src.models import Class, User
from src.migrate import create_all


client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all()
    async with session_scope() as session:
        await session.execute(delete(User))
        await session.execute(delete(Class))
    yield


@pytest.fixture(autouse=True)
def mock_rate_limiter():
    with patch(
        "src.extensions.limiter.limit", side_effect=lambda *args, **kwargs: lambda f: f
    ):
        yield


def test_multi_register_csv():
    csv_content = (
        b"email,password,role\n"
        b"testcsv1@example.com,Pass@word1,teacher\n"
        b"testcsv2@example.com,Pass@word2,teacher"
    )

    with patch("src.routers.auth.register.cognito_auth_service.ensure_user", return_value={"sub": "cognito-sub-test"}):
        files = {"file": ("users.csv", csv_content, "text/csv")}
        response = client.post("/multi-register", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "Successfully registered 2 users." in data["message"]


def test_multi_register_excel():
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

    with patch("src.routers.auth.register.cognito_auth_service.ensure_user", return_value={"sub": "cognito-sub-test"}):
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


def test_multi_register_invalid_format():
    files = {"file": ("users.txt", b"invalid", "text/plain")}
    response = client.post("/multi-register", files=files)
    assert response.status_code == 400
    assert "Invalid file format." in response.json()["detail"]


def test_multi_register_missing_columns():
    csv_content = b"email,role\ntest@example.com,teacher"
    files = {"file": ("users.csv", csv_content, "text/csv")}
    response = client.post("/multi-register", files=files)
    assert response.status_code == 400
    assert "must contain 'email' and 'password' columns" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_single_security():
    user_data = {
        "email": "testsingle@example.com",
        "password": "SecurePassword123#",
        "name": "Test User",
        "role": "student",
        "class_name": "10A1",
        "grade": 10,
    }

    with patch("src.routers.auth.register.cognito_auth_service.ensure_user", return_value={"sub": "cognito-sub-test"}):
        response = client.post("/register", json=user_data)
    assert response.status_code == 200

    async with session_scope() as session:
        user = (
            (await session.execute(select(User).where(User.email == "testsingle@example.com")))
            .scalar_one_or_none()
        )
        assert user is not None
        cls = (
            (await session.execute(select(Class).where(Class.name == "10A1", Class.grade == 10)))
            .scalar_one_or_none()
        )
        assert cls is not None
