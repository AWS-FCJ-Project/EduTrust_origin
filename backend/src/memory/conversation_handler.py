from typing import Any, Optional

import pymongo
from src.app_config import app_config
from src.memory.conversation_cache import ConversationCache


class ConversationHandler:
    def __init__(
        self,
        connection_string: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = "conversations",
        conversation_cache: Optional[ConversationCache] = None,
    ):
        self.client: Optional[pymongo.MongoClient] = None
        self.db: Optional[pymongo.database.Database] = None
        self.collection: Optional[pymongo.collection.Collection] = None

        self.connection_string = connection_string or app_config.MONGO_URI
        self.username = username or app_config.MONGO_USERNAME
        self.password = password or app_config.MONGO_PASSWORD
        self.db_name = db_name or app_config.MONGO_DB_NAME
        self.collection_name = collection_name
        self._conversation_cache = conversation_cache

    def connect_to_database(self):
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
        collection = self._require_collection()

        push_value: dict[str, Any] = {
            "$each": [{"role": role, "content": content, **extra}]
        }
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
            self._conversation_cache.invalidate_conversation(conversation_id)

    def get_context(self, conversation_id: str, *, k: int = 10) -> list[dict[str, Any]]:
        if self._conversation_cache and isinstance(k, int) and k > 0:
            cached = self._conversation_cache.get_conversation(conversation_id)
            cached_messages = (
                cached.get("messages") if isinstance(cached, dict) else None
            )
            if isinstance(cached_messages, list):
                return cached_messages[-k:]

        collection = self._require_collection()
        projection: dict[str, Any]
        if isinstance(k, int) and k > 0:
            projection = {"messages": {"$slice": -k}}
        else:
            projection = {"messages": 1}

        doc = collection.find_one({"_id": conversation_id}, projection)
        if not doc:
            return []

        messages = list(doc.get("messages", []))
        if self._conversation_cache and isinstance(k, int) and k > 0 and messages:
            self._conversation_cache.cache_conversation(
                {"_id": conversation_id, "messages": messages}
            )
        return messages

    def close(self) -> None:
        if self.client is not None:
            self.client.close()
        self.client = None
        self.db = None
        self.collection = None
        if self._conversation_cache:
            self._conversation_cache.close()
            self._conversation_cache = None
