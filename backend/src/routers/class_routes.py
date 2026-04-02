from typing import Annotated, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
from src.database import classes_collection
from src.database.class_handler import ClassHandler
from src.schemas.school_schemas import (
    AddStudentResponse,
    ClassCreate,
    ClassCreateResponse,
    ClassDeleteResponse,
    ClassResponse,
    ClassUpdate,
    ClassUpdateResponse,
    RemoveStudentResponse,
    StudentResponse,
)

router = APIRouter(prefix="/classes", tags=["Classes"])


def get_class_handler(request: Request) -> ClassHandler:
    """Get ClassHandler from app state."""
    return request.app.state.class_handler


@router.post(
    "", response_model=ClassCreateResponse, status_code=status.HTTP_201_CREATED
)
def create_class(
    class_data: ClassCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> ClassCreateResponse:
    """Create a new class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create classes")

    class_id = handler.create_class(class_data.model_dump())
    return ClassCreateResponse(id=class_id, message="Class created successfully")


@router.get("", response_model=List[dict])
def get_classes(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    """Get classes filtered by user role (admin: all, teacher: assigned, student: enrolled)."""
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    if role == "admin":
        return handler.get_all_classes()
    elif role == "teacher":
        return handler.get_classes_for_teacher(user_id)
    elif role == "student":
        user_class = current_user.get("class_name")
        user_grade = current_user.get("grade")
        if not user_class or not user_grade:
            return []
        return handler.get_classes_for_student(user_class, user_grade)
    else:
        raise HTTPException(status_code=403, detail="Invalid role")


@router.get("/homeroom/violations", response_model=List[dict])
def get_homeroom_violations(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    """Get violations for homeroom teacher's class."""
    user_id = str(current_user["_id"])
    class_obj = handler.collection.find_one({"homeroom_teacher_id": user_id})
    if not class_obj:
        return []
    class_id = str(class_obj["_id"])
    return handler.get_violations(class_id)


@router.get("/{class_id}", response_model=ClassResponse)
def get_class(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> ClassResponse:
    """Get class details by ID."""
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    class_obj = handler.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassResponse(**class_obj)


@router.patch("/{class_id}", response_model=ClassUpdateResponse)
def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> ClassUpdateResponse:
    """Update class info (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    success = handler.update_class(class_id, class_data.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassUpdateResponse(message="Class updated successfully")


@router.get("/{class_id}/students", response_model=List[StudentResponse])
def get_class_students(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> List[StudentResponse]:
    """Get students in a class."""
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    students = handler.get_students(class_id)
    return [StudentResponse(**s) for s in students]


@router.get("/students/available", response_model=List[StudentResponse])
def get_available_students(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> List[StudentResponse]:
    """Get students not yet assigned to this class."""
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    students = handler.get_available_students(class_id)
    return [StudentResponse(**s) for s in students]


@router.post("/{class_id}/students/{student_id}", response_model=AddStudentResponse)
def add_student_to_class(
    class_id: str,
    student_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> AddStudentResponse:
    """Add a student to a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    success = handler.add_student(class_id, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student or class not found")
    return AddStudentResponse(message="Student added to class")


@router.delete(
    "/{class_id}/students/{student_id}", response_model=RemoveStudentResponse
)
def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> RemoveStudentResponse:
    """Remove a student from a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    success = handler.remove_student(class_id, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return RemoveStudentResponse(message="Student removed from class")


@router.delete("/{class_id}", response_model=ClassDeleteResponse)
def delete_class(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
) -> ClassDeleteResponse:
    """Delete a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    success = handler.delete_class(class_id)
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassDeleteResponse(message="Class deleted successfully")
