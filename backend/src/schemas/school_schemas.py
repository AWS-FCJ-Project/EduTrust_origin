from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class SubjectTeacher(BaseModel):
    teacher_id: str
    subject: str


class ClassCreate(BaseModel):
    name: str
    grade: int
    school_year: str
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: List[SubjectTeacher] = []
    status: str = "inactive"


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[int] = None
    school_year: Optional[str] = None
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: Optional[List[SubjectTeacher]] = None
    status: Optional[str] = None


class ClassResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    grade: int
    school_year: str
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: List[SubjectTeacher] = []
    status: str = "inactive"

    class Config:
        populate_by_name = True


class ExamCreate(BaseModel):
    title: str
    description: Optional[str] = None
    subject: str
    class_id: str
    start_time: datetime
    end_time: datetime
    duration: int = 60  # Default to 60 minutes
    exam_type: str = "15-minute quiz"
    secret_key: Optional[str] = None
    questions: List[dict] = []  # Keeping it flexible for now


class ExamResponse(ExamCreate):
    id: str = Field(..., alias="_id")
    teacher_id: str

    class Config:
        populate_by_name = True


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    subject: Optional[str] = None
    class_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    exam_type: Optional[str] = None
    secret_key: Optional[str] = None
    questions: Optional[List[dict]] = None


class ExamSubmission(BaseModel):
    answers: dict  # {question_index: selected_option_index}
    violation_count: int = 0
    status: str = "completed"  # "completed" or "failed"


class ExamStatusResponse(BaseModel):
    is_submitted: bool
    status: Optional[str] = None  # "completed", "failed", or None
    submitted_at: Optional[datetime] = None
    violation_count: int = 0


class ExamKeyVerify(BaseModel):
    key: str
