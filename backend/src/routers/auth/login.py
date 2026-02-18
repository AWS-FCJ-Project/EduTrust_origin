from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from src.auth.auth_utils import verify_password
from src.auth.session_handler import clear_user_session, set_user_session
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserLogin

router = APIRouter()


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not db_user.get("is_verified"):
        raise HTTPException(
            status_code=403,
            detail="Email not verified. Please verify your email first.",
        )

    # Update last login
    await users_collection.update_one(
        {"email": user.email}, {"$set": {"last_login": datetime.utcnow()}}
    )

    # Create session (no JWT, no 2FA)
    set_user_session(request, user.email)

    return {"message": "Login successful", "email": user.email}


@router.post("/logout")
async def logout(request: Request):
    """Logout user by clearing session"""
    clear_user_session(request)
    return {"message": "Logged out successfully"}
