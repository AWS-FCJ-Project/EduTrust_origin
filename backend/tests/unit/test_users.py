import pytest
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user
from src.db import session_scope
from src.main import app
from src.models import Class, ClassSubjectTeacher, User
from src.migrate import create_all


client = TestClient(app)


@pytest.fixture(autouse=True)
async def setup_db():
    await create_all()
    yield


@pytest.fixture
def mock_user_session():
    def _mock(role="admin"):
        user = {"_id": f"{role}-id", "email": f"{role}@example.com", "role": role}
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yield _mock
    app.dependency_overrides.pop(get_current_user, None)


def test_list_teachers_permission_denied(mock_user_session):
    mock_user_session(role="student")
    response = client.get("/users/teachers")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_teachers_success(mock_user_session):
    mock_user_session(role="admin")

    async with session_scope() as session:
        teacher = User(
            id="teacher1",
            name="Teacher One",
            email="t1@example.com",
            hashed_password="x",
            role="teacher",
            is_verified=True,
            subjects=["Math"],
        )
        session.add(teacher)
        cls_hr = Class(
            id="class1",
            name="10A1",
            grade=10,
            school_year="2026-2027",
            homeroom_teacher_id="teacher1",
            status="active",
        )
        cls_st = Class(
            id="class2",
            name="11B1",
            grade=11,
            school_year="2026-2027",
            homeroom_teacher_id=None,
            status="active",
        )
        session.add_all([cls_hr, cls_st])
        session.add(
            ClassSubjectTeacher(class_id="class2", teacher_id="teacher1", subject="Math")
        )

    response = client.get("/users/teachers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    roles = [c["role"] for c in data[0]["assigned_classes"]]
    assert "Giáo viên Chủ nhiệm" in roles
    assert "Giáo viên Bộ môn (Math)" in roles


@pytest.mark.asyncio
async def test_list_admins_success(mock_user_session):
    mock_user_session(role="admin")
    async with session_scope() as session:
        session.add(
            User(
                id="admin1",
                name="Admin One",
                email="a1@example.com",
                hashed_password="x",
                role="admin",
                is_verified=True,
            )
        )

    response = client.get("/users/admins")
    assert response.status_code == 200
    assert response.json()[0]["name"] == "Admin One"

