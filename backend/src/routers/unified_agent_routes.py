from typing import Annotated

from fastapi import APIRouter, Depends
from backend.src.auth.dependencies import get_current_user
from backend.src.crew import tools
from backend.src.crew.orchestrator import ask, ask_stream_with_tool_calls
from backend.src.schemas.unified_agent_schema import (
    UnifiedAgentRequestSchema,
    UnifiedAgentResponseSchema,
)
from backend.src.streaming import sse_json, sse_response

router = APIRouter(prefix="/unified-agent", tags=["Unified Agent"])


@router.post("/ask", response_model=UnifiedAgentResponseSchema)
async def ask_agent(
    request: UnifiedAgentRequestSchema, email: Annotated[str, Depends(get_current_user)]
) -> UnifiedAgentResponseSchema:
    answer = await ask(
        question=request.question, conversation_id=request.conversation_id
    )
    return UnifiedAgentResponseSchema(
        answer=answer, conversation_id=request.conversation_id
    )


@router.post("/ask/streaming")
async def ask_agent_streaming(request: UnifiedAgentRequestSchema):
    async def generate():
        try:
            async for event in ask_stream_with_tool_calls(
                question=request.question, conversation_id=request.conversation_id
            ):
                yield sse_json({"type": event.type, "content": event.content})

            yield sse_json({"type": "complete"})
        except Exception as e:
            yield sse_json({"type": "error", "content": str(e)})

    return sse_response(generate())
