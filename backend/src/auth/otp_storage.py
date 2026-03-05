"""
OTP Storage — Redis (Amazon ElastiCache)
Thay thế MongoDB cho OTP storage để có TTL tự động và performance tốt hơn.

Khi dùng ElastiCache:
- REDIS_URL=redis://aws-fcj-redis.xxxxx.cache.amazonaws.com:6379

Khi dev local:
- REDIS_URL=redis://localhost:6379
"""

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis

from src.app_config import app_config

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------
# Redis connection pool (singleton per process)
# -----------------------------------------------------------------
_redis_pool: aioredis.Redis | None = None


def _get_redis() -> aioredis.Redis:
    """Trả về Redis client. Tạo mới nếu chưa có."""
    global _redis_pool
    if _redis_pool is None:
        redis_url = app_config.REDIS_URL or "redis://localhost:6379"
        _redis_pool = aioredis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        logger.info(f"Redis connected: {redis_url}")
    return _redis_pool


def _otp_key(email: str, purpose: str) -> str:
    """Tạo Redis key theo pattern: otp:{purpose}:{email}"""
    return f"otp:{purpose}:{email}"


# -----------------------------------------------------------------
# Public API (giữ nguyên signature để không cần đổi code khác)
# -----------------------------------------------------------------


async def save_otp(email: str, otp: str, purpose: str, expire_seconds: int = 300) -> None:
    """
    Lưu OTP vào Redis với TTL tự động.

    Args:
        email:          Email người dùng
        otp:            Mã OTP
        purpose:        Mục đích (vd: "register", "reset_password")
        expire_seconds: Thời gian hết hạn (giây), mặc định 5 phút
    """
    r = _get_redis()
    key = _otp_key(email, purpose)

    payload = json.dumps({
        "otp": otp,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })

    # Redis tự xử lý TTL — không cần cleanup thủ công
    await r.set(key, payload, ex=expire_seconds)
    logger.debug(f"OTP saved for {email} [{purpose}] — expires in {expire_seconds}s")


async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """
    Xác minh OTP. Tự động xóa sau khi verify (dù đúng hay sai quá số lần).

    Args:
        email:   Email người dùng
        otp:     Mã OTP cần kiểm tra
        purpose: Mục đích

    Returns:
        True nếu OTP đúng và còn hiệu lực
    """
    r = _get_redis()
    key = _otp_key(email, purpose)

    raw = await r.get(key)
    if not raw:
        logger.debug(f"OTP not found or expired for {email} [{purpose}]")
        return False

    try:
        data = json.loads(raw)
        stored_otp = data.get("otp")
    except (json.JSONDecodeError, KeyError):
        await r.delete(key)
        return False

    if stored_otp != otp:
        logger.debug(f"OTP mismatch for {email} [{purpose}]")
        return False

    # OTP đúng → xóa ngay để tránh dùng lại
    await r.delete(key)
    logger.info(f"OTP verified successfully for {email} [{purpose}]")
    return True


async def cleanup_expired_otps() -> None:
    """
    Không cần làm gì — Redis tự xóa key hết hạn.
    Giữ function này để backward compatible với code cũ.
    """
    logger.debug("cleanup_expired_otps: Redis handles TTL automatically, nothing to do.")
