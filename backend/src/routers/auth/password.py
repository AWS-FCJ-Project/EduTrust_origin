from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from src.app_config import app_config
from src.auth.auth_utils import generate_otp, hash_password
from src.auth.email_service import send_email
from src.auth.otp_storage import save_otp, verify_otp
from src.auth.auth_utils import hash_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.database import users_collection
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
    del request
    del background_tasks
    try:
        cognito_auth_service.forgot_password(data.email)
    except CognitoAuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)

    return {"message": "If email exists, OTP sent."}


@router.post(
    "/reset-password",
    responses={
        400: {"description": "Invalid or expired OTP"},
    },
)
async def reset_password(data: ResetPassword):
    try:
        cognito_auth_service.confirm_forgot_password(
            data.email,
            data.otp,
            data.new_password,
        )
    except CognitoAuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)

    hashed = hash_password(data.new_password)
    await users_collection.update_one(
        {"email": data.email},
        {"$set": {"hashed_password": hashed}},
    )

    return {"message": "Password reset successfully"}
