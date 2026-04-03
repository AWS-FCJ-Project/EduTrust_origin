from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.dependencies import get_current_user
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


def get_persistence(request: Request):
    """Get persistence facade from app state."""
    return request.app.state.persistence


def class_response_helper(cls: dict) -> dict:
    """Format class document for API response."""
    student_count = cls.get("student_count", 0)
    return {
        "id": str(cls["_id"]) if "_id" in cls else cls.get("id"),
        "name": cls["name"],
        "grade": cls["grade"],
        "school_year": cls.get("school_year", ""),
        "homeroom_teacher_id": cls.get("homeroom_teacher_id"),
        "subject_teachers": cls.get("subject_teachers", []),
        "student_count": student_count,
        "status": cls.get("status", "inactive"),
    }


def user_helper(user: dict) -> dict:
    return {
        "id": str(user["_id"]) if "_id" in user else user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "class_name": user.get("class_name"),
        "grade": user.get("grade"),
    }


@router.post(
    "", response_model=ClassCreateResponse, status_code=status.HTTP_201_CREATED
)
async def create_class(
    class_data: ClassCreate,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ClassCreateResponse:
    """Create a new class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create classes")

    persistence = get_persistence(request)
    class_doc = class_data.model_dump()
    if class_doc.get("homeroom_teacher_id") and class_doc.get("subject_teachers"):
        class_doc["status"] = "active"
    else:
        class_doc["status"] = "inactive"

    class_id = await persistence.classes.insert_one(class_doc)
    id_str = str(class_id) if hasattr(class_id, "__str__") else class_id
    return ClassCreateResponse(id=id_str, message="Class created successfully")


@router.get("", response_model=List[dict])
async def get_classes(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get classes filtered by user role (admin: all, teacher: assigned, student: enrolled)."""
    persistence = get_persistence(request)
    role = current_user.get("role")
    user_id = str(current_user["_id"])

    if role == "admin":
        classes = await persistence.classes.list_all()
        return [class_response_helper(c) for c in classes]
    elif role == "teacher":
        classes = await persistence.classes.list_by_teacher(user_id)
        return [class_response_helper(c) for c in classes]
    elif role == "student":
        user_class = current_user.get("class_name")
        user_grade = current_user.get("grade")
        if not user_class or not user_grade:
            return []
        cls = await persistence.classes.get_by_name_grade(user_class, user_grade)
        if cls:
            return [class_response_helper(cls)]
        return []
    else:
        raise HTTPException(status_code=403, detail="Invalid role")


@router.get("/homeroom/violations", response_model=List[dict])
async def get_homeroom_violations(
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
):
    """Get violations for homeroom teacher's class."""
    persistence = get_persistence(request)
    user_id = str(current_user["_id"])
    class_obj = await persistence.classes.find_one({"homeroom_teacher_id": user_id})
    if not class_obj:
        return []
    class_id = str(class_obj["_id"])
    violations = await persistence.violations.list_by_class(class_id)
    return violations


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ClassResponse:
    """Get class details by ID."""
    if not class_id or not class_id.strip():
        raise HTTPException(status_code=400, detail="Invalid class ID")
    persistence = get_persistence(request)
    class_obj = await persistence.classes.get_by_id(class_id)
    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassResponse(**class_response_helper(class_obj))


@router.patch("/{class_id}", response_model=ClassUpdateResponse)
async def update_class(
    class_id: str,
    class_data: ClassUpdate,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ClassUpdateResponse:
    """Update class info (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update classes")

    if not class_id or not class_id.strip():
        raise HTTPException(status_code=400, detail="Invalid class ID")

    persistence = get_persistence(request)
    update_data = {
        k: v
        for k, v in class_data.model_dump().items()
        if v is not None
        and str(v).strip() != ""
        and str(v).lower() != "string"
        and not (k == "grade" and v == 0)
    }
    if not update_data:
        return ClassUpdateResponse(message="No changes provided")

    current = await persistence.classes.get_by_id(class_id)
    if not current:
        raise HTTPException(status_code=404, detail="Class not found")

    merged = {**current, **update_data}
    if merged.get("homeroom_teacher_id") and merged.get("subject_teachers"):
        update_data["status"] = "active"
    else:
        update_data["status"] = "inactive"

    success = await persistence.classes.update(class_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail="Class not found")
    return ClassUpdateResponse(message="Class updated successfully")


@router.get("/{class_id}/students", response_model=List[StudentResponse])
async def get_class_students(
    class_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[StudentResponse]:
    """Get students in a class."""
    if not class_id or not class_id.strip():
        raise HTTPException(status_code=400, detail="Invalid class ID")
    persistence = get_persistence(request)
    cls = await persistence.classes.get_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    students = await persistence.users.list_students_by_class(cls["name"], cls["grade"])
    return [StudentResponse(**user_helper(s)) for s in students]


@router.get("/students/available", response_model=List[StudentResponse])
async def get_available_students(
    class_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> List[StudentResponse]:
    """Get students not yet assigned to this class."""
    if not class_id or not class_id.strip():
        raise HTTPException(status_code=400, detail="Invalid class ID")
    persistence = get_persistence(request)
    cls = await persistence.classes.get_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    students = await persistence.users.list_available_students(
        cls["name"], cls["grade"]
    )
    return [StudentResponse(**user_helper(s)) for s in students]


@router.post("/{class_id}/students/{student_id}", response_model=AddStudentResponse)
async def add_student_to_class(
    class_id: str,
    student_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> AddStudentResponse:
    """Add a student to a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can assign students")

    if not class_id or not class_id.strip() or not student_id or not student_id.strip():
        raise HTTPException(status_code=400, detail="Invalid IDs")

    persistence = get_persistence(request)
    cls = await persistence.classes.get_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    success = await persistence.users.update(
        student_id,
        {"class_name": cls["name"], "grade": cls["grade"]},
    )
    if not success:
        raise HTTPException(status_code=404, detail="Student or class not found")
    return AddStudentResponse(message="Student added to class")


@router.delete(
    "/{class_id}/students/{student_id}", response_model=RemoveStudentResponse
)
async def remove_student_from_class(
    class_id: str,
    student_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> RemoveStudentResponse:
    """Remove a student from a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can remove students")

    if not class_id or not class_id.strip() or not student_id or not student_id.strip():
        raise HTTPException(status_code=400, detail="Invalid IDs")

    persistence = get_persistence(request)
    success = await persistence.users.update(
        student_id,
        {"class_name": None, "grade": None},
    )
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return RemoveStudentResponse(message="Student removed from class")


@router.delete("/{class_id}", response_model=ClassDeleteResponse)
async def delete_class(
    class_id: str,
    request: Request,
    current_user: Annotated[dict, Depends(get_current_user)],
) -> ClassDeleteResponse:
    """Delete a class (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete classes")

    if not class_id or not class_id.strip():
        raise HTTPException(status_code=400, detail="Invalid class ID")

    persistence = get_persistence(request)
    cls = await persistence.classes.get_by_id(class_id)
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    # Clear student associations
    await persistence.users.update_many(
        {"role": "student", "class_name": cls["name"], "grade": cls["grade"]},
        {"class_name": None, "grade": None},
    )

    await persistence.classes.delete(class_id)
    return ClassDeleteResponse(message="Class deleted successfully")
