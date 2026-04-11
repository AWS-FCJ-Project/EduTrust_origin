from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from src.auth.auth_utils import hash_password
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
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
async def reset_password(request: Request, data: ResetPassword):
    try:
        cognito_auth_service.confirm_forgot_password(
            data.email,
            data.otp,
            data.new_password,
        )
    except CognitoAuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)

    persistence = request.app.state.persistence
    user = await persistence.users.get_by_email(data.email)
    if user:
        user_id = str(user.get("user_id") or user.get("_id") or "")
        await persistence.users.update(
            user_id, {"hashed_password": hash_password(data.new_password)}
        )

    return {"message": "Password reset successfully"}
