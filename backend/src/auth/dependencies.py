from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service

security = HTTPBearer()


async def get_current_auth_claims(
    auth: HTTPAuthorizationCredentials = Depends(security),
):
    token = auth.credentials
    try:
        return cognito_auth_service.verify_token(token)
    except CognitoAuthError as error:
        raise HTTPException(
            status_code=error.status_code or status.HTTP_401_UNAUTHORIZED,
            detail=error.message,
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_email(
    claims: dict = Depends(get_current_auth_claims),
):
    email = claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


async def get_current_user(
    request: Request,
    claims: dict = Depends(get_current_auth_claims),
):
    persistence = request.app.state.persistence
    email = claims.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await persistence.users.get_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    cognito_groups = claims.get("cognito:groups") or []
    if not user.get("role") and cognito_groups:
        user["role"] = cognito_groups[0]

    if "_id" not in user and user.get("user_id"):
        user["_id"] = user.get("user_id")

    return user
