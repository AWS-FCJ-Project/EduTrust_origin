from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Form

from src.auth.auth_utils import verify_password
from src.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import RefreshTokenRequest

router = APIRouter()


class OAuth2LoginForm:
    def __init__(
        self,
        username: str = Form(...),
        password: str = Form(...),
    ):
        self.username = username
        self.password = password


@router.post("/token", summary="Login and get JWT")
@limiter.limit("5/minute")
async def login(form_data: OAuth2LoginForm = Depends()):
    db_user = await users_collection.find_one({"email": form_data.username})

    if not db_user or not verify_password(
        form_data.password, db_user["hashed_password"]
    ):
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
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )

    return {
        "access_token": create_access_token(subject=form_data.username),
        "refresh_token": create_refresh_token(subject=form_data.username),
        "token_type": "bearer",
    }


@router.post("/refresh", summary="Refresh Access Token")
async def refresh_token(data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {
        "access_token": create_access_token(subject=subject),
        "token_type": "bearer",
    }