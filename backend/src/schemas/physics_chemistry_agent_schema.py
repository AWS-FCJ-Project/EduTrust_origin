from pydantic import BaseModel


class PhysicsChemistryAgentRequest(BaseModel):
    question: str


class PhysicsChemistryAgentResponse(BaseModel):
    answer: str
