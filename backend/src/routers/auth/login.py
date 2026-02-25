from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Request, status
from src.auth.auth_utils import verify_password
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserLogin

router = APIRouter()


@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    """Authenticate user and return JWT access + refresh tokens."""
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    if not db_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )

    await users_collection.update_one(
        {"email": user.email}, {"$set": {"last_login": datetime.utcnow()}}
    )

    return {
        "access_token": create_access_token(user.email),
        "refresh_token": create_refresh_token(user.email),
        "token_type": "bearer",
        "email": user.email,
    }


@router.post("/refresh")
async def refresh(refresh_token: str = Body(..., embed=True)):
    """Issue a new access token given a valid refresh token."""
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )
    return {
        "access_token": create_access_token(payload.get("sub", "")),
        "token_type": "bearer",
    }


@router.post("/logout")
async def logout():
    """Stateless logout — client must discard tokens on their end."""
    return {"message": "Logged out successfully."}
