import json
import logging
from typing import Any, Dict, Optional

from src.memory.redis_client import RedisClient

logger = logging.getLogger(__name__)


class ConversationCache:
    def __init__(self, redis_client: RedisClient):
        self._redis = redis_client

    def _conversation_key(self, conversation_id: str) -> str:
        return self._redis.build_key("chat", "conversation", conversation_id)

    def cache_conversation(self, conversation: Dict[str, Any]) -> bool:
        if not self._redis.is_healthy():
            return False
        try:
            conv_id = conversation.get("_id")
            if not conv_id:
                return False
            data = self._redis._serialize(conversation)
            self._redis.client.set(
                self._conversation_key(conv_id),
                json.dumps(data, ensure_ascii=False),
                ex=self._redis._ttl_seconds(),
            )
            return True
        except Exception as e:
            logger.error(f"Cache error: {e}")
            return False

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        if not self._redis.is_healthy():
            return None
        try:
            data = self._redis.client.get(self._conversation_key(conversation_id))
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Get error: {e}")
            return None

    def invalidate_conversation(self, conversation_id: str) -> bool:
        if not self._redis.is_healthy():
            return False
        try:
            return self._redis.delete(self._conversation_key(conversation_id))
        except Exception as e:
            logger.error(f"Invalidate error: {e}")
            return False

    def close(self) -> None:
        self._redis.close_connection()
