import re

from pydantic import BaseModel, EmailStr, Field, validator


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

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
