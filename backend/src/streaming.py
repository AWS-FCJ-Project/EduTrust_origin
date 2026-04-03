from collections.abc import AsyncIterator
from typing import Any, Optional

from fastapi.responses import StreamingResponse
from pydantic_ai import Agent, AgentRunResultEvent, messages
from src.logger import log_agent_response
from src.schemas.unified_agent_schema import MainAgentDeps, MainAgentStreamEvent

TOOL_CALL_TYPES = tuple(
    tool_type
    for tool_type in (
        getattr(messages, "ToolCallPart", None),
        getattr(messages, "BuiltinToolCallPart", None),
    )
    if tool_type is not None
)
TOOL_RETURN_TYPES = tuple(
    return_type
    for return_type in (
        getattr(messages, "ToolReturnPart", None),
        getattr(messages, "BuiltinToolReturnPart", None),
    )
    if return_type is not None
)


class Streaming:
    """Handles streaming output for agents."""

    def __init__(
        self,
        orchestrator: Agent[MainAgentDeps],
        deps: MainAgentDeps,
        prompt: str,
        conversation_id: str,
        conversation_handler: Any,
    ) -> None:
        self._orchestrator = orchestrator
        self._deps = deps
        self._prompt = prompt
        self._conversation_id = conversation_id
        self._conversation_handler = conversation_handler

    async def stream_events(self) -> AsyncIterator[MainAgentStreamEvent]:
        """Stream orchestrator events, then store the assistant's reply."""
        final_answer: Optional[str] = None
        text_parts: list[str] = []

        async for event in self._orchestrator.run_stream_events(
            self._prompt, deps=self._deps
        ):
            streamed = self._process_event(event, text_parts)
            if streamed is not None:
                yield streamed
                continue

            if isinstance(event, AgentRunResultEvent):
                final_answer = str(event.result.output)

        if final_answer is not None and not text_parts:
            yield MainAgentStreamEvent(type="text_delta", content=final_answer)

        reply = final_answer if final_answer is not None else "".join(text_parts)
        log_agent_response("Orchestrator", reply)
        await self._conversation_handler.add_message(
            self._conversation_id, role="assistant", content=reply
        )
        await self._conversation_handler.get_context(
            self._conversation_id, message_limit=10
        )

    def _process_event(
        self, event: Any, text_parts: list[str]
    ) -> Optional[MainAgentStreamEvent]:
        """Return a stream event for text/tool parts, or None for other events."""
        if isinstance(event, messages.PartDeltaEvent) and isinstance(
            event.delta, messages.TextPartDelta
        ):
            text_parts.append(event.delta.content_delta)
            return MainAgentStreamEvent(
                type="text_delta", content=event.delta.content_delta
            )

        if isinstance(event, messages.PartStartEvent) and isinstance(
            event.part, messages.TextPart
        ):
            text_parts.append(event.part.content)
            return MainAgentStreamEvent(type="text_delta", content=event.part.content)

        if isinstance(event, messages.PartEndEvent):
            return self._process_part(event.part)

        return None

    def _process_part(self, part: Any) -> Optional[MainAgentStreamEvent]:
        """Return a stream event for a tool part, or None."""
        if TOOL_CALL_TYPES and isinstance(part, TOOL_CALL_TYPES):
            return MainAgentStreamEvent(
                type="tool_call",
                content={"tool_name": part.tool_name, "arguments": part.args},
            )
        if TOOL_RETURN_TYPES and isinstance(part, TOOL_RETURN_TYPES):
            return MainAgentStreamEvent(
                type="tool_result",
                content={"tool_name": part.tool_name, "result": part.content},
            )
        return None

    @staticmethod
    def sse_json(payload: dict[str, Any]) -> str:
        import json

        return f"data: {json.dumps(payload, ensure_ascii=False, default=str)}\n\n"

    @staticmethod
    def sse_response(events: AsyncIterator[str]) -> StreamingResponse:
        return StreamingResponse(
            events,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
                "X-Accel-Buffering": "no",
            },
        )
