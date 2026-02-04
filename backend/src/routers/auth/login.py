from fastapi import APIRouter, HTTPException, status, Depends, Request
from src.schemas.auth_schemas import UserLogin, Verify2FA, RefreshTokenRequest
from src.database import users_collection
from src.auth.auth_utils import verify_password
from src.auth.jwt_handler import create_access_token, create_refresh_token, decode_token
from src.extensions import limiter
import pyotp
from datetime import datetime

router = APIRouter()

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user: UserLogin):
    db_user = await users_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not db_user.get("is_verified"):
        raise HTTPException(status_code=403, detail="Email not verified")

    return {"message": "Credentials valid. Please enter 2FA code."}

@router.post("/verify-2fa")
async def verify_2fa(data: Verify2FA):
    db_user = await users_collection.find_one({"email": data.email})
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
        
    secret = db_user.get("totp_secret")
    if not secret:
        raise HTTPException(status_code=400, detail="2FA not setup")
        
    totp = pyotp.TOTP(secret)
    if not totp.verify(data.totp_code):
        raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
    # Success
    access_token = create_access_token({"sub": data.email})
    refresh_token = create_refresh_token({"sub": data.email})
    
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token, 
        "token_type": "bearer"
    }

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token subject")
        
    new_access_token = create_access_token({"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}
