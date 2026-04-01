import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

import numpy as np
import pymongo
from pymongo import ASCENDING, DESCENDING
from sentence_transformers import SentenceTransformer
from src.conversation.conversation_cache import ConversationCache
from src.database.mongo_client import MongoClient

logger = logging.getLogger(__name__)

DEFAULT_TITLE = "New Chat"
DEFAULT_LIMIT = 50


class ConversationHandler:
    """
    Handler for storing conversations in MongoDB with optional caching.
    Provides search functionality with embeddings.
    """

    def __init__(
        self,
        mongo_client: MongoClient,
        embedding_model: SentenceTransformer,
        conversation_cache: Optional[ConversationCache] = None,
        collection_name: str = "conversations",
    ):
        self._mongo = mongo_client
        self._embedding_model = embedding_model
        self._collection_name = collection_name
        self._conversation_cache = conversation_cache
        self._embedding_cache: dict[str, list[float]] = {}

    @property
    def collection(self) -> pymongo.collection.Collection:
        """Get the conversations collection."""
        return self._mongo.get_collection(self._collection_name)

    def create_index(self) -> None:
        """Create required indexes for efficient queries."""
        self.collection.create_index(
            [("user_id", ASCENDING), ("updated_at", DESCENDING)]
        )

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

    def _log_mongo_read(self, *, conversation_id: str, message_limit: int) -> None:
        logger.info(
            "conversation_mongo read conversation_id=%s message_limit=%s",
            conversation_id,
            message_limit,
        )

    def _require_collection(self) -> pymongo.collection.Collection:
        """Get MongoDB collection."""
        return self.collection

    def add_message(
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
        collection = self._require_collection()
        now = datetime.now(timezone.utc)

        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "created_at": extra.pop("created_at", now),
            **extra,
        }
        push_value: dict[str, Any] = {"$each": [message]}
        if max_messages is not None:
            push_value["$slice"] = -max_messages

        set_on_insert: dict[str, Any] = {
            "_id": conversation_id,
            "title": DEFAULT_TITLE,
            "created_at": now,
        }
        if user_id is not None:
            set_on_insert["user_id"] = user_id

        collection.update_one(
            {"_id": conversation_id},
            {
                "$setOnInsert": set_on_insert,
                "$set": {"updated_at": now},
                "$inc": {"message_count": 1},
                "$push": {"messages": push_value},
            },
            upsert=True,
        )

        if role == "user":
            self._update_title_from_first_message(conversation_id, content)

        if self._conversation_cache:
            self._write_through_cache(
                conversation_id, message, max_messages, now, user_id
            )

    def _write_through_cache(
        self,
        conversation_id: str,
        message: dict,
        max_messages: int,
        now: datetime,
        user_id: Optional[str],
    ) -> None:
        """Write-through cache sync."""
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

    def get_context(
        self,
        conversation_id: str,
        *,
        message_limit: int = 10,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve recent messages from conversation."""
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

        collection = self._require_collection()
        projection: dict[str, Any] = {"messages": 1}
        query: dict[str, Any] = {"_id": conversation_id}
        if user_id is not None:
            query["user_id"] = user_id

        self._log_mongo_read(
            conversation_id=conversation_id, message_limit=message_limit
        )
        doc = collection.find_one(query, projection)
        if not doc:
            return []

        messages = list(doc.get("messages", []))
        if user_id is None and self._conversation_cache and message_limit > 0:
            self._conversation_cache.cache_conversation(
                {"_id": conversation_id, "messages": messages, "is_complete": True}
            )
        return messages[-message_limit:] if message_limit > 0 else messages

    def create_conversation(
        self, conversation_id: str, *, user_id: str
    ) -> dict[str, Any]:
        """Create a new empty conversation for a user."""
        collection = self._require_collection()
        now = datetime.now(timezone.utc)
        conversation = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": DEFAULT_TITLE,
            "messages": [],
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        collection.insert_one(conversation)
        return conversation

    def list_conversations(
        self, *, user_id: str, limit: int = DEFAULT_LIMIT
    ) -> list[dict[str, Any]]:
        """List conversation summaries for a user, newest first."""
        collection = self._require_collection()
        cursor = (
            collection.find(
                {"user_id": user_id},
                {
                    "title": 1,
                    "created_at": 1,
                    "updated_at": 1,
                    "message_count": 1,
                    "messages": {"$slice": -1},
                },
            )
            .sort("updated_at", DESCENDING)
            .limit(limit)
        )

        conversations: list[dict[str, Any]] = []
        for doc in cursor:
            messages = list(doc.get("messages", []))
            preview = messages[-1].get("content", "") if messages else ""
            conversations.append(
                {
                    "conversation_id": doc["_id"],
                    "title": doc.get("title", DEFAULT_TITLE),
                    "preview": preview[:140],
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                    "message_count": int(doc.get("message_count", 0)),
                }
            )
        return conversations

    def get_conversation(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Return a conversation document by id, optionally scoped to a user."""
        collection = self._require_collection()
        query: dict[str, Any] = {"_id": conversation_id}
        if user_id is not None:
            query["user_id"] = user_id
        return collection.find_one(query)

    def conversation_exists(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> bool:
        """Return True when the conversation exists."""
        collection = self._require_collection()
        query: dict[str, Any] = {"_id": conversation_id}
        if user_id is not None:
            query["user_id"] = user_id
        return collection.count_documents(query, limit=1) > 0

    def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        """Return the most recently updated conversation id for a user."""
        collection = self._require_collection()
        doc = collection.find_one(
            {"user_id": user_id},
            {"_id": 1},
            sort=[("updated_at", DESCENDING)],
        )
        return str(doc["_id"]) if doc else None

    def search_conversations(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = DEFAULT_LIMIT,
    ) -> list[dict[str, Any]]:
        """Search conversations by text similarity."""
        query_text = " ".join((query or "").split()).strip()
        if not query_text:
            return self.list_conversations(user_id=user_id, limit=limit)

        conversations = self.list_conversations(user_id=user_id, limit=max(limit, 50))

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

        query_embedding = self.embed_title(query_text)
        if not query_embedding:
            return []

        scored: list[dict[str, Any]] = []
        for conversation in conversations:
            title = str(conversation.get("title") or "")
            embedding = self.embed_title(title)
            score = self.calculate_cosine_similarity(query_embedding, embedding)
            scored.append({**conversation, "similarity": score})

        scored.sort(
            key=lambda item: (
                float(item.get("similarity") or 0.0),
                str(item.get("updated_at") or ""),
            ),
            reverse=True,
        )
        return [item for item in scored if (item.get("similarity") or 0) > 0][:limit]

    def calculate_cosine_similarity(
        self, left: list[float], right: list[float]
    ) -> float:
        """Calculate cosine similarity between two vectors."""
        if not left or not right or len(left) != len(right):
            return 0.0

        left_vec = np.asarray(left, dtype=np.float32)
        right_vec = np.asarray(right, dtype=np.float32)
        denom = float(np.linalg.norm(left_vec) * np.linalg.norm(right_vec))
        if denom <= 0:
            return 0.0
        return float(np.dot(left_vec, right_vec) / denom)

    def embed_title(self, title: str) -> list[float]:
        """Get embedding for title with caching."""
        normalized = " ".join((title or "").split()).strip()
        if not normalized:
            return []
        cached = self._embedding_cache.get(normalized)
        if cached is not None:
            return cached

        model = self._embedding_model
        if model is None:
            return []
        embedding = model.encode(normalized, normalize_embeddings=True).tolist()
        self._embedding_cache[normalized] = embedding
        return embedding

    def delete_conversation(self, conversation_id: str, *, user_id: str) -> bool:
        """Delete a conversation document for a user (hard delete)."""
        collection = self._require_collection()
        result = collection.delete_one({"_id": conversation_id, "user_id": user_id})

        if self._conversation_cache:
            self._conversation_cache.invalidate_conversation(conversation_id)

        return bool(result.deleted_count)

    def _update_title_from_first_message(
        self, conversation_id: str, content: str
    ) -> None:
        """Use the first user message as the conversation title."""
        collection = self._require_collection()
        doc = collection.find_one(
            {"_id": conversation_id},
            {"title": 1, "messages": {"$slice": 2}},
        )
        if not doc:
            return

        title = str(doc.get("title") or "").strip()
        if title and title != DEFAULT_TITLE:
            return

        user_messages = [
            message
            for message in doc.get("messages", [])
            if message.get("role") == "user" and message.get("content")
        ]
        if len(user_messages) != 1:
            return

        normalized = " ".join(content.split()).strip()
        if not normalized:
            return

        collection.update_one(
            {"_id": conversation_id},
            {"$set": {"title": normalized[:60]}},
        )

    def close(self) -> None:
        """Close database and cache connections."""
        if self._mongo:
            self._mongo.close()
        if self._conversation_cache:
            self._conversation_cache.close()
