from datetime import datetime, timedelta, timezone

from src.database import db

otp_collection = db["otps"]

expire_at = datetime.now(timezone.utc)

async def save_otp(email: str, otp: str, purpose: str, expire_seconds: int = 300):
    expire_at = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)

    await otp_collection.update_one(
        {"email": email, "purpose": purpose},
        {
            "$set": {
                "otp": otp,
                "expire_at": expire_at,
                "created_at": datetime.now(timezone.utc),
            }
        },
        upsert=True,
    )


async def verify_otp(email: str, otp: str, purpose: str) -> bool:

    doc = await otp_collection.find_one(
        {"email": email, "purpose": purpose, "otp": otp}
    )

    if not doc:
        return False

    if doc["expire_at"] < datetime.now(timezone.utc):

        await otp_collection.delete_one({"_id": doc["_id"]})
        return False

    await otp_collection.delete_one({"_id": doc["_id"]})
    return True


async def cleanup_expired_otps():

    await otp_collection.delete_many({"expire_at": {"$lt": datetime.now(timezone.utc)}})
