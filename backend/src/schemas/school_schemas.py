from typing import List, Optional

from pydantic import BaseModel, Field


class SubjectTeacher(BaseModel):
    """Schema for subject teacher."""

    teacher_id: str
    subject: str


class ClassCreate(BaseModel):
    """Schema for creating a new class."""

    name: str
    grade: int
    school_year: str
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: List[SubjectTeacher] = []
    status: str = "inactive"


class ClassUpdate(BaseModel):
    """Schema for updating a class."""

    name: Optional[str] = None
    grade: Optional[int] = None
    school_year: Optional[str] = None
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: Optional[List[SubjectTeacher]] = None
    status: Optional[str] = None


class ClassResponse(BaseModel):
    """Schema for class response."""

    id: str = Field(..., alias="_id")
    name: str
    grade: int
    school_year: str
    homeroom_teacher_id: Optional[str] = None
    subject_teachers: List[SubjectTeacher] = []
    student_count: int = 0
    status: str = "inactive"

    class Config:
        populate_by_name = True


class ClassCreateResponse(BaseModel):
    """Response schema for class creation."""

    id: str
    message: str = "Class created successfully"


class ClassUpdateResponse(BaseModel):
    """Response schema for class update."""

    message: str = "Class updated successfully"


class ClassDeleteResponse(BaseModel):
    """Response schema for class deletion."""

    message: str = "Class deleted successfully"


class StudentResponse(BaseModel):
    """Schema for student response."""

    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    role: str
    class_name: Optional[str] = None
    grade: Optional[int] = None


class AddStudentResponse(BaseModel):
    """Response schema for adding student to class."""

    message: str = "Student added to class"


class RemoveStudentResponse(BaseModel):
    """Response schema for removing student from class."""

    message: str = "Student removed from class"
