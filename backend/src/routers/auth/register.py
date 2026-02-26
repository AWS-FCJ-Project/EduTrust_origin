from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from src.app_config import app_config
from src.auth.auth_utils import generate_otp, hash_password
from src.auth.email_service import send_email
from src.auth.otp_storage import save_otp, verify_otp
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import ResendOTPRequest, UserRegister, VerifyEmail

router = APIRouter()


@router.post("/register")
@limiter.limit("5/minute")
async def register(
    request: Request, user: UserRegister, background_tasks: BackgroundTasks
):
    """Register a new user and send an email verification OTP."""
    existing = await users_collection.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")

    user_doc = {
        "email": user.email,
        "hashed_password": hash_password(user.password),
        "is_verified": False,
        "created_at": datetime.now(timezone.utc),
    }
    await users_collection.insert_one(user_doc)

    otp = generate_otp()
    await save_otp(user.email, otp, "email_verification", app_config.OTP_EXPIRE_SECONDS)
    background_tasks.add_task(
        send_email, user.email, "Verify Account", f"Your OTP is {otp}"
    )

    return {"message": "User registered. Please verify your email."}


@router.post("/verify-email")
async def verify_email_route(data: VerifyEmail):
    """Verify a user's email address using the OTP sent during registration."""
    is_valid = await verify_otp(data.email, data.otp, "email_verification")
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP.")

    await users_collection.update_one(
        {"email": data.email}, {"$set": {"is_verified": True}}
    )
    return {"message": "Email verified successfully. You can now log in."}


@router.post("/resend-otp")
@limiter.limit("3/minute")
async def resend_otp(
    request: Request, data: ResendOTPRequest, background_tasks: BackgroundTasks
):
    """Resend the email verification OTP."""
    user = await users_collection.find_one({"email": data.email})
    if not user:
        return {"message": "If the email exists, a new OTP has been sent."}

    if user.get("is_verified"):
        return {"message": "User is already verified."}

    otp = generate_otp()
    await save_otp(data.email, otp, "email_verification", app_config.OTP_EXPIRE_SECONDS)
    background_tasks.add_task(
        send_email, data.email, "Resend Verification OTP", f"Your new OTP is {otp}"
    )

    return {"message": "If the email exists, a new OTP has been sent."}
