from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.auth_utils import verify_password
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.auth.jwt_handler import create_access_token
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
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    await users_collection.update_one(
        {"email": user.email}, {"$set": {"last_login": datetime.now(timezone.utc)}}
    )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer", "email": user.email}


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
        update_dict["password_plain"] = new_password

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

    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)}, {"$set": update_dict}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

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

    await users_collection.delete_one({"_id": ObjectId(user_id)})
    return {"message": "User deleted successfully"}


@router.post("/logout")
async def logout():
    """Logout user (client-side handles token removal)"""
    return {"message": "Client should remove the token to logout"}
