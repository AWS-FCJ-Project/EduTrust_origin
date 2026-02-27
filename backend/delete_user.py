import asyncio
import io
import sys

from motor.motor_asyncio import AsyncIOMotorClient
from src.app_config import app_config

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run python delete_user.py <email_to_delete>")
        print("Example: uv run python delete_user.py hieu16012005@gmail.com")
        sys.exit(1)

    email_to_delete = sys.argv[1]

    # Kết nối DB trực tiếp không import qua file database để đảm bảo Event Loop không gặp lỗi trên Windows
    client = AsyncIOMotorClient(app_config.MONGO_URI)
    db = client[app_config.MONGO_DB_NAME]
    users_collection = db["users"]
    otp_collection = db["otps"]

    try:
        print(f"Bat dau quy trinh don dep cho email: {email_to_delete}")

        # 1. Xoá User trong bảng (collection) users
        user_result = await users_collection.delete_many({"email": email_to_delete})
        print(f" -> Da xoa {user_result.deleted_count} tai khoan nguoi dung.")

        # 2. Xoá các session OTP đang treo trong bảng (collection) otps của user này
        otp_result = await otp_collection.delete_many({"email": email_to_delete})
        print(f" -> Da xoa {otp_result.deleted_count} ma OTP dang ton dong.")

        print("\nHoan tat! Ban co the su dung email nay de dang ky lai tu dau.")
    finally:
        # Ngắt kết nối để event loop đóng an toàn
        client.close()


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
