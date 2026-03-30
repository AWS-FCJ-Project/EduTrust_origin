from datetime import datetime, timezone

from bson import ObjectId
from src.routers.exam_routes import exam_helper
from src.schemas.school_schemas import ExamCreate, ExamUpdate


def test_exam_create_defaults_exam_type():
    payload = ExamCreate(
        title="Quiz",
        subject="Mathematics",
        class_id="507f1f77bcf86cd799439011",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
    )

    assert payload.exam_type == "15-minute quiz"


def test_exam_update_accepts_exam_type():
    payload = ExamUpdate(exam_type="Final exam")

    assert payload.exam_type == "Final exam"


def test_exam_helper_returns_exam_type_from_exam_document():
    exam = {
        "_id": ObjectId(),
        "title": "Exam 1",
        "description": "Description",
        "subject": "Chemistry",
        "exam_type": "Midterm exam",
        "teacher_id": "t-1",
        "class_id": "c-1",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "questions": [],
    }

    result = exam_helper(exam)

    assert result["exam_type"] == "Midterm exam"


def test_exam_helper_falls_back_for_legacy_exams_without_exam_type():
    exam = {
        "_id": ObjectId(),
        "title": "Exam 2",
        "description": "Description",
        "subject": "Physics",
        "teacher_id": "t-2",
        "class_id": "c-2",
        "start_time": datetime.now(timezone.utc),
        "end_time": datetime.now(timezone.utc),
        "questions": [],
    }

    result = exam_helper(exam)

    assert result["exam_type"] == "15-minute quiz"
