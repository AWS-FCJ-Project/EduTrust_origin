from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status, Form
from src.auth.auth_utils import verify_password
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.auth.session_handler import clear_user_session, set_user_session
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserLogin, RefreshTokenRequest

router = APIRouter()


class SimpleLoginForm:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
    ):
        self.username = username
        self.password = password


@router.post("/login", summary="Login (Session)")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not db_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email first.",
        )

    await users_collection.update_one(
        {"email": user.email},
        {"$set": {"last_login": datetime.utcnow()}},
    )
    set_user_session(request, user.email)
    return {"message": "Login successful", "email": user.email}


@router.post("/token", summary="Get JWT Token (for Swagger testing)")
async def get_token(form_data: SimpleLoginForm = Depends()):
    db_user = await users_collection.find_one({"email": form_data.username})
    if not db_user or not verify_password(form_data.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not db_user.get("is_verified"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified.",
        )

    await users_collection.update_one(
        {"email": form_data.username},
        {"$set": {"last_login": datetime.utcnow()}},
    )

    return {
        "access_token": create_access_token(subject=form_data.username),
        "refresh_token": create_refresh_token(subject=form_data.username),
        "token_type": "bearer",
        "email": form_data.username,
    }


@router.post("/refresh", summary="Refresh Access Token")
@limiter.limit("10/minute")
async def refresh_token(request: Request, data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, refresh token required",
        )
    subject: str = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user information",
        )
    return {
        "access_token": create_access_token(subject=subject),
        "token_type": "bearer",
    }


@router.post("/logout", summary="Logout")
async def logout(request: Request):
    clear_user_session(request)
    return {"message": "Logged out successfully"}
