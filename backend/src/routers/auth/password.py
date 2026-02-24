from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from src.app_config import app_config
from src.auth.auth_utils import generate_otp, hash_password
from src.auth.email_service import send_email
from src.auth.otp_storage import save_otp, verify_otp
from src.database import users_collection
from src.extensions import limiter
from src.schemas.auth_schemas import ForgotPassword, ResetPassword

router = APIRouter()


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    data: ForgotPassword,
    background_tasks: BackgroundTasks,
):
    user = await users_collection.find_one({"email": data.email})

    # Không tiết lộ user có tồn tại hay không
    if not user:
        return {"message": "If email exists, OTP sent."}

    otp = generate_otp()

    await save_otp(
        data.email,
        otp,
        "password_reset",
        app_config.OTP_EXPIRE_SECONDS,
    )

    background_tasks.add_task(
        send_email,
        data.email,
        "Reset Password",
        f"Your OTP is {otp}",
    )

    return {"message": "If email exists, OTP sent."}


@router.post("/reset-password")
async def reset_password(data: ResetPassword):
    is_valid = await verify_otp(
        data.email,
        data.otp,
        "password_reset",
    )

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired OTP",
        )

    hashed = hash_password(data.new_password)

    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"hashed_password": hashed}},
    )

    return {"message": "Password reset successfully"}