"""
OTP storage using MongoDB instead of Redis
"""
from datetime import datetime, timedelta
from src.database import db

# Collection để lưu OTP
otp_collection = db["otps"]

async def save_otp(email: str, otp: str, purpose: str, expire_seconds: int = 300):
    """
    Lưu OTP vào MongoDB với thời gian hết hạn
    purpose: 'email_verification', 'password_reset', etc.
    """
    expire_at = datetime.utcnow() + timedelta(seconds=expire_seconds)
    
    await otp_collection.update_one(
        {"email": email, "purpose": purpose},
        {
            "$set": {
                "otp": otp,
                "expire_at": expire_at,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

async def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """
    Verify OTP và xóa nếu hợp lệ
    Returns True nếu valid, False nếu không
    """
    doc = await otp_collection.find_one({
        "email": email,
        "purpose": purpose,
        "otp": otp
    })
    
    if not doc:
        return False
    
    # Kiểm tra expiry
    if doc["expire_at"] < datetime.utcnow():
        # Xóa OTP đã hết hạn
        await otp_collection.delete_one({"_id": doc["_id"]})
        return False
    
    # OTP hợp lệ - xóa để không dùng lại
    await otp_collection.delete_one({"_id": doc["_id"]})
    return True

async def cleanup_expired_otps():
    """
    Cleanup OTPs đã hết hạn (có thể chạy định kỳ)
    """
    await otp_collection.delete_many({
        "expire_at": {"$lt": datetime.utcnow()}
    })
