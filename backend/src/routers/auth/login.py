from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, status

from backend.src.auth.auth_utils import verify_password
from backend.src.auth.jwt_handler import create_access_token
from backend.src.database import users_collection
from backend.src.extensions import limiter
from backend.src.schemas.auth_schemas import UserLogin

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


@router.post("/logout")
async def logout():
    """Logout user (client-side handles token removal)"""
    return {"message": "Client should remove the token to logout"}
