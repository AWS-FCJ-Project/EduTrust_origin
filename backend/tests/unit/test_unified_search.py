from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai import RunContext
from src.search_services.unified_search import UnifiedSearch


def test_init_prefers_explicit_api_key(monkeypatch):
    tavily_ctor = MagicMock(return_value=MagicMock())
    monkeypatch.setattr(
        "src.search_services.unified_search.TavilySearch",
        tavily_ctor,
    )

    search = UnifiedSearch(tavily_api_key="tvly-explicit")

    assert search.tavily_api_key == "tvly-explicit"
    tavily_ctor.assert_called_once_with("tvly-explicit")


def test_get_search_tools_returns_expected_methods():
    search = object.__new__(UnifiedSearch)
    search.search = MagicMock()
    search.extract = MagicMock()
    search.create_research_task = MagicMock()
    search.get_research_task_result = MagicMock()

    tools = search.get_search_tools()

    assert tools == [
        search.search,
        search.extract,
        search.create_research_task,
        search.get_research_task_result,
    ]


@pytest.mark.asyncio
async def test_search_forwards_parameters_to_tavily():
    search = object.__new__(UnifiedSearch)
    search.tavily_search = MagicMock()
    search.tavily_search.search = AsyncMock(return_value="search-result")

    result = await search.search(
        ctx=MagicMock(spec=RunContext),
        query="latest exam rules",
        search_depth="advanced",
        topic="news",
        days=7,
        max_results=10,
    )

    assert result == "search-result"
    search.tavily_search.search.assert_awaited_once_with(
        query="latest exam rules",
        search_depth="advanced",
        topic="news",
        days=7,
        max_results=10,
    )


@pytest.mark.asyncio
async def test_extract_forwards_parameters_to_tavily():
    search = object.__new__(UnifiedSearch)
    search.tavily_search = MagicMock()
    search.tavily_search.extract = AsyncMock(return_value="extract-result")

    result = await search.extract(
        ctx=MagicMock(spec=RunContext),
        urls=["https://example.com"],
        extract_depth="advanced",
        query="grade rubric",
        chunks_per_source=2,
    )

    assert result == "extract-result"
    search.tavily_search.extract.assert_awaited_once_with(
        urls=["https://example.com"],
        extract_depth="advanced",
        query="grade rubric",
        chunks_per_source=2,
    )


@pytest.mark.asyncio
async def test_create_research_task_forwards_parameters_to_tavily():
    search = object.__new__(UnifiedSearch)
    search.tavily_search = MagicMock()
    search.tavily_search.create_research_task = AsyncMock(return_value="req-123")

    result = await search.create_research_task(
        ctx=MagicMock(spec=RunContext),
        input="compare online proctoring methods",
        model="research-model",
    )

    assert result == "req-123"
    search.tavily_search.create_research_task.assert_awaited_once_with(
        input="compare online proctoring methods",
        model="research-model",
    )


@pytest.mark.asyncio
async def test_get_research_task_result_forwards_request_id_to_tavily():
    search = object.__new__(UnifiedSearch)
    search.tavily_search = MagicMock()
    search.tavily_search.get_research_task_result = AsyncMock(
        return_value="final report"
    )

    result = await search.get_research_task_result(
        ctx=MagicMock(spec=RunContext),
        request_id="req-123",
    )

    assert result == "final report"
    search.tavily_search.get_research_task_result.assert_awaited_once_with(
        request_id="req-123"
    )
