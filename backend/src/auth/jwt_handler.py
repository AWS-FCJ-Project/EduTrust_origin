from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from src.app_config import app_config


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "type": "access",
        "iat": _now(),
        "exp": _now() + timedelta(minutes=app_config.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload, app_config.SECRET_KEY, algorithm=app_config.JWT_ALGORITHM
    )


def create_refresh_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "type": "refresh",
        "iat": _now(),
        "exp": _now() + timedelta(days=app_config.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(
        payload, app_config.SECRET_KEY, algorithm=app_config.JWT_ALGORITHM
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token, app_config.SECRET_KEY, algorithms=[app_config.JWT_ALGORITHM]
        )
    except JWTError:
        return None
