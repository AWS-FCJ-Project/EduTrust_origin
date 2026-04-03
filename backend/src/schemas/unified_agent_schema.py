from typing import Any

from pydantic import BaseModel, ConfigDict
from src.memory.conversation_handler import ConversationHandler


class UnifiedAgentRequestSchema(BaseModel):
    question: str


class UnifiedAgentResponseSchema(BaseModel):
    answer: str
    conversation_id: str


class MainAgentDeps(BaseModel):
    conversation_id: str
    conversation_handler: ConversationHandler

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MainAgentStreamEvent(BaseModel):
    type: str
    content: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)
