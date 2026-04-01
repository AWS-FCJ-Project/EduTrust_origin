from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from src.agent.unified_agent import UnifiedAgent
from src.auth.dependencies import get_current_user
from src.llm import LLM
from src.schemas.unified_agent_schema import (UnifiedAgentRequestSchema,
                                              UnifiedAgentResponseSchema)
from src.streaming import Streaming

router = APIRouter(prefix="/unified-agent", tags=["Unified Agent"])


@lru_cache
def get_llm() -> LLM:
    return LLM()


def get_orchestrator(request: Request) -> UnifiedAgent:
    handler = request.app.state.conversation_handler
    return UnifiedAgent(llm=get_llm(), conversation_handler=handler)


@router.post("/ask", response_model=UnifiedAgentResponseSchema)
async def ask_agent(
    request: UnifiedAgentRequestSchema,
    current_user: Annotated[dict, Depends(get_current_user)],
    orch: Annotated[UnifiedAgent, Depends(get_orchestrator)],
) -> UnifiedAgentResponseSchema:
    handler = orch.conversation_handler
    user_id = str(current_user["_id"])
    if handler.conversation_exists(request.conversation_id):
        if not handler.conversation_exists(request.conversation_id, user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        handler.create_conversation(request.conversation_id, user_id=user_id)

    answer = await orch.ask(
        question=request.question, conversation_id=request.conversation_id
    )
    return UnifiedAgentResponseSchema(
        answer=answer, conversation_id=request.conversation_id
    )


@router.post("/ask/streaming")
async def ask_agent_streaming(
    request: UnifiedAgentRequestSchema,
    current_user: Annotated[dict, Depends(get_current_user)],
    orch: Annotated[UnifiedAgent, Depends(get_orchestrator)],
):
    handler = orch.conversation_handler
    user_id = str(current_user["_id"])
    if handler.conversation_exists(request.conversation_id):
        if not handler.conversation_exists(request.conversation_id, user_id=user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
    else:
        handler.create_conversation(request.conversation_id, user_id=user_id)

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
