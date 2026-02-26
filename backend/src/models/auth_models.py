from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserInDB(BaseModel):
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    hashed_password: str
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True


def user_helper(user) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "is_verified": user.get("is_verified"),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
