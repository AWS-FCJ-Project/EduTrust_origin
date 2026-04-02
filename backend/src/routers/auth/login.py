from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from src.auth.auth_utils import hash_password, verify_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.database import classes_collection, users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import (
    UserInfoResponse,
    UserLogin,
    UserRole,
    UserUpdate,
    user_helper,
)

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
    del request
    db_user = await users_collection.find_one({"email": user.email})
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
        await users_collection.update_one(
            {"email": user.email},
            {"$set": update_fields},
        )
        auth_result = cognito_auth_service.authenticate_user(user.email, user.password)
    else:
        cognito_auth_service.sync_user_group(user.email, db_user.get("role"))
        update_fields = {"last_login": datetime.now(timezone.utc)}
        cognito_user = cognito_auth_service.get_user(user.email)
        if cognito_user and cognito_user.get("sub"):
            update_fields["cognito_sub"] = cognito_user["sub"]
        await users_collection.update_one(
            {"email": user.email},
            {"$set": update_fields},
        )

    id_token = auth_result.get("IdToken")
    if not id_token:
        raise HTTPException(
            status_code=500,
            detail="Cognito did not return an ID token",
        )

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
async def list_students(user: dict = Depends(get_current_user_from_token)):
    if user["role"] not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    students = []
    async for s in users_collection.find({"role": UserRole.student.value}):
        students.append(user_helper(s))
    return students


@router.patch("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user_from_token),
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can update users")

    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID")

    target_user = await users_collection.find_one({"_id": ObjectId(user_id)})
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

    if "email" in update_dict and update_dict["email"] != target_user["email"]:
        raise HTTPException(
            status_code=400,
            detail="Updating email is not supported while Cognito auth is enabled.",
        )

    if "password" in update_dict:
        new_password = update_dict.pop("password")
        cognito_auth_service.set_user_password(target_user["email"], new_password)
        update_dict["hashed_password"] = hash_password(new_password)

    if not update_dict:
        return {"message": "No changes provided"}

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

    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_dict},
    )

    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str, current_user: dict = Depends(get_current_user_from_token)
):
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

    cognito_auth_service.delete_user(target_user["email"])
    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}


@router.post("/logout")
async def logout():
    """Logout user (client-side handles token removal)"""
    return {"message": "Client should remove the token to logout"}


@router.get("/users/teachers", response_model=list[dict])
async def list_teachers(current_user: dict = Depends(get_current_user_from_token)):
    if current_user.get("role") not in ["admin", "teacher"]:
        raise HTTPException(status_code=403, detail="Permission denied")

    teachers = []
    async for t in users_collection.find({"role": "teacher"}):
        t_id = str(t["_id"])
        assigned_classes = []

        async for c in classes_collection.find({"homeroom_teacher_id": t_id}):
            assigned_classes.append(
                {
                    "id": str(c["_id"]),
                    "name": c["name"],
                    "role": "Giáo viên Chủ nhiệm",
                }
            )

        async for c in classes_collection.find({"subject_teachers.teacher_id": t_id}):
            for st in c.get("subject_teachers", []):
                if st["teacher_id"] == t_id:
                    assigned_classes.append(
                        {
                            "id": str(c["_id"]),
                            "name": c["name"],
                            "role": f"Giáo viên Bộ môn ({st.get('subject', 'N/A')})",
                        }
                    )

        teachers.append(
            {
                "id": t_id,
                "name": t.get("name"),
                "email": t["email"],
                "subjects": t.get("subjects", []),
                "assigned_classes": assigned_classes,
                "is_assigned": len(assigned_classes) > 0,
            }
        )
    return teachers


@router.get("/users/admins", response_model=list[dict])
async def list_admins(current_user: dict = Depends(get_current_user_from_token)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Permission denied")

    admins = []
    async for a in users_collection.find({"role": "admin"}):
        admins.append(
            {
                "id": str(a["_id"]),
                "name": a.get("name"),
                "email": a["email"],
            }
        )
    return admins
