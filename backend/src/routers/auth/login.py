from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from src.auth.auth_utils import verify_password
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.auth.jwt_handler import create_access_token
from src.extensions import limiter
from src.schemas.auth_schemas import (
    AdminResponse,
    LoginResponse,
    MessageResponse,
    StudentResponse,
    TeacherClassAssignment,
    TeacherResponse,
    UpdateUserResponse,
    UserInfoResponse,
    UserLogin,
    UserRole,
    UserUpdate,
    user_helper,
)

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"description": "Invalid credentials"},
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin) -> LoginResponse:
    """Authenticate user and return access token."""
    persistence = request.app.state.persistence
    db_user = await persistence.users.get_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await persistence.users.update_last_login(user.email)

    access_token = create_access_token(data={"sub": user.email})

    return LoginResponse(
        access_token=access_token, token_type="bearer", email=user.email
    )


@router.get(
    "/user-info",
    response_model=UserInfoResponse,
    responses={
        401: {"description": "Invalid or expired token"},
        404: {"description": "User not found"},
    },
)
async def get_user_info(
    user: dict = Depends(get_current_user_from_token),
) -> UserInfoResponse:
    """Get current user info."""
    return UserInfoResponse(**user_helper(user))


@router.get("/users/students", response_model=List[StudentResponse])
async def list_students(
    request: Request,
    user: dict = Depends(get_current_user_from_token),
) -> List[StudentResponse]:
    """List all students (admin/teacher only)."""
    if user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    persistence = request.app.state.persistence
    students_docs = await persistence.users.list_by_role(UserRole.student.value)
    students = [StudentResponse(**user_helper(s)) for s in students_docs]
    return students


@router.patch("/users/{user_id}", response_model=UpdateUserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> UpdateUserResponse:
    """Update user info (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")

    update_dict = {
        k: v
        for k, v in update_data.model_dump().items()
        if v is not None
        and str(v).strip() != ""
        and str(v).lower() != "string"
        and not (k == "grade" and v == 0)
    }

    if "password" in update_dict:
        new_password = update_dict.pop("password")
        from src.auth.auth_utils import hash_password

        update_dict["hashed_password"] = hash_password(new_password)

    if not update_dict:
        return UpdateUserResponse(message="No changes provided")

    persistence = request.app.state.persistence
    if "class_name" in update_dict and "grade" in update_dict:
        existing_class = await persistence.classes.get_by_name_grade(
            update_dict["class_name"], update_dict["grade"]
        )
        if not existing_class:
            await persistence.classes.insert_one(
                {
                    "name": update_dict["class_name"],
                    "grade": update_dict["grade"],
                    "school_year": "2026-2027",
                    "homeroom_teacher_id": None,
                    "subject_teachers": [],
                    "status": "inactive",
                }
            )

    result = await persistence.users.update(user_id, update_dict)

    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    return UpdateUserResponse(message="User updated successfully")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> MessageResponse:
    """Delete user (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")

    persistence = request.app.state.persistence
    target_user = await persistence.users.get_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user["role"] == "teacher":
        await persistence.classes.clear_homeroom_teacher(user_id)
        await persistence.classes.pull_subject_teacher(user_id)

    await persistence.users.delete(user_id)
    return MessageResponse(message="User deleted successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    """Logout user (client-side handles token removal)."""
    return MessageResponse(message="Client should remove the token to logout")


@router.get("/users/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> List[TeacherResponse]:
    """List all teachers with their assigned classes."""
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    persistence = request.app.state.persistence
    teachers_docs = await persistence.users.list_by_role("teacher")
    teachers = []
    for t in teachers_docs:
        t_id = str(t["_id"])
        assigned_classes = []

        homeroom_classes = await persistence.classes.list_by_homeroom_teacher(t_id)
        for c in homeroom_classes:
            assigned_classes.append(
                TeacherClassAssignment(
                    id=str(c["_id"]), name=c["name"], role="Homeroom Teacher"
                )
            )

        all_classes = await persistence.classes.list_all()
        for c in all_classes:
            for st in c.get("subject_teachers", []):
                if st["teacher_id"] == t_id:
                    assigned_classes.append(
                        TeacherClassAssignment(
                            id=str(c["_id"]),
                            name=c["name"],
                            role=f"Subject Teacher ({st.get('subject', 'N/A')})",
                        )
                    )

        teachers.append(
            TeacherResponse(
                id=t_id,
                name=t.get("name"),
                email=t["email"],
                subjects=t.get("subjects", []),
                assigned_classes=assigned_classes,
                is_assigned=len(assigned_classes) > 0,
            )
        )
    return teachers


@router.get("/users/admins", response_model=List[AdminResponse])
async def list_admins(
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> List[AdminResponse]:
    """List all admins (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    persistence = request.app.state.persistence
    admins_docs = await persistence.users.list_by_role("admin")
    admins = [
        AdminResponse(
            id=str(a["_id"]),
            name=a.get("name"),
            email=a["email"],
        )
        for a in admins_docs
    ]
    return admins
