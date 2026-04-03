"""
DynamoDB-backed ConversationHandler for Phase 03.
Delegates persistence to ConversationRepository while keeping
cache for read optimization.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from src.conversation.conversation_cache import ConversationCache
from src.conversation.conversation_constants import DEFAULT_LIMIT, DEFAULT_TITLE
from src.database.repositories.conversation_handler import ConversationRepository

logger = logging.getLogger(__name__)


class DynamoDBConversationHandler:
    """
    Handler for storing conversations in DynamoDB with optional caching.
    Provides search functionality with regex.
    All methods are async to safely integrate with ASGI/FastAPI.
    """

    def __init__(
        self,
        conversation_repo: ConversationRepository,
        conversation_cache: Optional[ConversationCache] = None,
    ):
        self._repo = conversation_repo
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

    async def create_conversation(
        self, conversation_id: str, *, user_id: str
    ) -> dict[str, Any]:
        """Create a new empty conversation for a user."""
        import uuid

        conv_id = conversation_id or str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conversation = {
            "conversation_id": conv_id,
            "user_id": user_id,
            "title": DEFAULT_TITLE,
            "messages": [],
            "message_count": 0,
            "last_message_preview": "",
            "created_at": now,
            "updated_at": now,
        }
        await self._repo.insert_one(conversation)
        return conversation

    async def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        max_messages: int = 200,
        **extra: Any,
    ) -> None:
        """Append message to conversation, creating it if needed."""
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "created_at": extra.pop("created_at", now_iso),
            **extra,
        }

        await self._repo.append_message(
            conversation_id=conversation_id,
            message=message,
            user_id=user_id,
            max_messages=max_messages,
        )

        if role == "user":
            await self._update_title_from_first_message(conversation_id, content)

        if self._conversation_cache:
            await self._write_through_cache(
                conversation_id, message, max_messages, now, user_id
            )

    async def _write_through_cache(
        self,
        conversation_id: str,
        message: dict,
        max_messages: int,
        now: datetime,
        user_id: Optional[str],
    ) -> None:
        """Write-through cache sync."""
        if not self._conversation_cache:
            return
        cached = self._conversation_cache.get_conversation(conversation_id)
        cached_messages = cached.get("messages") if isinstance(cached, dict) else None
        if isinstance(cached_messages, list):
            is_complete = (
                bool(cached.get("is_complete")) if isinstance(cached, dict) else False
            )
            cached_messages.append(message)
            if max_messages is not None and max_messages > 0:
                cached_messages = cached_messages[-max_messages:]
            self._conversation_cache.cache_conversation(
                {
                    "_id": conversation_id,
                    "user_id": cached.get("user_id"),
                    "title": cached.get("title", DEFAULT_TITLE),
                    "created_at": cached.get("created_at"),
                    "updated_at": now,
                    "messages": cached_messages,
                    "is_complete": is_complete,
                }
            )
            self._log_cache(
                "write_through",
                conversation_id=conversation_id,
                cached_messages=len(cached_messages),
            )
        else:
            self._conversation_cache.invalidate_conversation(conversation_id)

    async def get_context(
        self,
        conversation_id: str,
        *,
        message_limit: int = 10,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve recent messages from conversation."""
        # Try cache first
        if user_id is None and self._conversation_cache and message_limit > 0:
            cached = self._conversation_cache.get_conversation(conversation_id)
            cached_messages = (
                cached.get("messages") if isinstance(cached, dict) else None
            )
            is_complete = (
                bool(cached.get("is_complete")) if isinstance(cached, dict) else False
            )
            if (
                isinstance(cached_messages, list)
                and len(cached_messages) >= message_limit
            ):
                self._log_cache(
                    "hit",
                    conversation_id=conversation_id,
                    message_limit=message_limit,
                    cached_messages=len(cached_messages),
                )
                return cached_messages[-message_limit:]
            if isinstance(cached_messages, list) and is_complete:
                self._log_cache(
                    "hit_complete",
                    conversation_id=conversation_id,
                    message_limit=message_limit,
                    cached_messages=len(cached_messages),
                )
                return cached_messages[-message_limit:]
            self._log_cache(
                "miss",
                conversation_id=conversation_id,
                message_limit=message_limit,
                cached_messages=(
                    len(cached_messages) if isinstance(cached_messages, list) else None
                ),
            )

        # Read from DynamoDB
        conv = await self._repo.get_conversation(conversation_id, user_id)
        if not conv:
            return []

        messages = conv.get("messages", [])
        if isinstance(messages, list):
            messages = messages[-message_limit:] if message_limit > 0 else messages
        else:
            messages = []

        # Cache if no user_id filter
        if user_id is None and self._conversation_cache and message_limit > 0:
            self._conversation_cache.cache_conversation(
                {"_id": conversation_id, "messages": messages, "is_complete": True}
            )
        return messages

    async def list_conversations(
        self, *, user_id: str, limit: int = DEFAULT_LIMIT
    ) -> list[dict[str, Any]]:
        """List conversation summaries for a user, newest first."""
        conversations = await self._repo.list_conversations(user_id, limit)
        results = []
        for conv in conversations:
            messages = conv.get("messages", [])
            if isinstance(messages, list) and messages:
                preview = messages[-1].get("content", "") if messages else ""
            else:
                preview = conv.get("last_message_preview", "")
            results.append(
                {
                    "conversation_id": conv.get("conversation_id"),
                    "title": conv.get("title", DEFAULT_TITLE),
                    "preview": preview[:140] if preview else "",
                    "created_at": conv.get("created_at"),
                    "updated_at": conv.get("updated_at"),
                    "message_count": int(conv.get("message_count", 0)),
                }
            )
        return results

    async def get_conversation(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Return a conversation document by id, optionally scoped to a user."""
        return await self._repo.get_conversation(conversation_id, user_id)

    async def conversation_exists(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> bool:
        """Return True when the conversation exists."""
        return await self._repo.exists(conversation_id, user_id)

    async def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        """Return the most recently updated conversation id for a user."""
        conv = await self._repo.get_latest(user_id)
        return conv.get("conversation_id") if conv else None

    async def search_conversations(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search conversations by title regex match."""
        query_text = " ".join((query or "").split()).strip()
        if not query_text:
            return await self.list_conversations(user_id=user_id, limit=limit)

        conversations = await self.list_conversations(
            user_id=user_id, limit=max(limit, 50)
        )

        pattern = re.compile(re.escape(query_text), flags=re.IGNORECASE)
        matched = [
            conv
            for conv in conversations
            if pattern.search(str(conv.get("title") or "").strip())
        ]
        return matched[:limit]

    async def delete_conversation(self, conversation_id: str, *, user_id: str) -> bool:
        """Delete a conversation document for a user (hard delete)."""
        result = await self._repo.delete_conversation(conversation_id, user_id)
        if self._conversation_cache:
            self._conversation_cache.invalidate_conversation(conversation_id)
        return result

    async def _update_title_from_first_message(
        self, conversation_id: str, content: str
    ) -> None:
        """Use the first user message as the conversation title."""
        conv = await self._repo.get_conversation(conversation_id)
        if not conv:
            return
        title = str(conv.get("title") or "").strip()
        if title and title != DEFAULT_TITLE:
            return
        messages = conv.get("messages", [])
        if not isinstance(messages, list):
            return
        user_messages = [
            m for m in messages if m.get("role") == "user" and m.get("content")
        ]
        if len(user_messages) != 1:
            return
        normalized = " ".join(content.split()).strip()
        if not normalized:
            return
        await self._repo.update_title(conversation_id, normalized[:60])

    def close(self) -> None:
        """Close database and cache connections."""
        if self._conversation_cache:
            self._conversation_cache.close()

    def create_index(self) -> None:
        """No-op: DynamoDB indexes are created via Terraform."""
        pass
