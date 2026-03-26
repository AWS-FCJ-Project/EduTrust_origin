import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from src.auth.auth_utils import verify_password
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.database import refresh_tokens_collection, users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import RefreshTokenRequest, UserLogin

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
    refresh_token = create_refresh_token(data={"sub": user.email})

    hashed_rt = hashlib.sha256(refresh_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    await refresh_tokens_collection.insert_one(
        {
            "email": user.email,
            "hashed_token": hashed_rt,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc),
            "user_agent": request.headers.get("user-agent", ""),
            "ip": request.client.host if request.client else "127.0.0.1",
            "used": False,
            "revoked": False,
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": user.email,
        "role": db_user.get("role", "student"),
    }


@router.post("/refresh")
@limiter.limit("5/minute")
async def refresh_token(request: Request, body: RefreshTokenRequest):
    token = body.refresh_token
    if not token:
        raise HTTPException(status_code=400, detail="Refresh token required")

    try:
        payload = decode_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    email = payload.get("sub")
    hashed_rt = hashlib.sha256(token.encode()).hexdigest()

    session = await refresh_tokens_collection.find_one({"hashed_token": hashed_rt})
    if (
        not session
        or session.get("revoked", True)
        or session.get("expires_at").replace(tzinfo=timezone.utc)
        < datetime.now(timezone.utc)
    ):
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired")

    if session.get("used"):
        await refresh_tokens_collection.update_many(
            {"email": email}, {"$set": {"revoked": True}}
        )
        raise HTTPException(status_code=401, detail="Token reuse detected")

    if session.get("user_agent") != request.headers.get("user-agent", ""):
        raise HTTPException(status_code=401, detail="Device mismatch")

    db_user = await users_collection.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")

    await refresh_tokens_collection.update_one(
        {"_id": session["_id"]}, {"$set": {"used": True, "revoked": True}}
    )

    new_access_token = create_access_token(data={"sub": email})
    new_refresh_token = create_refresh_token(data={"sub": email})
    new_hashed_rt = hashlib.sha256(new_refresh_token.encode()).hexdigest()

    await refresh_tokens_collection.insert_one(
        {
            "email": email,
            "hashed_token": new_hashed_rt,
            "expires_at": datetime.now(timezone.utc) + timedelta(days=7),
            "created_at": datetime.now(timezone.utc),
            "user_agent": request.headers.get("user-agent", ""),
            "ip": request.client.host if request.client else "127.0.0.1",
            "used": False,
            "revoked": False,
        }
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "email": email,
        "role": db_user.get("role", "student"),
    }


@router.post("/logout")
async def logout(request: Request, body: RefreshTokenRequest = None):
    """Logout user and revoke refresh token if provided"""
    if body:
        if body.logout_all and body.refresh_token:
            hashed_rt = hashlib.sha256(body.refresh_token.encode()).hexdigest()
            session = await refresh_tokens_collection.find_one(
                {"hashed_token": hashed_rt}
            )
            if session:
                await refresh_tokens_collection.update_many(
                    {"email": session["email"]}, {"$set": {"revoked": True}}
                )
        elif body.refresh_token:
            hashed_rt = hashlib.sha256(body.refresh_token.encode()).hexdigest()
            await refresh_tokens_collection.update_many(
                {"hashed_token": hashed_rt}, {"$set": {"revoked": True}}
            )
    return {"message": "Logged out successfully"}
