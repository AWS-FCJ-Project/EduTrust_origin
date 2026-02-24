from datetime import datetime, timedelta, timezone

from src.database import db

otp_collection = db["otps"]


async def save_otp(email: str, otp: str, purpose: str, expire_seconds: int = 300):
    now = datetime.now(timezone.utc)
    expire_at = now + timedelta(seconds=expire_seconds)

    await otp_collection.update_one(
        {"email": email, "purpose": purpose},
        {
            "$set": {
                "otp": otp,
                "expire_at": expire_at,
                "created_at": now,
            }
        },
        upsert=True,
    )


async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    now = datetime.now(timezone.utc)

    doc = await otp_collection.find_one(
        {"email": email, "purpose": purpose, "otp": otp}
    )

    if not doc:
        return False

    if doc["expire_at"] < now:
        await otp_collection.delete_one({"_id": doc["_id"]})
        return False

    await otp_collection.delete_one({"_id": doc["_id"]})
    return True


async def cleanup_expired_otps():
    now = datetime.now(timezone.utc)
    await otp_collection.delete_many({"expire_at": {"$lt": now}})
