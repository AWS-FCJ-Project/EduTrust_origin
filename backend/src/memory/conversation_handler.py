from typing import Any, Optional

import pymongo
from src.app_config import app_config
from src.logger import logger
from src.memory.conversation_cache import ConversationCache


class ConversationHandler:
    """Handler for storing conversations in MongoDB with optional caching."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = "conversations",
        conversation_cache: Optional[ConversationCache] = None,
    ):
        """Initialize with MongoDB config and optional cache."""
        self.client: Optional[pymongo.MongoClient] = None
        self.db: Optional[pymongo.database.Database] = None
        self.collection: Optional[pymongo.collection.Collection] = None

        self.connection_string = connection_string or app_config.MONGO_URI
        self.username = username or app_config.MONGO_USERNAME
        self.password = password or app_config.MONGO_PASSWORD
        self.db_name = db_name or app_config.MONGO_DB_NAME
        self.collection_name = collection_name
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

    def _log_mongo_read(self, *, conversation_id: str, message_limit: int) -> None:
        logger.info(
            "conversation_mongo read conversation_id=%s message_limit=%s",
            conversation_id,
            message_limit,
        )

    def connect_to_database(self) -> None:
        """Connect to MongoDB server."""
        try:
            if self.connection_string.startswith("mongodb://"):
                self.client = pymongo.MongoClient(
                    self.connection_string + "/?directConnection=true",
                    username=self.username,
                    password=self.password,
                    retryWrites=False,
                    tlsAllowInvalidHostnames=True,
                )
            else:
                self.client = pymongo.MongoClient(
                    self.connection_string,
                    retryWrites=True,
                    w="majority",
                )
            ping_result = self.client.admin.command("ping")
            print(f"Ping result: {ping_result}")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            print(f"Connected to database: {self.db_name}")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    def _require_collection(self) -> pymongo.collection.Collection:
        """Get MongoDB collection, connecting if needed."""
        if self.collection is None:
            self.connect_to_database()
        if self.collection is None:
            raise RuntimeError("Mongo collection not initialized.")
        return self.collection

    def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        max_messages: Optional[int] = 200,
        **extra: Any,
    ) -> None:
        """Append message to conversation, creating it if needed."""
        collection = self._require_collection()

        # MongoDB is the source of truth: always write there first.
        message: dict[str, Any] = {"role": role, "content": content, **extra}
        push_value: dict[str, Any] = {"$each": [message]}
        if max_messages is not None:
            push_value["$slice"] = -max_messages

        collection.update_one(
            {"_id": conversation_id},
            {
                "$setOnInsert": {"_id": conversation_id},
                "$push": {"messages": push_value},
            },
            upsert=True,
        )

        if self._conversation_cache:
            # Write-through cache: if Redis already has this conversation, keep it
            # in sync so the next get_context() can hit Redis (no immediate Mongo read).
            cached = self._conversation_cache.get_conversation(conversation_id)
            cached_messages = (
                cached.get("messages") if isinstance(cached, dict) else None
            )
            if isinstance(cached_messages, list):
                is_complete = (
                    bool(cached.get("is_complete"))
                    if isinstance(cached, dict)
                    else False
                )
                cached_messages.append(message)
                if max_messages is not None and max_messages > 0:
                    cached_messages = cached_messages[-max_messages:]
                self._conversation_cache.cache_conversation(
                    {
                        "_id": conversation_id,
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
        self, conversation_id: str, *, message_limit: int = 10
    ) -> list[dict[str, Any]]:
        """Retrieve recent messages from conversation."""
        if self._conversation_cache and message_limit > 0:
            # Cache-aside: try Redis first; if cache is missing/short, fall back to Mongo
            # and repopulate Redis (marked is_complete=True).
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
        projection: dict[str, Any]
        projection = {"messages": 1}

        self._log_mongo_read(
            conversation_id=conversation_id, message_limit=message_limit
        )
        doc = collection.find_one({"_id": conversation_id}, projection)
        if not doc:
            return []

        messages = list(doc.get("messages", []))
        if self._conversation_cache and message_limit > 0:
            self._conversation_cache.cache_conversation(
                {"_id": conversation_id, "messages": messages, "is_complete": True}
            )
        return messages[-message_limit:] if message_limit > 0 else messages

    def close(self) -> None:
        """Close database and cache connections."""
        if self.client is not None:
            self.client.close()
        self.client = None
        self.db = None
        self.collection = None
        if self._conversation_cache:
            self._conversation_cache.close()
            self._conversation_cache = None
