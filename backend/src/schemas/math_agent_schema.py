from pydantic import BaseModel


class MathAgentRequest(BaseModel):
    question: str


class MathAgentResponse(BaseModel):
    answer: str
