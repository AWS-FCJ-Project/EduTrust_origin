from collections.abc import AsyncIterator
from typing import Optional

import logfire
import yaml
from pydantic_ai import Agent, AgentRunResultEvent, messages
from backend.src.app_config import app_config
from backend.src.llm import LLM
from backend.src.logger import log_agent_response, log_user_input
from backend.src.schemas.orchestrator_schema import (
    OrchestratorDeps,
    OrchestratorStreamEvent,
)
from backend.src.state import get_conversation_handler
from backend.src.utils import get_current_datetime

with open(app_config.AGENTS_CONFIG_PATH) as f:
    prompts = yaml.safe_load(f)

with open(app_config.LLMS_CONFIG_PATH) as f:
    llm_config = yaml.safe_load(f)

model_name = app_config.ORCHESTRATOR_MODEL or llm_config.get("orchestrator_model")
llm = LLM(app_config)
model = llm.chat_model(model_name)

orchestrator = Agent(
    model,
    name="orchestrator",
    deps_type=OrchestratorDeps,
    instructions=prompts["orchestrator"]["instructions"],
)

TOOL_CALL_PART_TYPES = tuple(
    part_type
    for part_type in (
        getattr(messages, "ToolCallPart", None),
        getattr(messages, "BuiltinToolCallPart", None),
    )
    if part_type is not None
)
TOOL_RETURN_PART_TYPES = tuple(
    part_type
    for part_type in (
        getattr(messages, "ToolReturnPart", None),
        getattr(messages, "BuiltinToolReturnPart", None),
    )
    if part_type is not None
)


def _extract_text_chunk(event) -> Optional[str]:
    if isinstance(event, messages.PartDeltaEvent) and isinstance(
        event.delta, messages.TextPartDelta
    ):
        return event.delta.content_delta or None

    if isinstance(event, messages.PartStartEvent) and isinstance(
        event.part, messages.TextPart
    ):
        return event.part.content or None

    return None


def _tool_call_arguments(part) -> Optional[object]:
    tool_arguments = getattr(part, "args", None)
    if tool_arguments not in (None, ""):
        return tool_arguments
    if hasattr(part, "args_as_json_str") and callable(
        getattr(part, "args_as_json_str")
    ):
        return part.args_as_json_str()
    return tool_arguments


def _extract_tool_event(part) -> Optional[OrchestratorStreamEvent]:
    if TOOL_CALL_PART_TYPES and isinstance(part, TOOL_CALL_PART_TYPES):
        tool_name = getattr(part, "tool_name", None)
        return OrchestratorStreamEvent(
            type="tool_call",
            content={"tool_name": tool_name, "arguments": _tool_call_arguments(part)},
        )

    if TOOL_RETURN_PART_TYPES and isinstance(part, TOOL_RETURN_PART_TYPES):
        tool_name = getattr(part, "tool_name", None)
        tool_result = getattr(part, "content", None)
        if tool_result is None:
            tool_result = str(part)
        return OrchestratorStreamEvent(
            type="tool_result",
            content={"tool_name": tool_name, "result": tool_result},
        )

    return None


def _build_context_text(conversation_handler, conversation_id: str) -> str:
    context = conversation_handler.get_context(conversation_id, k=10)
    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in context
        if message.get("content")
    )


def _build_prompt_text(question: str, context_text: str) -> str:
    return (
        f"{get_current_datetime()}\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}"
    )


def _build_run_inputs(question: str, conversation_id: str):
    log_user_input(question, conversation_id)

    conversation_handler = get_conversation_handler()
    conversation_handler.add_message(conversation_id, role="user", content=question)

    orchestrator_deps = OrchestratorDeps(
        conversation_id=conversation_id, conversation_handler=conversation_handler
    )

    context_text = _build_context_text(conversation_handler, conversation_id)
    prompt_text = _build_prompt_text(question, context_text)
    return conversation_handler, orchestrator_deps, prompt_text


async def ask(question: str, conversation_id: str) -> str:
    with logfire.span(
        "ask_orchestrator", question=question, conversation_id=conversation_id
    ):
        conversation_handler, orchestrator_deps, prompt_text = _build_run_inputs(
            question, conversation_id
        )
        result = await orchestrator.run(
            prompt_text,
            deps=orchestrator_deps,
        )

        answer = result.output
        log_agent_response("Orchestrator", answer)
        conversation_handler.add_message(
            conversation_id, role="assistant", content=answer
        )
        return answer


async def ask_stream_with_tool_calls(
    question: str, conversation_id: str
) -> AsyncIterator[OrchestratorStreamEvent]:
    """
    Stream the orchestrator's response with tool call / tool result events.
    """

    with logfire.span(
        "ask_orchestrator_stream_with_tools",
        question=question,
        conversation_id=conversation_id,
    ):
        conversation_handler, orchestrator_deps, prompt_text = _build_run_inputs(
            question, conversation_id
        )

        final_answer: Optional[str] = None
        sent_any_text = False
        fallback_text_parts: list[str] = []

        async for event in orchestrator.run_stream_events(
            prompt_text, deps=orchestrator_deps
        ):
            text_chunk = _extract_text_chunk(event)
            if text_chunk:
                sent_any_text = True
                fallback_text_parts.append(text_chunk)
                yield OrchestratorStreamEvent(type="text_delta", content=text_chunk)
                continue

            if isinstance(event, messages.PartEndEvent):
                tool_event = _extract_tool_event(event.part)
                if tool_event is not None:
                    yield tool_event
                continue

            if isinstance(event, AgentRunResultEvent):
                final_answer = str(event.result.output)

        if final_answer and not sent_any_text:
            yield OrchestratorStreamEvent(type="text_delta", content=final_answer)

        answer_for_memory = (
            final_answer if final_answer is not None else "".join(fallback_text_parts)
        )
        log_agent_response("Orchestrator", answer_for_memory)
        conversation_handler.add_message(
            conversation_id, role="assistant", content=answer_for_memory
        )
