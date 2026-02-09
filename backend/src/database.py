from motor.motor_asyncio import AsyncIOMotorClient
from src.app_config import app_config

client = AsyncIOMotorClient(app_config.MONGO_URI)
db = client[app_config.MONGO_DB_NAME]
users_collection = db["users"]
