import redis.asyncio as redis
from src.app_config import app_config

redis_client = redis.from_url(app_config.REDIS_URL, decode_responses=True)
