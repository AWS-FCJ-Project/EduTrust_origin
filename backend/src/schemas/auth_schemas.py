import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    role: UserRole = UserRole.student

    @field_validator("password")
    def validate_password_complexity(cls, v: str) -> str:
        if (
            not re.search(r"[A-Z]", v)
            or not re.search(r"[a-z]", v)
            or not re.search(r"\d", v)
            or not re.search(r"[^\w\s]", v)
        ):
            raise ValueError(
                "Password must contain 1 capital letter, 1 letter, 1 number and 1 symbol."
            )
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    def validate_new_password_complexity(cls, v: str) -> str:
        if (
            not re.search(r"[A-Z]", v)
            or not re.search(r"[a-z]", v)
            or not re.search(r"\d", v)
            or not re.search(r"[^\w\s]", v)
        ):
            raise ValueError(
                "Password must contain 1 capital letter, 1 letter, 1 number and 1 symbol."
            )
        return v


class UserInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    hashed_password: str
    is_verified: bool = False
    name: Optional[str] = None
    role: UserRole = UserRole.student
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class UserInfoResponse(BaseModel):
    id: str
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role", UserRole.student.value),
        "is_verified": bool(user.get("is_verified", False)),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
