from collections.abc import AsyncIterator
from typing import Optional

import logfire
import yaml
from pydantic_ai import Agent, AgentRunResultEvent, messages
from src.app_config import app_config
from src.llm import LLM
from src.logger import log_agent_response, log_user_input
from src.schemas.orchestrator_schema import OrchestratorDeps, OrchestratorStreamEvent
from src.state import get_conversation_handler
from src.utils import get_current_datetime

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


async def ask(question: str, conversation_id: str) -> str:
    with logfire.span(
        "ask_orchestrator", question=question, conversation_id=conversation_id
    ):
        log_user_input(question, conversation_id)

        conversation_handler = get_conversation_handler()
        conversation_handler.add_message(conversation_id, role="user", content=question)

        context = conversation_handler.get_context(conversation_id, k=10)
        context_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in context
            if message.get("content")
        )

        orchestrator_deps = OrchestratorDeps(
            conversation_id=conversation_id, conversation_handler=conversation_handler
        )
        prompt_text = (
            f"{get_current_datetime()}\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}"
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

    tool_call_part_types = tuple(
        part_type
        for part_type in (
            getattr(messages, "ToolCallPart", None),
            getattr(messages, "BuiltinToolCallPart", None),
        )
        if part_type is not None
    )
    tool_return_part_types = tuple(
        part_type
        for part_type in (
            getattr(messages, "ToolReturnPart", None),
            getattr(messages, "BuiltinToolReturnPart", None),
        )
        if part_type is not None
    )

    with logfire.span(
        "ask_orchestrator_stream_with_tools",
        question=question,
        conversation_id=conversation_id,
    ):
        log_user_input(question, conversation_id)

        conversation_handler = get_conversation_handler()
        conversation_handler.add_message(conversation_id, role="user", content=question)

        context = conversation_handler.get_context(conversation_id, k=10)
        context_text = "\n".join(
            f"{message['role']}: {message['content']}"
            for message in context
            if message.get("content")
        )

        orchestrator_deps = OrchestratorDeps(
            conversation_id=conversation_id, conversation_handler=conversation_handler
        )
        prompt_text = (
            f"{get_current_datetime()}\n"
            f"Context:\n{context_text}\n\n"
            f"Question: {question}"
        )

        final_answer: Optional[str] = None
        sent_any_text = False
        fallback_text_parts: list[str] = []

        async for event in orchestrator.run_stream_events(
            prompt_text, deps=orchestrator_deps
        ):
            if isinstance(event, messages.PartDeltaEvent) and isinstance(
                event.delta, messages.TextPartDelta
            ):
                chunk = event.delta.content_delta
                if chunk:
                    sent_any_text = True
                    fallback_text_parts.append(chunk)
                    yield OrchestratorStreamEvent(type="text_delta", content=chunk)
            elif isinstance(event, messages.PartStartEvent) and isinstance(
                event.part, messages.TextPart
            ):
                chunk = event.part.content
                if chunk:
                    sent_any_text = True
                    fallback_text_parts.append(chunk)
                    yield OrchestratorStreamEvent(type="text_delta", content=chunk)
            elif isinstance(event, messages.PartEndEvent):
                part = event.part

                if tool_call_part_types and isinstance(part, tool_call_part_types):
                    tool_name = getattr(part, "tool_name", None)
                    tool_arguments = getattr(part, "args", None)
                    if (
                        (tool_arguments is None or tool_arguments == "")
                        and hasattr(part, "args_as_json_str")
                        and callable(getattr(part, "args_as_json_str"))
                    ):
                        tool_arguments = part.args_as_json_str()

                    yield OrchestratorStreamEvent(
                        type="tool_call",
                        content={"tool_name": tool_name, "arguments": tool_arguments},
                    )
                elif tool_return_part_types and isinstance(part, tool_return_part_types):
                    tool_name = getattr(part, "tool_name", None)
                    tool_result = getattr(part, "content", None)
                    if tool_result is None:
                        tool_result = str(part)
                    yield OrchestratorStreamEvent(
                        type="tool_result",
                        content={"tool_name": tool_name, "result": tool_result},
                    )
            elif isinstance(event, AgentRunResultEvent):
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
