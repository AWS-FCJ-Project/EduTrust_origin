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


class UserRole(str, Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: Optional[str] = None
    role: UserRole = UserRole.student
    class_name: Optional[str] = None
    grade: Optional[int] = None
    base_64_url: Optional[str] = None

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
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: List[str] = []
    password_plain: Optional[str] = None
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
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: List[str] = []
    is_verified: bool = False
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    class_name: Optional[str] = None
    grade: Optional[int] = None
    subjects: Optional[List[str]] = None
    password: Optional[str] = None
    base_64_url: Optional[str] = None


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user.get("name"),
        "role": user.get("role", UserRole.student.value),
        "class_name": user.get("class_name"),
        "grade": user.get("grade"),
        "subjects": user.get("subjects", []),
        "is_verified": bool(user.get("is_verified", False)),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
        "avatar_url": user.get("avatar_url"),
    }
