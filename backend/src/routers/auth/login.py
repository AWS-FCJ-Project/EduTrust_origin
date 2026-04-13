from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from src.auth.auth_utils import hash_password, verify_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.extensions import limiter
from src.schemas.auth_schemas import (
    AdminResponse,
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
from src.utils.s3_utils import get_s3_handler

router = APIRouter()


@router.post(
    "/login",
    responses={
        401: {"description": "Invalid credentials"},
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    persistence = request.app.state.persistence
    db_user = await persistence.users.get_by_email(user.email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        auth_result = cognito_auth_service.authenticate_user(user.email, user.password)
    except CognitoAuthError as error:
        hashed_password = db_user.get("hashed_password")
        can_migrate = bool(
            hashed_password and verify_password(user.password, hashed_password)
        )
        if not can_migrate:
            raise HTTPException(status_code=error.status_code, detail=error.message)

        cognito_user = cognito_auth_service.ensure_user(
            user.email,
            user.password,
            name=db_user.get("name"),
            role=db_user.get("role"),
            email_verified=bool(db_user.get("is_verified", True)),
        )
        update_fields = {"last_login": datetime.now(timezone.utc)}
        if cognito_user.get("sub"):
            update_fields["cognito_sub"] = cognito_user["sub"]
        user_id = str(db_user.get("user_id") or db_user.get("_id") or "")
        await persistence.users.update(user_id, update_fields)
        auth_result = cognito_auth_service.authenticate_user(user.email, user.password)
    else:
        cognito_auth_service.sync_user_group(user.email, db_user.get("role"))
        update_fields = {"last_login": datetime.now(timezone.utc)}
        cognito_user = cognito_auth_service.get_user(user.email)
        if cognito_user and cognito_user.get("sub"):
            update_fields["cognito_sub"] = cognito_user["sub"]
        user_id = str(db_user.get("user_id") or db_user.get("_id") or "")
        await persistence.users.update(user_id, update_fields)

    id_token = auth_result.get("IdToken")
    if not id_token:
        raise HTTPException(
            status_code=500,
            detail="Cognito did not return an ID token",
        )

    return {
        # Only return what the frontend needs for authenticated API calls.
        # Refresh/access tokens are intentionally not exposed to the browser.
        "id_token": id_token,
        "expires_in": auth_result.get("ExpiresIn"),
        "token_type": "bearer",
    }


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
    return UserInfoResponse(**user_helper(user))


@router.get("/users/students", response_model=List[StudentResponse])
async def list_students(
    request: Request,
    user: dict = Depends(get_current_user_from_token),
) -> List[StudentResponse]:
    if user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    persistence = request.app.state.persistence
    students_docs = await persistence.users.list_by_role(UserRole.student.value)
    return [StudentResponse(**user_helper(s)) for s in students_docs]


@router.patch("/users/{user_id}", response_model=UpdateUserResponse)
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> UpdateUserResponse:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")

    persistence = request.app.state.persistence
    target_user = await persistence.users.get_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    update_dict = {
        k: v
        for k, v in update_data.model_dump().items()
        if v is not None
        and str(v).strip() != ""
        and str(v).lower() != "string"
        and not (k == "grade" and v == 0)
    }

    if "email" in update_dict and update_dict["email"] != target_user.get("email"):
        raise HTTPException(
            status_code=400,
            detail="Updating email is not supported while Cognito auth is enabled.",
        )

    if "password" in update_dict:
        new_password = update_dict.pop("password")
        cognito_auth_service.set_user_password(target_user["email"], new_password)
        update_dict["hashed_password"] = hash_password(new_password)

    if "role" in update_dict:
        cognito_auth_service.sync_user_group(
            target_user["email"],
            str(update_dict["role"]),
            current_group=str(target_user.get("role") or ""),
        )

    if not update_dict:
        return UpdateUserResponse(message="No changes provided")

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

    ok = await persistence.users.update(user_id, update_dict)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")

    return UpdateUserResponse(message="User updated successfully")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> MessageResponse:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    if not user_id or not user_id.strip():
        raise HTTPException(status_code=400, detail="Invalid user ID")

    persistence = request.app.state.persistence
    target_user = await persistence.users.get_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.get("role") == "teacher":
        await persistence.classes.clear_homeroom_teacher(user_id)
        await persistence.classes.pull_subject_teacher(user_id)

    cognito_auth_service.delete_user(target_user["email"])
    await persistence.users.delete(user_id)
    return MessageResponse(message="User deleted successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout() -> MessageResponse:
    return MessageResponse(message="Client should remove the token to logout")


@router.get("/users/teachers", response_model=List[TeacherResponse])
async def list_teachers(
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
) -> List[TeacherResponse]:
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
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can view admin list")

    persistence = request.app.state.persistence
    admins_docs = await persistence.users.list_by_role("admin")
    return [
        AdminResponse(
            id=str(a["_id"]),
            name=a.get("name"),
            email=a["email"],
        )
        for a in admins_docs
    ]


class AvatarUploadResponse(BaseModel):
    """Schema for avatar upload URL response."""

    upload_url: str
    s3_key: str
    avatar_url: str


@router.get(
    "/user/avatar-upload-url",
    responses={
        401: {"description": "Invalid or expired token"},
    },
)
async def get_avatar_upload_url(
    user: dict = Depends(get_current_user_from_token),
) -> AvatarUploadResponse:
    """Generate a presigned S3 URL for the current user to upload their avatar."""
    user_id = str(user.get("_id") or user.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    s3_key = f"avatars/{user_id}.jpg"
    s3 = get_s3_handler()
    upload_url = s3.get_presigned_upload_url(
        s3_key, content_type="image/jpeg", expiration=3600
    )
    avatar_url = s3.get_presigned_url(s3_key, expiration=3600)

    if not upload_url or not avatar_url:
        raise HTTPException(status_code=500, detail="Failed to generate upload URL")

    return AvatarUploadResponse(
        upload_url=upload_url, s3_key=s3_key, avatar_url=avatar_url
    )


class AvatarUpdateRequest(BaseModel):
    s3_key: str


@router.post(
    "/user/avatar",
    responses={
        401: {"description": "Invalid or expired token"},
        404: {"description": "User not found"},
    },
)
async def update_user_avatar(
    body: AvatarUpdateRequest,
    request: Request,
    current_user: dict = Depends(get_current_user_from_token),
):
    """Save the S3 key as the user's avatar URL in DynamoDB."""
    persistence = request.app.state.persistence
    user_id = str(current_user.get("_id") or current_user.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user")

    s3 = get_s3_handler()
    avatar_url = s3.get_presigned_url(body.s3_key, expiration=3600)
    if not avatar_url:
        raise HTTPException(status_code=500, detail="Failed to generate avatar URL")

    ok = await persistence.users.update(user_id, {"avatar": avatar_url})
    if not ok:
        raise HTTPException(status_code=404, detail="User not found")

    return {"avatar_url": avatar_url}
