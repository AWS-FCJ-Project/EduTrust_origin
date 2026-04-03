from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.deps import get_db_session
from src.models import User

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
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return email


async def get_current_user(
    claims: dict = Depends(get_current_auth_claims),
    session=Depends(get_db_session),
):
    cognito_sub = claims.get("sub")
    email = claims.get("email")
    cognito_groups = claims.get("cognito:groups") or []

    user: User | None = None
    if cognito_sub:
        result = await session.execute(select(User).where(User.cognito_sub == cognito_sub))
        user = result.scalar_one_or_none()

    if user is None and email:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is not None and cognito_sub and user.cognito_sub != cognito_sub:
            await session.execute(
                update(User).where(User.id == user.id).values(cognito_sub=cognito_sub)
            )
            user.cognito_sub = cognito_sub

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    role = user.role
    if (not role) and cognito_groups:
        role = cognito_groups[0]

    return {
        "_id": user.id,
        "email": user.email,
        "name": user.name,
        "role": role or "student",
        "class_name": user.class_name,
        "grade": user.grade,
        "subjects": list(user.subjects or []),
        "is_verified": bool(user.is_verified),
        "created_at": user.created_at,
        "last_login": user.last_login,
        "cognito_sub": user.cognito_sub,
    }
