from fastapi import APIRouter

from src.crew import tools
from src.crew.orchestrator import ask
from src.schemas.unified_agent_schema import (
    UnifiedAgentRequestSchema,
    UnifiedAgentResponseSchema,
)

router = APIRouter(prefix="/unified-agent", tags=["Unified Agent"])


@router.post("/ask", response_model=UnifiedAgentResponseSchema)
async def ask_agent(request: UnifiedAgentRequestSchema) -> UnifiedAgentResponseSchema:
    answer = await ask(
        question=request.question, conversation_id=request.conversation_id
    )
    return UnifiedAgentResponseSchema(
        answer=answer, conversation_id=request.conversation_id
    )
