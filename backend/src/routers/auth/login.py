from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.auth.auth_utils import verify_password
from src.auth.dependencies import get_current_user as get_current_user_from_token
from src.auth.jwt_handler import create_access_token
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserInfoResponse, UserLogin, user_helper

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
async def get_user_info(email: str = Depends(get_current_user_from_token)):
    db_user = await users_collection.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_helper(db_user)


@router.post("/logout")
async def logout():
    """Logout user (client-side handles token removal)"""
    return {"message": "Client should remove the token to logout"}
