from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from src.auth.auth_utils import hash_password
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import UserRegister

router = APIRouter()


@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegister):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "is_verified": True,
        "created_at": datetime.utcnow(),
    }
    await users_collection.insert_one(user_doc)

    return {"message": "User registered successfully, you can now login."}
