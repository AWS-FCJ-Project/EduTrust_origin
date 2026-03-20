from typing import Any

from pydantic import BaseModel, ConfigDict
from src.memory.conversation_handler import ConversationHandler


class OrchestratorDeps(BaseModel):
    conversation_id: str
    conversation_handler: ConversationHandler

    model_config = ConfigDict(arbitrary_types_allowed=True)


class OrchestratorStreamEvent(BaseModel):
    type: str
    content: Any

    model_config = ConfigDict(arbitrary_types_allowed=True)
