from pydantic import BaseModel


class LiteratureHistoryAgentRequest(BaseModel): 
    question: str


class LiteratureHistoryAgentResponse(BaseModel):
    answer: str
