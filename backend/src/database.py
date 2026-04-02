from motor.motor_asyncio import AsyncIOMotorClient

from src.app_config import app_config

client = AsyncIOMotorClient(
    app_config.MONGO_URI,
    tz_aware=True,
)

db = client[app_config.MONGO_DB_NAME]
users_collection = db["users"]
exams_collection = db["exams"]
classes_collection = db["classes"]
violations_collection = db["violations"]
submissions_collection = db["submissions"]
