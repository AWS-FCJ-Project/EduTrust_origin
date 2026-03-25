from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from src.app_config import app_config

SECRET_KEY = app_config.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update(
        {"exp": expire, "type": "access", "iat": datetime.now(timezone.utc)}
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # Default to 7 days
    to_encode.update(
        {"exp": expire, "type": "refresh", "iat": datetime.now(timezone.utc)}
    )
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        raise ValueError("Token expired")
    except InvalidTokenError:
        raise ValueError("Invalid token")
    except jwt.PyJWTError:
        raise ValueError("Could not validate credentials")
