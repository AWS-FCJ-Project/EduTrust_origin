from pydantic import BaseModel


class TutorAgentRequest(BaseModel):
    question: str


class TutorAgentResponse(BaseModel):
    answer: str
