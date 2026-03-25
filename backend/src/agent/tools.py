from pydantic_ai import Agent, RunContext
from pydantic_ai.toolsets import FunctionToolset
from src.logger import console, log_agent_response, log_delegation
from src.schemas.unified_agent_schema import MainAgentDeps
from src.search_services.unified_search import UnifiedSearch
from src.utils import get_current_datetime


class AgentTools:
    """Collection of tools for the main agent."""

    def __init__(
        self, sub_agents: dict[str, Agent], search_service: UnifiedSearch
    ) -> None:
        self._sub_agents = sub_agents
        self._search_service = search_service

    async def web_search(self, ctx: RunContext[MainAgentDeps], instruction: str) -> str:
        """
        Web search tool.
        - General searching (finding facts, news, or current events).
        - Deep research (comprehensive analysis on complex topics).
        - Content extraction (reading full content from specific URLs).
        Provide clear instructions on what needs to be found, researched, or extracted.
        """
        log_delegation("MainAgent", "Web Search", instruction)
        search_toolset = FunctionToolset(tools=self._search_service.get_search_tools())
        result = await self._sub_agents["web_search"].run(
            f"{get_current_datetime()}\n\nSearch: {instruction}",
            usage=ctx.usage,
            toolsets=[search_toolset],
        )
        log_agent_response("Web Search Agent", result.output)
        return result.output

    def planning(self, ctx: RunContext[MainAgentDeps], plan: str) -> str:
        """Create a deeply sequential plan before executing any other tools. Mandatory first step."""
        console.print(f"[bold cyan]Plan:[/bold cyan] {plan}")
        return "Plan acknowledged. Now proceed with the delegation tool."

    async def delegate_math(self, ctx: RunContext[MainAgentDeps], question: str) -> str:
        """Get math answer."""
        log_delegation("MainAgent", "Math", question)
        result = await self._sub_agents["math"].run(
            f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
        )
        log_agent_response("Math Agent", result.output)
        return result.output

    async def delegate_physics(
        self, ctx: RunContext[MainAgentDeps], question: str
    ) -> str:
        """Get physics answer."""
        log_delegation("MainAgent", "Physics", question)
        result = await self._sub_agents["physics"].run(
            f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
        )
        log_agent_response("Physics Agent", result.output)
        return result.output

    async def delegate_literature(
        self, ctx: RunContext[MainAgentDeps], question: str
    ) -> str:
        """Get literature answer."""
        log_delegation("MainAgent", "Literature", question)
        result = await self._sub_agents["literature"].run(
            f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
        )
        log_agent_response("Literature Agent", result.output)
        return result.output

    async def delegate_quiz(self, ctx: RunContext[MainAgentDeps], topic: str) -> str:
        """Get quiz questions."""
        log_delegation("MainAgent", "Quiz Generator", topic)
        result = await self._sub_agents["quiz"].run(
            f"Generate quiz questions about: {topic}", usage=ctx.usage
        )
        log_agent_response("Quiz Agent", result.output)
        return result.output

    async def delegate_general(
        self, ctx: RunContext[MainAgentDeps], question: str
    ) -> str:
        """General Q&A. Use when no specialist tool fits."""
        log_delegation("MainAgent", "General Chat", question)
        result = await self._sub_agents["general_chat"].run(
            f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
        )
        log_agent_response("General Chat Agent", result.output)
        return result.output
