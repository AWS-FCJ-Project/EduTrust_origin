from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from src.app_config import app_config
from src.auth.auth_utils import generate_otp, hash_password
from src.auth.email_service import send_email
from src.extensions import limiter
from src.schemas.auth_schemas import ForgotPassword, ResetPassword

router = APIRouter()


@router.post(
    "/forgot-password",
    responses={
        429: {"description": "Too Many Requests"},
    },
)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request, data: ForgotPassword, background_tasks: BackgroundTasks
):
    persistence = request.app.state.persistence
    user = await persistence.users.get_by_email(data.email)
    if not user:
        return {"message": "If email exists, OTP sent."}

    otp = generate_otp()
    await persistence.otps.save_otp(
        data.email, "password_reset", otp, app_config.OTP_EXPIRE_SECONDS
    )

    background_tasks.add_task(
        send_email, data.email, "Reset Password", f"Your OTP is {otp}"
    )

    return {"message": "If email exists, OTP sent."}


@router.post(
    "/reset-password",
    responses={
        400: {"description": "Invalid or expired OTP"},
    },
)
async def reset_password(request: Request, data: ResetPassword):
    persistence = request.app.state.persistence
    otp_doc = await persistence.otps.get_otp(data.email, "password_reset", data.otp)

    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    from datetime import datetime, timezone

    expire_at = otp_doc["expire_at"]
    now = datetime.now(timezone.utc)
    if expire_at < now:
        await persistence.otps.delete_otp(data.email, "password_reset")
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    hashed = hash_password(data.new_password)
    await persistence.users.update_one(
        {"email": data.email}, {"$set": {"hashed_password": hashed}}
    )
    await persistence.otps.delete_otp(data.email, "password_reset")

    return {"message": "Password reset successfully"}
