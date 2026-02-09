from datetime import datetime

from pydantic_ai import RunContext
from src.crew.agents import (
    stem_logic_agent,
    humanities_agent,
    quiz_agent,
    tutor_agent,
    web_search_agent,
)
from src.crew.orchestrator import OrchestratorDeps, orchestrator
from src.logger import console, log_agent_response, log_delegation


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
    result = await web_search_agent.run(instruction, usage=ctx.usage)
    log_agent_response("Web Search Agent", result.output)
    return result.output


@orchestrator.tool
async def planning(ctx: RunContext[OrchestratorDeps], plan: str) -> str:
    """Create a deeply sequential plan before executing any other tools. Mandatory first step."""
    console.print(f"[bold cyan]Plan:[/bold cyan] {plan}")
    return "Plan acknowledged. Now proceed with the delegation tool."


@orchestrator.tool
async def delegate_stem_logic(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """
    Get STEM/Logic answer for Math, Physics, Chemistry, and other science subjects.
    After receiving, call final_stem_logic_response with the result.
    """
    log_delegation("Orchestrator", "STEM Logic", question)
    result = await stem_logic_agent.run(question, usage=ctx.usage)
    log_agent_response("STEM Logic Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_humanities(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """
    Get Humanities answer for Literature, History, and Social Sciences subjects.
    After receiving, call final_humanities_response with the result.
    """
    log_delegation("Orchestrator", "Humanities", question)
    result = await humanities_agent.run(question, usage=ctx.usage)
    log_agent_response("Humanities Agent", result.output)
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
async def delegate_tutor(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """Get tutor answer. After receiving, call final_tutor_response with the result."""
    log_delegation("Orchestrator", "Tutor", question)
    result = await tutor_agent.run(question, usage=ctx.usage)
    log_agent_response("Tutor Agent", result.output)
    return result.output
