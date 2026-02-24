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
                "Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character."
            )
        return v



class VerifyEmail(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)



class UserLogin(BaseModel):
    email: EmailStr
    password: str



class RefreshTokenRequest(BaseModel):
    refresh_token: str



class ForgotPassword(BaseModel):
    email: EmailStr


class ResendOTPRequest(BaseModel):
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
                "Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character."
            )
        return v