from pydantic import BaseModel


class UnifiedAgentRequestSchema(BaseModel):
    question: str
    conversation_id: str


class UnifiedAgentResponseSchema(BaseModel):
    answer: str
    conversation_id: str
