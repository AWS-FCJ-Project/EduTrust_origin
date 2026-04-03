from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import delete, func, select, update

from src.db import session_scope
from src.memory.conversation_cache import ConversationCache
from src.models import Conversation, Message


class ConversationHandler:
    """Async conversation storage backed by RDS (SQLAlchemy)."""

    def __init__(
        self,
        *,
        conversation_cache: Optional[ConversationCache] = None,
    ):
        self._conversation_cache = conversation_cache

    def connect_to_database(self) -> None:
        # RDS connections are managed per-request/session in SQLAlchemy.
        return None

    def close(self) -> None:
        if self._conversation_cache:
            self._conversation_cache.close()
            self._conversation_cache = None

    async def create_conversation(self, conversation_id: str, *, user_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        async with session_scope() as session:
            existing = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
            row = existing.scalar_one_or_none()
            if row is None:
                session.add(
                    Conversation(
                        id=conversation_id,
                        user_id=user_id,
                        title="New Chat",
                        created_at=now,
                        updated_at=now,
                        message_count=0,
                    )
                )
        return {
            "_id": conversation_id,
            "user_id": user_id,
            "title": "New Chat",
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }

    async def conversation_exists(self, conversation_id: str, *, user_id: Optional[str] = None) -> bool:
        async with session_scope() as session:
            q = select(func.count()).select_from(Conversation).where(Conversation.id == conversation_id)
            if user_id is not None:
                q = q.where(Conversation.user_id == user_id)
            res = await session.execute(q)
            return bool(int(res.scalar() or 0) > 0)

    async def get_conversation(self, conversation_id: str, *, user_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        async with session_scope() as session:
            q = select(Conversation).where(Conversation.id == conversation_id)
            if user_id is not None:
                q = q.where(Conversation.user_id == user_id)
            res = await session.execute(q)
            row = res.scalar_one_or_none()
            if row is None:
                return None
            return {
                "_id": row.id,
                "user_id": row.user_id,
                "title": row.title,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "message_count": int(row.message_count or 0),
            }

    async def get_latest_conversation_id(self, user_id: str) -> Optional[str]:
        async with session_scope() as session:
            res = await session.execute(
                select(Conversation.id)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .limit(1)
            )
            row = res.first()
            return str(row[0]) if row and row[0] else None

    async def list_conversations(self, *, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        async with session_scope() as session:
            res = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .limit(int(limit or 50))
            )
            conversations: list[dict[str, Any]] = []
            for row in res.scalars().all():
                # Preview from last message
                last_msg_res = await session.execute(
                    select(Message.content)
                    .where(Message.conversation_id == row.id)
                    .order_by(Message.created_at.desc())
                    .limit(1)
                )
                preview_row = last_msg_res.first()
                preview = str(preview_row[0]) if preview_row and preview_row[0] else ""
                conversations.append(
                    {
                        "conversation_id": row.id,
                        "title": row.title or "New Chat",
                        "preview": preview[:140],
                        "created_at": row.created_at,
                        "updated_at": row.updated_at,
                        "message_count": int(row.message_count or 0),
                    }
                )
            return conversations

    async def search_conversations(self, *, user_id: str, query: str, limit: int = 50) -> list[dict[str, Any]]:
        query_text = " ".join((query or "").split()).strip()
        if not query_text:
            return await self.list_conversations(user_id=user_id, limit=limit)

        conversations = await self.list_conversations(user_id=user_id, limit=max(int(limit or 50), 50))
        exact_pattern = re.compile(rf"^{re.escape(query_text)}$", flags=re.IGNORECASE)
        exact_matches = [c for c in conversations if exact_pattern.match(str(c.get("title") or "").strip())]
        if exact_matches:
            return exact_matches[:limit]

        contains_pattern = re.compile(re.escape(query_text), flags=re.IGNORECASE)
        contains_matches = [c for c in conversations if contains_pattern.search(str(c.get("title") or "").strip())]
        return contains_matches[:limit]

    async def add_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        user_id: Optional[str] = None,
        max_messages: Optional[int] = 200,
        **extra: Any,
    ) -> None:
        now = datetime.now(timezone.utc)
        created_at = extra.pop("created_at", now)

        async with session_scope() as session:
            convo_res = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
            convo = convo_res.scalar_one_or_none()
            if convo is None:
                session.add(
                    Conversation(
                        id=conversation_id,
                        user_id=user_id or "",
                        title="New Chat",
                        created_at=now,
                        updated_at=now,
                        message_count=0,
                    )
                )
                await session.flush()
                convo_res = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
                convo = convo_res.scalar_one()

            session.add(
                Message(
                    conversation_id=conversation_id,
                    role=str(role),
                    content=str(content),
                    created_at=created_at,
                )
            )

            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=now, message_count=(Conversation.message_count + 1))
            )

            # Update title from first user message.
            if role == "user":
                await self._update_title_from_first_message(session, conversation_id, content)

            if max_messages is not None and max_messages > 0:
                # Trim older messages beyond max_messages
                count_res = await session.execute(
                    select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
                )
                count = int(count_res.scalar() or 0)
                if count > max_messages:
                    # delete oldest (count - max_messages)
                    to_delete = count - max_messages
                    oldest_res = await session.execute(
                        select(Message.id)
                        .where(Message.conversation_id == conversation_id)
                        .order_by(Message.created_at.asc())
                        .limit(to_delete)
                    )
                    ids = [row[0] for row in oldest_res.all() if row and row[0]]
                    if ids:
                        await session.execute(delete(Message).where(Message.id.in_(ids)))

        if self._conversation_cache:
            # Invalidate cache; next get_context will repopulate.
            self._conversation_cache.invalidate_conversation(conversation_id)

    async def _update_title_from_first_message(self, session, conversation_id: str, content: str) -> None:
        convo_res = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
        convo = convo_res.scalar_one_or_none()
        if convo is None:
            return
        title = str(convo.title or "").strip()
        if title and title != "New Chat":
            return

        # Only set title if there is exactly one user message.
        msg_res = await session.execute(
            select(Message.role, Message.content)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(3)
        )
        msgs = msg_res.all()
        user_msgs = [m for m in msgs if (m[0] == "user" and m[1])]
        if len(user_msgs) != 1:
            return

        normalized = " ".join(str(content).split()).strip()
        if not normalized:
            return

        await session.execute(
            update(Conversation).where(Conversation.id == conversation_id).values(title=normalized[:60])
        )

    async def get_context(
        self,
        conversation_id: str,
        *,
        message_limit: int = 10,
        user_id: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        if message_limit is None:
            message_limit = 10
        message_limit = int(message_limit)
        if message_limit <= 0:
            return []

        if self._conversation_cache:
            cached = self._conversation_cache.get_conversation(conversation_id)
            if cached and isinstance(cached.get("messages"), list):
                return list(cached["messages"])[-message_limit:]

        async with session_scope() as session:
            convo_q = select(Conversation).where(Conversation.id == conversation_id)
            if user_id is not None:
                convo_q = convo_q.where(Conversation.user_id == user_id)
            convo_res = await session.execute(convo_q)
            if convo_res.scalar_one_or_none() is None:
                return []

            msg_res = await session.execute(
                select(Message.role, Message.content, Message.created_at)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.desc())
                .limit(message_limit)
            )
            rows = msg_res.all()
            messages = [
                {"role": r[0], "content": r[1], "created_at": r[2]}
                for r in reversed(rows)
            ]

            if self._conversation_cache:
                self._conversation_cache.cache_conversation(
                    {"_id": conversation_id, "messages": messages}
                )
            return messages

    async def delete_conversation(self, conversation_id: str, *, user_id: str) -> bool:
        async with session_scope() as session:
            res = await session.execute(
                delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            )
            deleted = bool(getattr(res, "rowcount", 0) or 0)

        if self._conversation_cache:
            self._conversation_cache.invalidate_conversation(conversation_id)
        return deleted

