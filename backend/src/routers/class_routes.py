from typing import Annotated, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
from src.database import classes_collection
from src.database.class_handler import ClassHandler
from src.schemas.school_schemas import ClassCreate, ClassUpdate

router = APIRouter(prefix="/classes", tags=["Classes"])


def get_class_handler(request: Request) -> ClassHandler:
    return request.app.state.class_handler


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_class(
    class_data: ClassCreate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create classes")

    class_id = handler.create_class(class_data.model_dump())
    return {"id": class_id, "message": "Class created successfully"}


@router.get("", response_model=List[dict])
def get_classes(
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
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
    user_id = str(current_user["_id"])
    class_obj = handler.collection.find_one({"homeroom_teacher_id": user_id})
    if not class_obj:
        return []
    class_id = str(class_obj["_id"])
    return handler.get_violations(class_id)


@router.get("/{class_id}", response_model=dict)
def get_class(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    class_obj = handler.get_class_by_id(class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return class_obj


@router.patch("/{class_id}")
def update_class(
    class_id: str,
    class_data: ClassUpdate,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    success = handler.update_class(class_id, class_data.model_dump())
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class updated successfully"}


@router.get("/{class_id}/students", response_model=List[dict])
def get_class_students(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    return handler.get_students(class_id)


@router.get("/students/available", response_model=List[dict])
def get_available_students(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")
    return handler.get_available_students(class_id)


@router.post("/{class_id}/students/{student_id}")
def add_student_to_class(
    class_id: str,
    student_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    success = handler.add_student(class_id, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student or class not found")
    return {"message": "Student added to class"}


@router.delete("/{class_id}/students/{student_id}")
def remove_student_from_class(
    class_id: str,
    student_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove students")

    if not ObjectId.is_valid(class_id) or not ObjectId.is_valid(student_id):
        raise HTTPException(status_code=400, detail="Invalid IDs")

    success = handler.remove_student(class_id, student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student removed from class"}


@router.delete("/{class_id}")
def delete_class(
    class_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    handler: Annotated[ClassHandler, Depends(get_class_handler)],
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")

    if not ObjectId.is_valid(class_id):
        raise HTTPException(status_code=400, detail="Invalid class ID")

    success = handler.delete_class(class_id)
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return {"message": "Class deleted successfully"}
