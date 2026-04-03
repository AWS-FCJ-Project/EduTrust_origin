from typing import Any

from pydantic import BaseModel, ConfigDict
from src.conversation.conversation_handler_dynamodb import DynamoDBConversationHandler


class UnifiedAgentRequestSchema(BaseModel):
    question: str
    conversation_id: str


class UnifiedAgentResponseSchema(BaseModel):
    answer: str
    conversation_id: str


class MainAgentDeps(BaseModel):
    conversation_id: str
    conversation_handler: DynamoDBConversationHandler

    model_config = ConfigDict(arbitrary_types_allowed=True)


class MainAgentStreamEvent(BaseModel):
    type: str
    content: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)
