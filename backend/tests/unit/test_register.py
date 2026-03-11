import io
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch("src.main.ConversationHandler"):
        yield


from src.main import app

client = TestClient(app)


def test_multi_register_csv():
    csv_content = b"email,password\ntestcsv1@example.com,Pass@word1\ntestcsv2@example.com,Pass@word2"

    with patch(
        "src.routers.auth.register.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one, patch(
        "src.routers.auth.register.users_collection.insert_one", new_callable=AsyncMock
    ):

        def mock_find(query):
            if query.get("email") == "testcsv1@example.com":
                return {"email": "testcsv1@example.com"}
            return None

        mock_find_one.side_effect = mock_find

        files = {"file": ("users.csv", csv_content, "text/csv")}
        response = client.post("/multi-register", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "Successfully registered 1 users." in data["message"]
        assert len(data["errors"]) == 1
        assert "already registered" in data["errors"][0]


def test_multi_register_excel():
    df = pd.DataFrame(
        {
            "email": ["testexcel1@example.com", "testexcel2@example.com"],
            "password": ["Pass@word1", "Pass@word2"],
        }
    )

    excel_file = io.BytesIO()
    df.to_excel(excel_file, index=False)
    excel_file.seek(0)

    with patch(
        "src.routers.auth.register.users_collection.find_one", new_callable=AsyncMock
    ) as mock_find_one, patch(
        "src.routers.auth.register.users_collection.insert_one", new_callable=AsyncMock
    ):

        mock_find_one.return_value = None  # None of them exists

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
        assert len(data["errors"]) == 0


def test_multi_register_invalid_format():
    invalid_content = b"random text that is not a proper file"

    files = {"file": ("users.txt", invalid_content, "text/plain")}
    response = client.post("/multi-register", files=files)

    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


def test_multi_register_missing_columns():
    csv_content = b"name,age\nJohn,30\nJane,25"

    files = {"file": ("users.csv", csv_content, "text/csv")}
    response = client.post("/multi-register", files=files)

    assert response.status_code == 400
    assert (
        "File must contain 'email' and 'password' columns" in response.json()["detail"]
    )
