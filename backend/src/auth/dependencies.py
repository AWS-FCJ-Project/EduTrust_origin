from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.auth.cognito_auth import CognitoAuthError, cognito_auth_service
from src.database import users_collection

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


async def get_current_user(claims: dict = Depends(get_current_auth_claims)):
    cognito_sub = claims.get("sub")
    email = claims.get("email")
    cognito_groups = claims.get("cognito:groups") or []

    user = None
    if cognito_sub:
        user = await users_collection.find_one({"cognito_sub": cognito_sub})

    if user is None and email:
        user = await users_collection.find_one({"email": email})
        if user is not None and cognito_sub and user.get("cognito_sub") != cognito_sub:
            await users_collection.update_one(
                {"_id": user["_id"]},
                {"$set": {"cognito_sub": cognito_sub}},
            )
            user["cognito_sub"] = cognito_sub

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.get("role") and cognito_groups:
        user["role"] = cognito_groups[0]

    return user
