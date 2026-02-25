from typing import Optional

from fastapi import Header, HTTPException, Query, status
from src.auth.jwt_handler import decode_token


async def get_current_user(
    authorization: Optional[str] = Header(default=None, include_in_schema=False),
    token: Optional[str] = Query(
        default=None, description="Access token (Swagger testing only)"
    ),
) -> str:
    raw_token: Optional[str] = None

    if authorization:
        raw_token = (
            authorization[7:]
            if authorization.lower().startswith("bearer ")
            else authorization
        )
    elif token:
        raw_token = token

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(raw_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email: str = payload.get("sub", "")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing subject.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return email
