import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

os.environ["AGENTS_CONFIG_PATH"] = "config/agents.yaml"
os.environ["LLMS_CONFIG_PATH"] = "config/llms.yaml"
os.environ["AGENT_MODEL"] = "gpt-3.5-turbo"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./.pytest_rds.db"
os.environ["RDS_AUTO_CREATE_TABLES"] = "true"
os.environ["LOGFIRE_TOKEN"] = "test-token"
os.environ["TAVILY_API_KEY"] = "tvly-test-key"
os.environ["LITELLM_API_KEY"] = "sk-test-key"


import pytest
from sqlalchemy import delete

from src.db import session_scope
from src.migrate import create_all
from src.models import (
    Class,
    ClassSubjectTeacher,
    Conversation,
    Exam,
    Message,
    Otp,
    Submission,
    User,
    Violation,
)


@pytest.fixture(autouse=True)
async def _clean_db():
    await create_all()
    async with session_scope() as session:
        # Delete in FK-safe order.
        await session.execute(delete(Message))
        await session.execute(delete(Conversation))
        await session.execute(delete(Violation))
        await session.execute(delete(Submission))
        await session.execute(delete(Exam))
        await session.execute(delete(ClassSubjectTeacher))
        await session.execute(delete(Class))
        await session.execute(delete(Otp))
        await session.execute(delete(User))
    yield
