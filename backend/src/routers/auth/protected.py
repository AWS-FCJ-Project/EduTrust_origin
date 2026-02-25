from fastapi import APIRouter, Depends
from src.auth.dependencies import get_current_user

router = APIRouter()


@router.get("/protected")
async def protected_route(email: str = Depends(get_current_user)):
    """Example protected route — requires a valid JWT Bearer token."""
    return {"message": "You have access to the protected route", "user_email": email}
