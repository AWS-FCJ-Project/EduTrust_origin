from fastapi import APIRouter, Depends, Request

from src.auth.session_handler import get_current_user

router = APIRouter()


@router.get("/protected")
async def protected_route(request: Request, email: str = Depends(get_current_user)):
    """Example of a protected route that requires authentication"""
    return {"message": "You have access to protected route", "user_email": email}
