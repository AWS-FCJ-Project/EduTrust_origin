import re
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)
from src.utils.s3_utils import get_s3_handler


class UserRole(str, Enum):
    """Enum for user roles."""

    student = "student"
    teacher = "teacher"
    admin = "admin"


class UserRegister(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    role: UserRole = UserRole.student
    class_name: Optional[str] = None
    grade: Optional[int] = None
    avatar: Optional[str] = Field(
        None, description="Avatar as base64 data URL or image URL"
    )

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

    @model_validator(mode="after")
    def check_student_info(self) -> "UserRegister":
        if self.role == UserRole.student:
            if not self.class_name or not self.grade:
                raise ValueError("Students must provide class_name and grade.")
        return self


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr


class ResetPassword(BaseModel):
    """Schema for password reset."""

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
    """Schema for user stored in database."""

    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    hashed_password: str
    is_verified: bool = False
    name: Optional[str] = None
    role: UserRole = UserRole.student
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: List[str] = []
    avatar: Optional[str] = None
    password_plain: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class UserInfoResponse(BaseModel):
    """Schema for user info response."""

    id: str
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: List[str] = []
    avatar: Optional[str] = None
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for updating user info."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: Optional[List[str]] = None
    avatar: Optional[str] = None
    password: Optional[str] = None


class StudentResponse(BaseModel):
    """Schema for student list response."""

    id: str
    name: Optional[str] = None
    email: str
    role: str
    class_name: Optional[str] = None
    grade: Optional[int] = None


class TeacherClassAssignment(BaseModel):
    """Schema for teacher class assignment."""

    id: str
    name: str
    role: str


class TeacherResponse(BaseModel):
    """Schema for teacher list response."""

    id: str
    name: Optional[str] = None
    email: str
    subjects: List[str] = []
    assigned_classes: List[TeacherClassAssignment] = []
    is_assigned: bool = False


class AdminResponse(BaseModel):
    """Schema for admin list response."""

    id: str
    name: Optional[str] = None
    email: str


class LoginResponse(BaseModel):
    """Schema for login response."""

    access_token: str
    token_type: str = "bearer"
    email: str


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


class UpdateUserResponse(BaseModel):
    """Response for user update."""

    message: str = "User updated successfully"


def user_helper(user) -> dict:
    """Convert user document to user info dict."""
    avatar_value = user.get("avatar")
    # If avatar is S3 key (starts with "avatars/"), generate fresh presigned URL
    if avatar_value and str(avatar_value).startswith("avatars/"):
        s3 = get_s3_handler()
        avatar_value = (
            s3.get_presigned_url(avatar_value, expiration=604800) or avatar_value
        )

    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role", UserRole.student.value),
        "class_name": user.get("class_name"),
        "grade": user.get("grade"),
        "subjects": user.get("subjects", []),
        "avatar": avatar_value,
        "is_verified": bool(user.get("is_verified", False)),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
