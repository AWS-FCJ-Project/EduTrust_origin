from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from datetime import datetime
from src.schemas.auth_schemas import UserRegister, VerifyEmail, ResendOTPRequest

from src.database import users_collection
from src.auth.auth_utils import hash_password, generate_otp
from src.auth.email_service import send_email
from src.redis_client import redis_client
from src.app_config import app_config
from src.extensions import limiter
import pyotp

router = APIRouter()

@router.post("/register")
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegister, background_tasks: BackgroundTasks):
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(user.password)
    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "is_verified": False,
        "totp_secret": None,
        "created_at": datetime.utcnow()
    }
    await users_collection.insert_one(user_doc)
    
    otp = generate_otp()
    await redis_client.setex(f"otp:email_verification:{user.email}", app_config.OTP_EXPIRE_SECONDS, otp)
    
    background_tasks.add_task(send_email, user.email, "Verify Account", f"Your OTP is {otp}")
    
    return {"message": "User registered. Please verify email."}

@router.post("/verify-email")
async def verify_email_route(data: VerifyEmail):
    key = f"otp:email_verification:{data.email}"
    saved_otp = await redis_client.get(key)
    
    if not saved_otp or saved_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Generate TOTP Secret
    totp_secret = pyotp.random_base32()
    
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"is_verified": True, "totp_secret": totp_secret}}
    )
    
    # Generate Provisioning URI
    totp = pyotp.TOTP(totp_secret)
    uri = totp.provisioning_uri(name=data.email, issuer_name=app_config.MONGO_DB_NAME)
    
    return {"message": "Email verified", "totp_uri": uri, "totp_secret": totp_secret}


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(request: Request, data: ResendOTPRequest, background_tasks: BackgroundTasks):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        # Security: Do not reveal if email exists or not
        return {"message": "If email exists, new OTP has been sent."}
    
    if user.get("is_verified"):
         return {"message": "User already verified."}

    # Check Redis for internal rate limit (optional, but good practice)
    # For now relying on @limiter is enough for IP based limits.
    
    otp = generate_otp()
    await redis_client.setex(f"otp:email_verification:{data.email}", app_config.OTP_EXPIRE_SECONDS, otp)
    
    background_tasks.add_task(send_email, data.email, "Resend Verification OTP", f"Your new OTP is {otp}")
    
    return {"message": "If email exists, new OTP has been sent."} 
