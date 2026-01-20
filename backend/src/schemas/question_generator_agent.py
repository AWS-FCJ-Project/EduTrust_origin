from pydantic import BaseModel


class QuestionGeneratorAgentRequest(BaseModel):
    question: str


class QuestionGeneratorAgentResponse(BaseModel):
    answer: str
