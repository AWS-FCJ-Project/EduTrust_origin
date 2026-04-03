import json
import re
from datetime import datetime, timezone
from typing import Any, Optional

from src.logger import logger
from src.memory.conversation_cache import ConversationCache
from src.memory.redis_client import RedisClient


class ConversationHandler:
    """
    Conversation storage backed by Redis (single active conversation per user).

    Design goals:
    - Do not persist conversations in a database.
    - Keep only 1 active conversation per user.
    - Auto-clean after 30 minutes of inactivity via Redis TTL (sliding TTL).

    Notes:
    - We keep the existing public API used by routes/agent code.
    - This class relies on Redis being connected in app lifespan.
    """

    def __init__(
        self,
        *,
        redis_client: RedisClient,
        conversation_cache: Optional[ConversationCache] = None,
    ):
        self._redis = redis_client
        self._conversation_cache = conversation_cache

    def _log_cache(
        self,
        event: str,
        *,
        conversation_id: str,
        message_limit: Optional[int] = None,
        cached_messages: Optional[int] = None,
    ) -> None:
        logger.info(
            "conversation_cache %s conversation_id=%s message_limit=%s cached_messages=%s",
            event,
            conversation_id,
            message_limit,
            cached_messages,
        )

    def connect_to_database(self) -> None:
        """No-op (Redis connection is established by RedisClient)."""
        if not self._redis.is_healthy():
            self._redis.connect_to_database()

    def _require_redis(self) -> RedisClient:
        if not self._redis.is_healthy():
            raise RuntimeError("Redis is not connected.")
        return self._redis

    def _conversation_key(self, conversation_id: str) -> str:
        return self._require_redis().build_key("chat", "conversation", conversation_id)

    def _user_current_key(self, user_id: str) -> str:
        return self._require_redis().build_key("chat", "user", user_id, "current")

    def _ttl_seconds(self) -> Optional[int]:
        return self._require_redis()._ttl_seconds()

    def _touch_user_current(self, user_id: str, conversation_id: str) -> None:
        ttl = self._ttl_seconds()
        self._require_redis().client.set(
            self._user_current_key(user_id), conversation_id, ex=ttl
        )

    def _get_user_current(self, user_id: str) -> Optional[str]:
        val = self._require_redis().client.get(self._user_current_key(user_id))
        return str(val) if val else None

    def _delete_conversation_key(self, conversation_id: str) -> None:
        self._require_redis().client.delete(self._conversation_key(conversation_id))

    def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        max_messages: Optional[int] = 200,
        **extra: Any,
    ) -> None:
        """Append a message to the active conversation stored in Redis."""
        now = datetime.now(timezone.utc)

        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "created_at": extra.pop("created_at", now),
            **extra,
        }

        # Enforce single active conversation per user:
        # - If user has no current conversation, bind to this one.
        # - If user has a different current conversation, treat this id as the new one
        #   (and delete old) so storage remains 1 conversation/user.
        if user_id is not None:
            current_id = self._get_user_current(user_id)
            if current_id and current_id != conversation_id:
                self._delete_conversation_key(current_id)

        conversation = self.get_conversation(conversation_id, user_id=user_id)
        if not conversation:
            if user_id is None:
                # Best-effort: callers in this codebase normally create the conversation
                # in the request layer (where user_id is known). If they didn't, we still
                # initialize a conversation but cannot enforce 1 conversation/user.
                conversation = {
                    "_id": conversation_id,
                    "user_id": None,
                    "title": "New Chat",
                    "messages": [],
                    "message_count": 0,
                    "created_at": now,
                    "updated_at": now,
                }
            else:
                conversation = self.create_conversation(conversation_id, user_id=user_id)

        messages = list(conversation.get("messages") or [])
        messages.append(message)
        if isinstance(max_messages, int) and max_messages > 0:
            messages = messages[-max_messages:]

        title = str(conversation.get("title") or "New Chat")
        if role == "user" and (not title or title == "New Chat"):
            normalized = " ".join((content or "").split()).strip()
            if normalized:
                title = normalized[:60]

        updated = {
            **conversation,
            "title": title or "New Chat",
            "updated_at": now,
            "message_count": int(conversation.get("message_count") or 0) + 1,
            "messages": messages,
        }

        if self._conversation_cache:
            self._conversation_cache.cache_conversation(updated)
            self._log_cache(
                "write",
                conversation_id=conversation_id,
                cached_messages=len(messages),
            )
        else:
            # Fallback: still write to Redis even without the cache wrapper.
            ttl = self._ttl_seconds()
            self._require_redis().client.set(
                self._conversation_key(conversation_id),
                json.dumps(self._require_redis()._serialize(updated), ensure_ascii=False),
                ex=ttl,
            )

        effective_user_id = user_id or updated.get("user_id")
        if effective_user_id is not None:
            self._touch_user_current(str(effective_user_id), conversation_id)

    def get_context(
        self,
        conversation_id: str,
        *,
        message_limit: int = 10,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve recent messages from the Redis-backed conversation."""
        if user_id is not None:
            current_id = self._get_user_current(user_id)
            if current_id and current_id != conversation_id:
                return []

        conversation = self.get_conversation(conversation_id, user_id=user_id)
        if not conversation:
            return []
        messages = list(conversation.get("messages") or [])
        if message_limit <= 0:
            return messages
        return messages[-message_limit:]

    def create_conversation(
        self, conversation_id: str, *, user_id: str
    ) -> dict[str, Any]:
        """Create (or replace) the single active conversation for a user in Redis."""
        now = datetime.now(timezone.utc)

        current_id = self._get_user_current(user_id)
        if current_id and current_id != conversation_id:
            self._delete_conversation_key(current_id)

        conversation: dict[str, Any] = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "New Chat",
            "messages": [],
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        if self._conversation_cache:
            self._conversation_cache.cache_conversation(conversation)
        else:
            ttl = self._ttl_seconds()
            self._require_redis().client.set(
                self._conversation_key(conversation_id),
                json.dumps(
                    self._require_redis()._serialize(conversation), ensure_ascii=False
                ),
                ex=ttl,
            )

        self._touch_user_current(user_id, conversation_id)
        return conversation

    def list_conversations(
        self, *, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Return at most 1 conversation summary (single active conversation per user)."""
        current_id = self._get_user_current(user_id)
        if not current_id:
            return []
        conversation = self.get_conversation(current_id, user_id=user_id)
        if not conversation:
            return []
        messages = list(conversation.get("messages") or [])
        preview = messages[-1].get("content", "") if messages else ""
        return [
            {
                "conversation_id": conversation.get("_id") or current_id,
                "title": conversation.get("title", "New Chat"),
                "preview": (preview or "")[:140],
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "message_count": int(conversation.get("message_count", 0) or 0),
            }
        ][: max(1, int(limit or 1))]

    def get_conversation(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Return a conversation document by id, optionally scoped to the user's active conversation."""
        if self._conversation_cache:
            cached = self._conversation_cache.get_conversation(conversation_id)
            if isinstance(cached, dict):
                if user_id is None or str(cached.get("user_id") or "") == str(user_id):
                    return cached

        if user_id is not None:
            current_id = self._get_user_current(user_id)
            if current_id and current_id != conversation_id:
                return None

        try:
            data = self._require_redis().client.get(
                self._conversation_key(conversation_id)
            )
            if not data:
                return None
            conversation = json.loads(data)
            if user_id is not None and str(conversation.get("user_id") or "") != str(user_id):
                return None
            return conversation
        except Exception as e:
            logger.error(
                "conversation_redis get error conversation_id=%s error=%s",
                conversation_id,
                e,
            )
            return None

    def conversation_exists(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> bool:
        """Return True when the conversation exists (and is the user's active one if user_id is provided)."""
        if user_id is not None:
            current_id = self._get_user_current(user_id)
            if current_id != conversation_id:
                return False
        return bool(self.get_conversation(conversation_id, user_id=user_id))

    def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        """Return the single active conversation id for a user (if any)."""
        return self._get_user_current(user_id)

    def search_conversations(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        # With 1 active conversation per user, search is a lightweight title filter.
        query_text = " ".join((query or "").split()).strip()
        if not query_text:
            return self.list_conversations(user_id=user_id, limit=limit)

        conversations = self.list_conversations(user_id=user_id, limit=max(int(limit or 1), 1))

        exact_pattern = re.compile(
            rf"^{re.escape(query_text)}$",
            flags=re.IGNORECASE,
        )
        exact_matches = [
            conversation
            for conversation in conversations
            if exact_pattern.match(str(conversation.get("title") or "").strip())
        ]
        if exact_matches:
            return exact_matches[:limit]

        # Lightweight fallback: substring match on titles (regex, case-insensitive).
        contains_pattern = re.compile(
            re.escape(query_text),
            flags=re.IGNORECASE,
        )
        contains_matches = [
            conversation
            for conversation in conversations
            if contains_pattern.search(str(conversation.get("title") or "").strip())
        ]
        return contains_matches[:limit]

    def delete_conversation(self, conversation_id: str, *, user_id: str) -> bool:
        """Delete the active conversation for a user (hard delete from Redis)."""
        current_id = self._get_user_current(user_id)
        if current_id != conversation_id:
            return False

        deleted = (
            self._require_redis().client.delete(self._conversation_key(conversation_id))
            > 0
        )
        self._require_redis().client.delete(self._user_current_key(user_id))

        if self._conversation_cache:
            self._conversation_cache.invalidate_conversation(conversation_id)

        return bool(deleted)

    def close(self) -> None:
        """Close cache connection (Redis handled by RedisClient)."""
        if self._conversation_cache:
            self._conversation_cache.close()
            self._conversation_cache = None
