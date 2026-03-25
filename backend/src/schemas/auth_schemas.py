import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(
        default="student", description="Role of the user: student, teacher, or admin"
    )

    @validator("role")
    def validate_role(cls, v: str) -> str:
        allowed_roles = {"student", "teacher", "admin"}
        v_lower = v.lower().strip()
        if v_lower not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v_lower

    @validator("password")
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


class RefreshTokenRequest(BaseModel):
    refresh_token: Optional[str] = None
    logout_all: bool = False


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)

    @validator("new_password")
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
    role: str = "student"
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "student"),
        "is_verified": user.get("is_verified"),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
