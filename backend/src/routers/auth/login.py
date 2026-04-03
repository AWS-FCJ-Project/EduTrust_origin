from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import delete, select, update
from src.auth.auth_utils import hash_password, verify_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.deps import get_db_session
from src.extensions import limiter
from src.models import Class, ClassSubjectTeacher, User
from src.schemas.auth_schemas import (
    UserInfoResponse,
    UserLogin,
    UserRole,
    UserUpdate,
    user_helper,
)

router = APIRouter()


def _user_row_to_dict(user: User) -> dict:
    return {
        "_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "class_name": user.class_name,
        "grade": user.grade,
        "subjects": list(user.subjects or []),
        "is_verified": bool(user.is_verified),
        "created_at": user.created_at,
        "last_login": user.last_login,
        "cognito_sub": user.cognito_sub,
    }


@router.post(
    "/login",
    responses={
        401: {"description": "Invalid credentials"},
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin, session=Depends(get_db_session)):
    del request
    result = await session.execute(select(User).where(User.email == user.email))
    db_user = result.scalar_one_or_none()
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    try:
        auth_result = cognito_auth_service.authenticate_user(user.email, user.password)
    except CognitoAuthError as error:
        hashed_password = db_user.hashed_password
        can_migrate = bool(hashed_password and verify_password(user.password, hashed_password))
        if not can_migrate:
            raise HTTPException(status_code=error.status_code, detail=error.message)

        cognito_user = cognito_auth_service.ensure_user(
            user.email,
            user.password,
            name=db_user.name,
            role=db_user.role,
            email_verified=bool(db_user.is_verified),
        )
        update_fields = {"last_login": datetime.now(timezone.utc)}
        if cognito_user.get("sub"):
            update_fields["cognito_sub"] = cognito_user["sub"]
        await session.execute(update(User).where(User.email == user.email).values(**update_fields))
        auth_result = cognito_auth_service.authenticate_user(user.email, user.password)
    else:
        cognito_auth_service.sync_user_group(user.email, db_user.role)
        update_fields = {"last_login": datetime.now(timezone.utc)}
        cognito_user = cognito_auth_service.get_user(user.email)
        if cognito_user and cognito_user.get("sub"):
            update_fields["cognito_sub"] = cognito_user["sub"]
        await session.execute(update(User).where(User.email == user.email).values(**update_fields))

    id_token = auth_result.get("IdToken")
    if not id_token:
        raise HTTPException(status_code=500, detail="Cognito did not return an ID token")

    return {
        "access_token": id_token,
        "id_token": id_token,
        "provider_access_token": auth_result.get("AccessToken"),
        "refresh_token": auth_result.get("RefreshToken"),
        "expires_in": auth_result.get("ExpiresIn"),
        "token_type": "bearer",
        "email": user.email,
    }


@router.get(
    "/user-info",
    response_model=UserInfoResponse,
    responses={
        401: {"description": "Invalid or expired token"},
        404: {"description": "User not found"},
    },
)
async def get_user_info(user: dict = Depends(get_current_user_from_token)):
    return user_helper(user)


@router.get("/users/students", response_model=list[dict])
async def list_students(
    user: dict = Depends(get_current_user_from_token),
    session=Depends(get_db_session),
):
    if user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await session.execute(select(User).where(User.role == UserRole.student.value))
    return [user_helper(_user_row_to_dict(s)) for s in result.scalars().all()]


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user_from_token),
    session=Depends(get_db_session),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
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

    if "email" in update_dict and update_dict["email"] != target_user.email:
        raise HTTPException(
            status_code=400,
            detail="Updating email is not supported while Cognito auth is enabled.",
        )

    if "password" in update_dict:
        new_password = update_dict.pop("password")
        cognito_auth_service.set_user_password(target_user.email, new_password)
        update_dict["hashed_password"] = hash_password(new_password)

    if not update_dict:
        return {"message": "No changes provided"}

    if "class_name" in update_dict and "grade" in update_dict:
        existing_class = await session.execute(
            select(Class).where(
                Class.name == update_dict["class_name"], Class.grade == update_dict["grade"]
            )
        )
        if existing_class.scalar_one_or_none() is None:
            session.add(
                Class(
                    name=update_dict["class_name"],
                    grade=update_dict["grade"],
                    school_year="2026-2027",
                    homeroom_teacher_id=None,
                    status="inactive",
                )
            )

    await session.execute(update(User).where(User.id == user_id).values(**update_dict))
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user_from_token),
    session=Depends(get_db_session),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete users")

    result = await session.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if target_user.role == "teacher":
        await session.execute(
            update(Class)
            .where(Class.homeroom_teacher_id == user_id)
            .values(homeroom_teacher_id=None, status="inactive")
        )
        await session.execute(delete(ClassSubjectTeacher).where(ClassSubjectTeacher.teacher_id == user_id))

    cognito_auth_service.delete_user(target_user.email)
    await session.execute(delete(User).where(User.id == user_id))
    return {"message": "User deleted successfully"}


@router.post("/logout")
async def logout():
    return {"message": "Client should remove the token to logout"}


@router.get("/users/teachers", response_model=list[dict])
async def list_teachers(
    current_user: dict = Depends(get_current_user_from_token),
    session=Depends(get_db_session),
):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await session.execute(select(User).where(User.role == "teacher"))
    teachers = result.scalars().all()
    payload: list[dict] = []

    for t in teachers:
        t_id = str(t.id)
        assigned_classes: list[dict] = []

        hr = await session.execute(select(Class).where(Class.homeroom_teacher_id == t_id))
        for c in hr.scalars().all():
            assigned_classes.append(
                {"id": str(c.id), "name": c.name, "role": "Giáo viên Chủ nhiệm"}
            )

        st = await session.execute(
            select(Class, ClassSubjectTeacher)
            .join(ClassSubjectTeacher, ClassSubjectTeacher.class_id == Class.id)
            .where(ClassSubjectTeacher.teacher_id == t_id)
        )
        for c, st_row in st.all():
            assigned_classes.append(
                {
                    "id": str(c.id),
                    "name": c.name,
                    "role": f"Giáo viên Bộ môn ({st_row.subject})",
                }
            )

        payload.append(
            {
                "id": t_id,
                "name": t.name,
                "email": t.email,
                "subjects": list(t.subjects or []),
                "assigned_classes": assigned_classes,
                "is_assigned": len(assigned_classes) > 0,
            }
        )

    return payload


@router.get("/users/admins", response_model=list[dict])
async def list_admins(
    current_user: dict = Depends(get_current_user_from_token),
    session=Depends(get_db_session),
):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    result = await session.execute(select(User).where(User.role == "admin"))
    return [{"id": str(a.id), "name": a.name, "email": a.email} for a in result.scalars().all()]

