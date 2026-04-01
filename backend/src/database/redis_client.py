import json
import logging
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis connection management."""

    def __init__(
        self,
        host: Optional[str] = None,
        password: Optional[str] = None,
        port: Optional[int] = None,
        db: Optional[int] = None,
        tls: bool = False,
        key_prefix: Optional[str] = None,
        chat_ttl: Optional[int] = None,
    ):
        from src.app_config import app_config

        self.host = host or app_config.REDIS_CLIENT_HOST
        self.port = port or app_config.REDIS_CLIENT_PORT
        self.db = db if db is not None else app_config.REDIS_DB
        self.password = password or app_config.REDIS_CLIENT_PASSWORD
        self.use_tls = tls if tls is not None else app_config.REDIS_TLS
        self.key_prefix = key_prefix or app_config.REDIS_KEY_PREFIX
        self.chat_ttl = chat_ttl if chat_ttl is not None else app_config.REDIS_CHAT_TTL

        self._is_connected = False
        self._client: Optional[redis.Redis] = None

    def _create_client(self) -> redis.Redis:
        """Create Redis client instance."""
        return redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            password=self.password,
            decode_responses=True,
            ssl=self.use_tls,
            ssl_cert_reqs="none" if self.use_tls else None,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

    def connect_to_database(self) -> bool:
        """Connect to Redis server."""
        try:
            self._client = self._create_client()
            ping_result = self._client.ping()
            self._is_connected = True
            logger.info(f"Redis ping result: {ping_result}")
            logger.info("Connected to Redis")
            return True
        except Exception as e:
            self._is_connected = False
            logger.warning(f"Redis connection failed: {e}")
            return False

    def is_healthy(self) -> bool:
        """Check if Redis is connected."""
        return self._is_connected

    def close(self) -> None:
        """Close Redis connection."""
        if self._client is not None:
            try:
                self._client.close()
                self._is_connected = False
            except Exception as e:
                logger.error(f"Error closing Redis: {e}")

    def _ttl_seconds(self) -> Optional[int]:
        """Get TTL in seconds for cache expiration."""
        if not isinstance(self.chat_ttl, int):
            return None
        return self.chat_ttl if self.chat_ttl > 0 else None

    def _serialize(self, obj: Any) -> Any:
        """Recursively serialize objects for JSON storage (handles datetime)."""
        if isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._serialize(item) for item in obj]
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj

    def set_json(self, key: str, value: Dict, expiration: Optional[int] = None) -> bool:
        """Store dictionary as JSON in Redis."""
        if not self._is_connected or self._client is None:
            return False
        try:
            self._client.set(key, json.dumps(value, ensure_ascii=False), ex=expiration)
            return True
        except Exception as e:
            logger.error(f"Set error: {e}")
            return False

    def get_json(self, key: str) -> Optional[Dict]:
        """Retrieve JSON dictionary from Redis."""
        if not self._is_connected or self._client is None:
            return None
        try:
            val = self._client.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.error(f"Get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """Delete a key from Redis."""
        if not self._is_connected or self._client is None:
            return False
        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False

    def build_key(self, *parts: Any) -> str:
        """Build namespaced Redis key."""
        normalized_parts = [str(part).strip(":") for part in parts]
        prefix = (self.key_prefix or "").strip(":")
        if prefix:
            return ":".join([prefix, *normalized_parts])
        return ":".join(normalized_parts)
