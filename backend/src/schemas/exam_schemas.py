from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ExamStatus(str, Enum):
    """Enum for exam submission status."""

    completed = "completed"
    failed = "failed"


class LockReason(str, Enum):
    """Enum for exam lock reasons."""

    disqualified = "disqualified"
    submitted = "submitted"
    not_started = "not_started"
    expired = "expired"


class ExamType(str, Enum):
    """Enum for exam types."""

    quiz_15_min = "15-minute quiz"
    quiz_45_min = "45-minute exam"
    final_exam = "final exam"


class Question(BaseModel):
    """Schema for exam question."""

    question_text: str
    options: List[str]
    correct: Any  # index of correct option


class ExamCreate(BaseModel):
    """Schema for creating a new exam."""

    title: str
    description: Optional[str] = None
    subject: str
    class_id: str
    start_time: datetime
    end_time: datetime
    duration: int = 60  # minutes
    exam_type: ExamType = ExamType.quiz_15_min
    secret_key: Optional[str] = None
    questions: List[Dict[str, Any]] = []


class ExamUpdate(BaseModel):
    """Schema for updating an exam."""

    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    exam_type: Optional[ExamType] = None
    secret_key: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None


class ExamSubmission(BaseModel):
    """Schema for student exam submission (input)."""

    answers: Dict[str, Any]  # {question_index: selected_option_index}
    violation_count: int = 0
    status: ExamStatus = ExamStatus.completed


class ExamKeyVerify(BaseModel):
    """Schema for verifying exam key."""

    key: str


class ExamResponse(BaseModel):
    """Schema for full exam response."""

    id: str = Field(..., alias="_id")
    title: str
    description: Optional[str] = None
    subject: str
    exam_type: ExamType = ExamType.quiz_15_min
    teacher_id: str
    class_id: str
    start_time: datetime
    end_time: datetime
    duration: int = 60
    has_secret_key: bool = False
    secret_key: Optional[str] = None
    questions: List[Dict[str, Any]] = []

    class Config:
        populate_by_name = True


class ExamStatusResponse(BaseModel):
    """Schema for exam status response."""

    is_submitted: bool
    status: Optional[ExamStatus] = None
    submitted_at: Optional[datetime] = None
    violation_count: int = 0


class ExamSubmissionResponse(BaseModel):
    """Schema for exam submission response (output with full details)."""

    exam_id: str
    student_id: str
    submitted_at: datetime
    score: float
    correct_count: int
    total_questions: int
    status: ExamStatus
    violation_count: int = 0


class ExamAccessResponse(BaseModel):
    """Schema for exam access response (includes lock info for students)."""

    id: str
    title: str
    subject: str
    is_locked: bool = False
    lock_reason: Optional[LockReason] = None
    submission_status: Optional[ExamStatus] = None
    violation_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExamSubmissionSummary(BaseModel):
    """Schema for exam submission summary (teacher/admin view)."""

    student_id: str
    student_name: str
    score: float
    violation_count: int
    status: ExamStatus
    submitted_at: Optional[datetime] = None


class ExamResultSummary(BaseModel):
    """Schema for exam result summary."""

    exam_id: str
    exam_title: str
    subject: str
    score: float
    correct_count: int
    total_questions: int
    status: Optional[ExamStatus] = None
    submitted_at: Optional[datetime] = None


class ExamResultSummaryList(BaseModel):
    """Schema for exam result summary list response (for get_all_results_summary)."""

    id: str
    title: str
    subject: str
    class_id: Optional[str] = None
    class_name: str = "N/A"
    grade: Optional[str] = None
    total_submissions: int = 0
    average_score: float = 0
    highest_score: float = 0
    violations_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ExamViolation(BaseModel):
    """Schema for exam violation."""

    id: str
    student_id: str
    student_name: str = "Unknown student"
    student_class: str = "N/A"
    exam_id: str
    exam_title: str = "Unknown Exam"
    exam_start: Optional[datetime] = None
    exam_end: Optional[datetime] = None
    class_id: str
    subject: str = "N/A"
    violation_type: str
    violation_time: datetime
    created_at: Optional[datetime] = None


class ExamCreateResponse(BaseModel):
    """Response schema for exam creation."""

    id: str
    secret_key: str
    message: str = "Exam created successfully"


class ExamVerifyKeyResponse(BaseModel):
    """Response schema for exam key verification."""

    valid: bool


class ExamUpdateResponse(BaseModel):
    """Response schema for exam update."""

    message: str = "Exam updated successfully"


class ExamDeleteResponse(BaseModel):
    """Response schema for exam deletion."""

    message: str = "Exam deleted successfully"


class ExamSecretKeyResponse(BaseModel):
    """Response schema for getting exam secret key."""

    secret_key: Optional[str] = None


class ExamRegenerateKeyResponse(BaseModel):
    """Response schema for regenerating exam key."""

    secret_key: str
    message: str = "Secret key regenerated successfully"


class ExamSubmitAlreadyResponse(BaseModel):
    """Response schema when exam already submitted."""

    message: str = "Exam already submitted"
    already_submitted: bool = True


def exam_helper(exam_document: dict, include_secret: bool = False) -> dict:
    """Format exam document for API response."""
    result = {
        "id": str(exam_document["_id"]),
        "title": exam_document["title"],
        "description": exam_document.get("description"),
        "subject": exam_document["subject"],
        "exam_type": exam_document.get("exam_type", "15-minute quiz"),
        "teacher_id": exam_document["teacher_id"],
        "class_id": exam_document["class_id"],
        "start_time": exam_document["start_time"],
        "end_time": exam_document["end_time"],
        "duration": exam_document.get("duration", 60),
        "has_secret_key": bool(exam_document.get("secret_key")),
        "questions": exam_document.get("questions", []),
    }
    if include_secret:
        result["secret_key"] = exam_document.get("secret_key")
    return result
