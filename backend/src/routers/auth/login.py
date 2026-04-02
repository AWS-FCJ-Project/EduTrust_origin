from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from src.auth.auth_utils import verify_password
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.auth.jwt_handler import create_access_token
from src.database import classes_collection, users_collection
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
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await users_collection.update_one(
        {"email": user.email}, {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

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
    user: dict = Depends(get_current_user_from_token),
) -> List[StudentResponse]:
    """List all students (admin/teacher only)."""
    if user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    students = []
    async for s in users_collection.find({"role": UserRole.student.value}):
        students.append(StudentResponse(**user_helper(s)))
    return students


@router.patch("/users/{user_id}", response_model=UpdateUserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user_from_token),
) -> UpdateUserResponse:
    """Update user info (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    if not ObjectId.is_valid(user_id):
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

    if "class_name" in update_dict and "grade" in update_dict:
        existing_class = await classes_collection.find_one(
            {"name": update_dict["class_name"], "grade": update_dict["grade"]}
        )
        if not existing_class:
            await classes_collection.insert_one(
                {
                    "name": update_dict["class_name"],
                    "grade": update_dict["grade"],
                    "school_year": "2026-2027",
                    "homeroom_teacher_id": None,
                    "subject_teachers": [],
                    "status": "inactive",
                }
            )

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return UpdateUserResponse(message="User updated successfully")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str, current_user: dict = Depends(get_current_user_from_token)
) -> MessageResponse:
    """Delete user (admin only)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    target_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user["role"] == "teacher":
        await classes_collection.update_many(
            {"homeroom_teacher_id": user_id},
            {"$set": {"homeroom_teacher_id": None, "status": "inactive"}},
        )
        await classes_collection.update_many(
            {}, {"$pull": {"subject_teachers": {"teacher_id": user_id}}}
        )

    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return MessageResponse(message="User deleted successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    """Logout user (client-side handles token removal)."""
    return MessageResponse(message="Client should remove the token to logout")


@router.get("/users/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    current_user: dict = Depends(get_current_user_from_token),
) -> List[TeacherResponse]:
    """List all teachers with their assigned classes."""
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    teachers = []
    async for t in users_collection.find({"role": "teacher"}):
        t_id = str(t["_id"])
        assigned_classes = []

        async for c in classes_collection.find({"homeroom_teacher_id": t_id}):
            assigned_classes.append(
                TeacherClassAssignment(
                    id=str(c["_id"]), name=c["name"], role="Homeroom Teacher"
                )
            )

        async for c in classes_collection.find({"subject_teachers.teacher_id": t_id}):
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
    current_user: dict = Depends(get_current_user_from_token),
) -> List[AdminResponse]:
    """List all admins (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    admins = []
    async for a in users_collection.find({"role": "admin"}):
        admins.append(
            AdminResponse(
                id=str(a["_id"]),
                name=a.get("name"),
                email=a["email"],
            )
        )
    return admins
