from datetime import datetime, timezone
from typing import Any, Optional

from src.persistence.dynamodb_client import get_dynamodb_client


class ConversationRepository:
    """Repository for conversation operations using DynamoDB."""

    def __init__(self, dynamodb_client=None):
        self._client = dynamodb_client or get_dynamodb_client()

    def _table(self) -> str:
        return "conversations"

    def _pk(self, conversation_id: str) -> dict:
        return {"conversation_id": {"S": conversation_id}}

    async def get_by_id(self, id: str) -> Optional[dict]:
        return await self._client.get_item(self._table(), self._pk(id))

    async def create(self, doc: dict) -> str:
        return doc.get("conversation_id") or doc.get("_id", "")

    async def update(self, id: str, fields: dict) -> bool:
        fields = {k: v for k, v in fields.items() if v is not None}
        if not fields:
            return False
        try:
            await self._client.update_item(self._table(), self._pk(id), fields)
            return True
        except Exception:
            return False

    async def delete(self, id: str) -> bool:
        await self._client.delete_item(self._table(), self._pk(id))
        return True

    async def find_one(self, query: dict) -> Optional[dict]:
        return None

    async def find_many(self, query: dict, **kwargs) -> list[dict]:
        return []

    async def insert_one(self, doc: dict) -> Any:
        conv_id = doc.get("conversation_id") or doc.get("_id")
        item = {
            "conversation_id": conv_id,
            "user_id": doc.get("user_id", ""),
            "title": doc.get("title", "New Chat"),
            "messages": doc.get("messages", []),
            "message_count": doc.get("message_count", 0),
            "last_message_preview": doc.get("last_message_preview", ""),
            "created_at": doc.get("created_at", datetime.now(timezone.utc).isoformat()),
            "updated_at": doc.get("updated_at", datetime.now(timezone.utc).isoformat()),
        }
        item = {k: v for k, v in item.items() if v != "" and v is not None}
        await self._client.put_item(self._table(), item)
        return conv_id

    async def update_one(self, query: dict, update: dict, upsert: bool = False) -> Any:
        return None

    async def delete_one(self, query: dict) -> Any:
        return None

    async def create_conversation(self, conversation_id: str, user_id: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        conversation = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "title": "New Chat",
            "messages": [],
            "message_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        await self._client.put_item(self._table(), conversation)
        return conversation

    async def get_conversation(
        self, conversation_id: str, user_id: Optional[str] = None
    ) -> Optional[dict]:
        return await self._client.get_item(self._table(), self._pk(conversation_id))

    async def list_conversations(self, user_id: str, limit: int = 50) -> list[dict]:
        items = await self._client.query(
            self._table(),
            index_name="user-updated-index",
            key_condition="user_id = :uid",
            expression_values={":uid": {"S": user_id}},
            scan_index_forward=False,
            limit=limit,
        )
        return items

    async def get_latest(self, user_id: str) -> Optional[dict]:
        items = await self.list_conversations(user_id, limit=1)
        return items[0] if items else None

    async def append_message(
        self,
        conversation_id: str,
        message: dict,
        user_id: Optional[str] = None,
        max_messages: int = 200,
    ) -> None:
        # Get current conversation
        conv = await self.get_conversation(conversation_id, user_id)
        now = datetime.now(timezone.utc).isoformat()

        if conv:
            messages = conv.get("messages", [])
            if isinstance(messages, list):
                messages.append(message)
                if max_messages and len(messages) > max_messages:
                    messages = messages[-max_messages:]
            else:
                messages = [message]

            preview = message.get("content", "")[:140] if message.get("content") else ""
            count = int(conv.get("message_count") or 0) + 1

            await self._client.update_item(
                self._table(),
                self._pk(conversation_id),
                {
                    "messages": messages,
                    "message_count": count,
                    "last_message_preview": preview,
                    "updated_at": now,
                },
            )
        else:
            # Create new conversation
            await self.create_conversation(conversation_id, user_id or "")
            await self.append_message(conversation_id, message, user_id, max_messages)

    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        # Enforce ownership: read first, verify user_id, then delete
        conv = await self.get_conversation(conversation_id)
        if not conv or conv.get("user_id") != user_id:
            return False
        await self._client.delete_item(
            self._table(),
            self._pk(conversation_id),
        )
        return True

    async def update_title(self, conversation_id: str, title: str) -> None:
        await self._client.update_item(
            self._table(),
            self._pk(conversation_id),
            {"title": title},
        )

    async def exists(self, conversation_id: str, user_id: Optional[str] = None) -> bool:
        conv = await self.get_conversation(conversation_id, user_id)
        return conv is not None

    def create_index(self) -> None:
        # Indexes created via Terraform, no-op here
        pass
