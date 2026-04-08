import math
import re
from datetime import datetime, timezone
from typing import Any, Optional

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.config import Config
from botocore.exceptions import ClientError
from src.app_config import app_config
from src.logger import logger
from src.memory.conversation_cache import ConversationCache


def _normalize_table_prefix(prefix: str | None) -> str:
    value = (prefix or "").strip()
    if not value:
        return "edutrust-backend-"
    return value if value.endswith("-") else f"{value}-"


class ConversationHandler:
    """Handler for storing conversations in DynamoDB with optional caching."""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        db_name: Optional[str] = None,
        collection_name: Optional[str] = "conversations",
        conversation_cache: Optional[ConversationCache] = None,
    ):
        """Initialize with DynamoDB config and optional cache."""
        self._dynamodb = None
        self._table = None

        # Keep parameter names for backward compatibility with existing wiring.
        del connection_string, username, password, db_name

        self.collection_name = collection_name or "conversations"
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

    def _log_db_read(self, *, conversation_id: str, message_limit: int) -> None:
        logger.info(
            "conversation_db read conversation_id=%s message_limit=%s",
            conversation_id,
            message_limit,
        )

    def connect_to_database(self) -> None:
        """Connect to DynamoDB (table handle)."""
        try:
            region = (app_config.AWS_REGION or "ap-southeast-1").strip() or "ap-southeast-1"
            prefix = _normalize_table_prefix(app_config.DYNAMODB_TABLE_PREFIX)
            table_name = f"{prefix}{self.collection_name}"

            client_kwargs: dict[str, Any] = {
                "region_name": region,
                "config": Config(retries={"max_attempts": 10, "mode": "standard"}),
            }
            if app_config.AWS_ACCESS_KEY_ID and app_config.AWS_SECRET_ACCESS_KEY:
                client_kwargs.update(
                    {
                        "aws_access_key_id": app_config.AWS_ACCESS_KEY_ID,
                        "aws_secret_access_key": app_config.AWS_SECRET_ACCESS_KEY,
                    }
                )
            endpoint_url = (app_config.DYNAMODB_ENDPOINT_URL or "").strip() or None
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            self._dynamodb = boto3.resource("dynamodb", **client_kwargs)
            self._table = self._dynamodb.Table(table_name)
        except Exception as exc:
            logger.error("Error connecting to DynamoDB: %s", exc)
            self._dynamodb = None
            self._table = None

    def _require_table(self):
        """Get DynamoDB table handle, connecting if needed."""
        if self._table is None:
            self.connect_to_database()
        if self._table is None:
            raise RuntimeError("DynamoDB table not initialized.")
        return self._table

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _to_iso(dt: datetime | None) -> str | None:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    @staticmethod
    def _from_iso(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return value

    def _deserialize_conversation(self, item: dict[str, Any] | None) -> dict[str, Any] | None:
        if not item:
            return None
        item = dict(item)
        item["created_at"] = self._from_iso(item.get("created_at"))
        item["updated_at"] = self._from_iso(item.get("updated_at"))
        messages = item.get("messages")
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict) and "created_at" in msg:
                    msg["created_at"] = self._from_iso(msg.get("created_at"))
        return item

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
        """Append message to conversation, creating it if needed."""
        table = self._require_table()
        now = self._now()

        message: dict[str, Any] = {
            "role": role,
            "content": content,
            "created_at": extra.pop("created_at", now),
            **extra,
        }
        message_serialized = dict(message)
        if isinstance(message_serialized.get("created_at"), datetime):
            message_serialized["created_at"] = self._to_iso(message_serialized["created_at"])

        # DynamoDB doesn't support server-side slicing; do a read-modify-write with a cap.
        try:
            existing = table.get_item(Key={"_id": conversation_id}).get("Item")
        except ClientError as exc:
            logger.error("DynamoDB get_item failed: %s", exc)
            existing = None

        if existing is None:
            created = {
                "_id": conversation_id,
                "title": "New Chat",
                "messages": [],
                "message_count": 0,
                "created_at": self._to_iso(now),
                "updated_at": self._to_iso(now),
            }
            if user_id is not None:
                created["user_id"] = user_id
            existing = created

        messages = list(existing.get("messages", []) or [])
        messages.append(message_serialized)
        if max_messages is not None and max_messages > 0:
            messages = messages[-max_messages:]

        message_count = int(existing.get("message_count", 0)) + 1
        update_expr = "SET #messages = :messages, #updated_at = :updated_at, #message_count = :message_count"
        expr_names = {
            "#messages": "messages",
            "#updated_at": "updated_at",
            "#message_count": "message_count",
        }
        expr_values = {
            ":messages": messages,
            ":updated_at": self._to_iso(now),
            ":message_count": message_count,
        }
        if user_id is not None and not existing.get("user_id"):
            update_expr += ", #user_id = :user_id"
            expr_names["#user_id"] = "user_id"
            expr_values[":user_id"] = user_id

        try:
            table.update_item(
                Key={"_id": conversation_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
        except ClientError as exc:
            logger.error("DynamoDB update_item failed: %s", exc)
            return

        if role == "user":
            self._update_title_from_first_message(conversation_id, content)

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
                        "user_id": cached.get("user_id"),
                        "title": cached.get("title", "New Chat"),
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

        table = self._require_table()
        self._log_db_read(conversation_id=conversation_id, message_limit=message_limit)
        try:
            item = table.get_item(Key={"_id": conversation_id}).get("Item")
        except ClientError as exc:
            logger.error("DynamoDB get_item failed: %s", exc)
            item = None

        doc = self._deserialize_conversation(item)
        if not doc:
            return []
        if user_id is not None and str(doc.get("user_id") or "") != str(user_id):
            return []

        messages = list(doc.get("messages", []) or [])
        if user_id is None and self._conversation_cache and message_limit > 0:
            self._conversation_cache.cache_conversation(
                {"_id": conversation_id, "messages": messages, "is_complete": True}
            )
        return messages[-message_limit:] if message_limit > 0 else messages

    def create_conversation(
        self, conversation_id: str, *, user_id: str
    ) -> dict[str, Any]:
        """Create a new empty conversation for a user."""
        table = self._require_table()
        now = self._now()
        conversation = {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "New Chat",
            "messages": [],
            "message_count": 0,
            "created_at": self._to_iso(now),
            "updated_at": self._to_iso(now),
        }
        try:
            table.put_item(
                Item=conversation,
                ConditionExpression="attribute_not_exists(#id)",
                ExpressionAttributeNames={"#id": "_id"},
            )
        except ClientError as exc:
            # If the item already exists, just return the current version.
            if exc.response.get("Error", {}).get("Code") != "ConditionalCheckFailedException":
                logger.error("DynamoDB put_item failed: %s", exc)
            existing = table.get_item(Key={"_id": conversation_id}).get("Item")
            return self._deserialize_conversation(existing) or {"_id": conversation_id, "user_id": user_id, "title": "New Chat", "messages": []}

        return self._deserialize_conversation(conversation) or conversation

    def list_conversations(
        self, *, user_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List conversation summaries for a user, newest first."""
        table = self._require_table()
        # Without a user_id GSI, fall back to a filtered scan and local sort.
        items: list[dict[str, Any]] = []
        start_key = None
        while True:
            scan_kwargs: dict[str, Any] = {
                "FilterExpression": Attr("user_id").eq(user_id),
                "ProjectionExpression": "#id, title, created_at, updated_at, message_count, messages",
                "ExpressionAttributeNames": {"#id": "_id"},
                "Limit": max(limit * 4, 50),
            }
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key
            resp = table.scan(**scan_kwargs)
            batch = resp.get("Items", []) or []
            items.extend(batch)
            start_key = resp.get("LastEvaluatedKey")
            if not start_key or len(items) >= limit * 4:
                break

        conversations: list[dict[str, Any]] = []
        for raw in items:
            doc = self._deserialize_conversation(raw) or raw
            messages = list(doc.get("messages", []) or [])
            preview = ""
            if messages and isinstance(messages[-1], dict):
                preview = str(messages[-1].get("content") or "")
            conversations.append(
                {
                    "conversation_id": doc.get("_id"),
                    "title": doc.get("title", "New Chat"),
                    "preview": preview[:140],
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                    "message_count": int(doc.get("message_count", 0) or 0),
                }
            )

        conversations.sort(
            key=lambda x: x.get("updated_at") or datetime.min,
            reverse=True,
        )
        conversations = conversations[:limit]
        return conversations

    def get_conversation(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> Optional[dict[str, Any]]:
        """Return a conversation document by id, optionally scoped to a user."""
        table = self._require_table()
        try:
            item = table.get_item(Key={"_id": conversation_id}).get("Item")
        except ClientError as exc:
            logger.error("DynamoDB get_item failed: %s", exc)
            return None
        doc = self._deserialize_conversation(item)
        if not doc:
            return None
        if user_id is not None and str(doc.get("user_id") or "") != str(user_id):
            return None
        return doc

    def conversation_exists(
        self, conversation_id: str, *, user_id: Optional[str] = None
    ) -> bool:
        """Return True when the conversation exists."""
        return self.get_conversation(conversation_id, user_id=user_id) is not None

    def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        """Return the most recently updated conversation id for a user."""
        conversations = self.list_conversations(user_id=user_id, limit=1)
        if not conversations:
            return None
        return str(conversations[0].get("conversation_id") or "")

    def search_conversations(
        self,
        *,
        user_id: str,
        query: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
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
        """Delete a conversation document for a user (hard delete)."""
        table = self._require_table()
        existing = self.get_conversation(conversation_id, user_id=user_id)
        if not existing:
            return False

        try:
            table.delete_item(Key={"_id": conversation_id})
        except ClientError as exc:
            logger.error("DynamoDB delete_item failed: %s", exc)
            return False

        if self._conversation_cache:
            self._conversation_cache.invalidate_conversation(conversation_id)

        return True

    def _update_title_from_first_message(
        self, conversation_id: str, content: str
    ) -> None:
        """Use the first user message as the conversation title."""
        table = self._require_table()
        doc = self.get_conversation(conversation_id)
        if not doc:
            return

        title = str(doc.get("title") or "").strip()
        if title and title != "New Chat":
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

        try:
            table.update_item(
                Key={"_id": conversation_id},
                UpdateExpression="SET #title = :title",
                ExpressionAttributeNames={"#title": "title"},
                ExpressionAttributeValues={":title": normalized[:60]},
            )
        except ClientError as exc:
            logger.error("DynamoDB update_item failed: %s", exc)

    def close(self) -> None:
        """Close database and cache connections."""
        self._dynamodb = None
        self._table = None
        if self._conversation_cache:
            self._conversation_cache.close()
            self._conversation_cache = None
