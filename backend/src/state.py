from __future__ import annotations
from typing import TYPE_CHECKING

from src.memory.conversation_handler import ConversationHandler

if TYPE_CHECKING:
    from src.rag import RagService

conversation_handler: ConversationHandler | None = None
rag_service: "RagService | None" = None


def get_conversation_handler() -> ConversationHandler:
    if conversation_handler is None:
        raise RuntimeError("ConversationHandler not initialized")
    return conversation_handler


def get_rag_service() -> "RagService":
    if rag_service is None:
        raise RuntimeError("RagService not initialized")
    return rag_service
