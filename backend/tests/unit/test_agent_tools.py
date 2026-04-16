from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai.toolsets import FunctionToolset
from src.agent.tools import AgentTools


@pytest.fixture
def ctx():
    return SimpleNamespace(usage={"requests": 1})


@pytest.fixture
def search_service():
    service = MagicMock()
    service.get_search_tools.return_value = [lambda: None]
    return service


@pytest.fixture
def sub_agents():
    def make_agent(output: str):
        return SimpleNamespace(
            run=AsyncMock(return_value=SimpleNamespace(output=output))
        )

    return {
        "web_search": make_agent("web-output"),
        "technical": make_agent("technical-output"),
        "social": make_agent("social-output"),
        "general": make_agent("general-output"),
    }


@pytest.fixture
def agent_tools(sub_agents, search_service) -> AgentTools:
    return AgentTools(sub_agents=sub_agents, search_service=search_service)


def test_planning_prints_plan_and_returns_acknowledgement(agent_tools, monkeypatch):
    mock_print = MagicMock()
    monkeypatch.setattr("src.agent.tools.console.print", mock_print)

    result = agent_tools.planning(ctx=None, plan="1. Search\n2. Answer")

    assert result == "Plan acknowledged. Now proceed with the delegation tool."
    mock_print.assert_called_once()


@pytest.mark.asyncio
async def test_web_search_delegates_with_toolset(
    agent_tools, sub_agents, search_service, ctx, monkeypatch
):
    log_delegation = MagicMock()
    log_response = MagicMock()
    monkeypatch.setattr("src.agent.tools.log_delegation", log_delegation)
    monkeypatch.setattr("src.agent.tools.log_agent_response", log_response)
    monkeypatch.setattr(
        "src.agent.tools.get_current_datetime",
        lambda: "Current date and time: 2026-04-16 12:00:00 +0700",
    )

    result = await agent_tools.web_search(ctx=ctx, instruction="Find latest AI policy")

    assert result == "web-output"
    search_service.get_search_tools.assert_called_once_with()
    sub_agents["web_search"].run.assert_awaited_once()
    call = sub_agents["web_search"].run.await_args
    assert call.args[0] == (
        "Current date and time: 2026-04-16 12:00:00 +0700\n\n"
        "Search: Find latest AI policy"
    )
    assert call.kwargs["usage"] == ctx.usage
    assert len(call.kwargs["toolsets"]) == 1
    assert isinstance(call.kwargs["toolsets"][0], FunctionToolset)
    log_delegation.assert_called_once_with(
        "MainAgent", "Web Search", "Find latest AI policy"
    )
    log_response.assert_called_once_with("Web Search Agent", "web-output")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "method_name",
        "agent_key",
        "label",
        "prompt_prefix",
        "question",
        "expected_output",
    ),
    [
        (
            "delegate_technical",
            "technical",
            "Technical",
            "Question",
            "Solve integral",
            "technical-output",
        ),
        (
            "delegate_social",
            "social",
            "Social",
            "Question",
            "Summarize history chapter",
            "social-output",
        ),
        (
            "delegate_general",
            "general",
            "General Chat",
            "Question",
            "Explain attendance rules",
            "general-output",
        ),
    ],
)
async def test_delegate_methods_forward_questions_to_sub_agents(
    agent_tools,
    sub_agents,
    ctx,
    monkeypatch,
    method_name,
    agent_key,
    label,
    prompt_prefix,
    question,
    expected_output,
):
    log_delegation = MagicMock()
    log_response = MagicMock()
    monkeypatch.setattr("src.agent.tools.log_delegation", log_delegation)
    monkeypatch.setattr("src.agent.tools.log_agent_response", log_response)
    monkeypatch.setattr(
        "src.agent.tools.get_current_datetime",
        lambda: "Current date and time: 2026-04-16 12:00:00 +0700",
    )

    method = getattr(agent_tools, method_name)
    result = await method(ctx=ctx, question=question)

    assert result == expected_output
    sub_agents[agent_key].run.assert_awaited_once_with(
        "Current date and time: 2026-04-16 12:00:00 +0700\n\n"
        f"{prompt_prefix}: {question}",
        usage=ctx.usage,
    )
    log_delegation.assert_called_once_with("MainAgent", label, question)
    log_response.assert_called_once()
