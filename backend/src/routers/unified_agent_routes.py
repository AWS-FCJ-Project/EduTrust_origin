from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends
from src.agent.unified_agent import UnifiedAgent
from src.auth.dependencies import get_current_user
from src.llm import LLM
from src.schemas.unified_agent_schema import (
    UnifiedAgentRequestSchema,
    UnifiedAgentResponseSchema,
)
from src.state import get_conversation_handler
from src.streaming import Streaming

router = APIRouter(prefix="/unified-agent", tags=["Unified Agent"])


@lru_cache
def get_orchestrator() -> UnifiedAgent:
    return UnifiedAgent(
        llm=LLM(),
        conversation_handler=get_conversation_handler(),
    )


@router.post("/ask", response_model=UnifiedAgentResponseSchema)
async def ask_agent(
    request: UnifiedAgentRequestSchema,
    _email: Annotated[str, Depends(get_current_user)],
    orch: Annotated[UnifiedAgent, Depends(get_orchestrator)],
) -> UnifiedAgentResponseSchema:
    answer = await orch.ask(
        question=request.question, conversation_id=request.conversation_id
    )
    return UnifiedAgentResponseSchema(
        answer=answer, conversation_id=request.conversation_id
    )


@router.post("/ask/streaming")
async def ask_agent_streaming(
    request: UnifiedAgentRequestSchema,
    orch: Annotated[UnifiedAgent, Depends(get_orchestrator)],
):
    async def generate():
        try:
            async for event in orch.ask_stream_with_tool_calls(
                question=request.question, conversation_id=request.conversation_id
            ):
                yield Streaming.sse_json({"type": event.type, "content": event.content})

            yield Streaming.sse_json({"type": "complete"})
        except Exception as e:
            yield Streaming.sse_json({"type": "error", "content": str(e)})

    return Streaming.sse_response(generate())
