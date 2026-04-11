# Legacy compatibility module - delegates to PersistenceFacade OTP repository.
# Phase 01: used MongoDB directly; Phase 03: uses DynamoDB via OtpRepository.
# Tests and callers importing from here get the current persistence implementation.
from datetime import datetime, timezone
from typing import Callable, Optional

# Injectable repo getter - defaults to src.main app state, override-able for tests.
_otp_repo_getter: Optional[Callable] = None


def _set_otp_repo_getter(getter: Callable) -> None:
    """Override the OTP repo getter (for testing)."""
    global _otp_repo_getter
    _otp_repo_getter = getter


def _get_otp_repo():
    """Get OTP repository. Uses injected getter if set, otherwise falls back to app state."""
    if _otp_repo_getter is not None:
        return _otp_repo_getter()
    from src.main import app

    return app.state.persistence.otps


async def save_otp(
    email: str, otp: str, purpose: str, expire_seconds: int = 300
) -> None:
    """Save an OTP for the given email and purpose."""
    repo = _get_otp_repo()
    await repo.save_otp(email, purpose, otp, expire_seconds)


async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """Verify an OTP. Returns True if valid and not expired, False otherwise."""
    repo = _get_otp_repo()
    doc = await repo.get_otp(email, purpose, otp)
    if not doc:
        return False

    expire_at = doc.get("expire_at")
    if expire_at is None:
        return False

    # Handle both naive and aware datetimes
    if expire_at.tzinfo is None:
        expire_at = expire_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    if expire_at < now:
        await repo.delete_otp(email, purpose)
        return False

    await repo.delete_otp(email, purpose)
    return True


async def cleanup_expired_otps() -> None:
    """Cleanup expired OTPs. DynamoDB uses TTL so this is a no-op."""
    repo = _get_otp_repo()
    await repo.delete_expired_otps()
