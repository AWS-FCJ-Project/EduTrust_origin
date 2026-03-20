from pydantic_ai import RunContext

from src.crew.agents import (
    general_chat_agent,
    literature_agent,
    math_agent,
    physics_agent,
    quiz_agent,
    web_search_agent,
)
from src.crew.orchestrator import orchestrator
from src.logger import console, log_agent_response, log_delegation
from src.schemas.orchestrator_schema import OrchestratorDeps
from src.utils import get_current_datetime


@orchestrator.tool
async def web_search(ctx: RunContext[OrchestratorDeps], instruction: str) -> str:
    """
    Web search tool.
    - General searching (finding facts, news, or current events).
    - Deep research (comprehensive analysis on complex topics).
    - Content extraction (reading full content from specific URLs).
    Provide clear instructions on what needs to be found, researched, or extracted.
    """
    log_delegation("Orchestrator", "Web Search", instruction)
    result = await web_search_agent.run(
        f"{get_current_datetime()}\n\nInstruction: {instruction}", usage=ctx.usage
    )
    log_agent_response("Web Search Agent", result.output)
    return result.output


@orchestrator.tool
async def planning(ctx: RunContext[OrchestratorDeps], plan: str) -> str:
    """Create a deeply sequential plan before executing any other tools. Mandatory first step."""
    console.print(f"[bold cyan]Plan:[/bold cyan] {plan}")
    return "Plan acknowledged. Now proceed with the delegation tool."


@orchestrator.tool
async def delegate_math(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Get math answer. After receiving, call final_math_response with the result."""
    log_delegation("Orchestrator", "Math", question)
    result = await math_agent.run(
        f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
    )
    log_agent_response("Math Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_physics(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Get physics answer. After receiving, call final_physics_response with the result."""
    log_delegation("Orchestrator", "Physics", question)
    result = await physics_agent.run(
        f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
    )
    log_agent_response("Physics Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_literature(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Get literature answer. After receiving, call final_literature_response with the result."""
    log_delegation("Orchestrator", "Literature", question)
    result = await literature_agent.run(
        f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
    )
    log_agent_response("Literature Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_quiz(ctx: RunContext[OrchestratorDeps], topic: str) -> str:
    """Get quiz questions. After receiving, call final_quiz_response with the result."""
    log_delegation("Orchestrator", "Quiz Generator", topic)
    result = await quiz_agent.run(
        f"Generate quiz questions about: {topic}", usage=ctx.usage
    )
    log_agent_response("Quiz Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_general(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """General Q&A. Use when no specialist tool fits. After receiving, call final_general_response with the result."""
    log_delegation("Orchestrator", "General Chat", question)
    result = await general_chat_agent.run(
        f"{get_current_datetime()}\n\nQuestion: {question}", usage=ctx.usage
    )
    log_agent_response("General Chat Agent", result.output)
    return result.output
