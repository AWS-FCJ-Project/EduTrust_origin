from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from src.schemas.auth_schemas import ForgotPassword, ResetPassword
from src.database import users_collection
from src.auth.auth_utils import generate_otp, hash_password
from src.auth.email_service import send_email
from src.redis_client import redis_client
from src.app_config import app_config
from src.extensions import limiter

router = APIRouter()

@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(request: Request, data: ForgotPassword, background_tasks: BackgroundTasks):
    user = await users_collection.find_one({"email": data.email})
    if not user:
        # Don't reveal user existence
        return {"message": "If email exists, OTP sent."}
        
    otp = generate_otp()
    await redis_client.setex(f"otp:password_reset:{data.email}", app_config.OTP_EXPIRE_SECONDS, otp)
    
    background_tasks.add_task(send_email, data.email, "Reset Password", f"Your OTP is {otp}")
    
    return {"message": "If email exists, OTP sent."}

@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    key = f"otp:password_reset:{data.email}"
    saved_otp = await redis_client.get(key)
    
    if not saved_otp or saved_otp != data.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
    hashed = hash_password(data.new_password)
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"hashed_password": hashed}}
    )
    
    # Invalidate OTP
    await redis_client.delete(key)
    
    return {"message": "Password reset successfully"}
