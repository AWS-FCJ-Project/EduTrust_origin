from datetime import datetime

from pydantic import BaseModel, Field


class ConversationMessageSchema(BaseModel):
    role: str
    content: str
    created_at: datetime | None = None


class ConversationSummarySchema(BaseModel):
    conversation_id: str
    title: str
    preview: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
    message_count: int = 0


class ConversationResponseSchema(BaseModel):
    conversation_id: str
    title: str = Field(default="New Chat")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    messages: list[ConversationMessageSchema] = Field(default_factory=list)
