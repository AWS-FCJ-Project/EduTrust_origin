from pydantic import BaseModel


class GenerateQuestionsRequest(BaseModel):
    prompt: str
    num_questions: int = 5


class GenerateQuestionsResponse(BaseModel):
    raw: str
