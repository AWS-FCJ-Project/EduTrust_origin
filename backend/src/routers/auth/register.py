from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from datetime import datetime
from src.schemas.auth_schemas import UserRegister, VerifyEmail, ResendOTPRequest

from src.database import users_collection
from src.auth.auth_utils import hash_password, generate_otp
from src.auth.email_service import send_email
from src.auth.otp_storage import save_otp, verify_otp
from src.app_config import app_config
from src.extensions import limiter

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
        "created_at": datetime.utcnow()
    }
    await users_collection.insert_one(user_doc)
    
    # Generate and save OTP to MongoDB
    otp = generate_otp()
    await save_otp(user.email, otp, "email_verification", app_config.OTP_EXPIRE_SECONDS)
    
    # Send email in background
    background_tasks.add_task(send_email, user.email, "Verify Account", f"Your OTP is {otp}")
    
    return {"message": "User registered. Please verify email."}

@router.post("/verify-email")
async def verify_email_route(data: VerifyEmail):
    # Verify OTP from MongoDB
    is_valid = await verify_otp(data.email, data.otp, "email_verification")
    
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Mark user as verified (no TOTP setup)
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"is_verified": True}}
    )
    
    return {"message": "Email verified successfully. You can now login."}


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(request: Request, data: ResendOTPRequest, background_tasks: BackgroundTasks):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        # Security: Do not reveal if email exists or not
        return {"message": "If email exists, new OTP has been sent."}
    
    if user.get("is_verified"):
         return {"message": "User already verified."}

    # Generate new OTP
    otp = generate_otp()
    await save_otp(data.email, otp, "email_verification", app_config.OTP_EXPIRE_SECONDS)
    
    background_tasks.add_task(send_email, data.email, "Resend Verification OTP", f"Your new OTP is {otp}")
    
    return {"message": "If email exists, new OTP has been sent."}
