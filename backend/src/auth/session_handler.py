
from fastapi import Request, HTTPException, status
from datetime import datetime

def set_user_session(request: Request, email: str):
    request.session["user_email"] = email
    request.session["login_time"] = datetime.utcnow().isoformat()

def get_current_user(request: Request) -> str:
    email = request.session.get("user_email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please login."
        )
    return email

def clear_user_session(request: Request):
    request.session.clear()

def is_authenticated(request: Request) -> bool:
    return "user_email" in request.session
