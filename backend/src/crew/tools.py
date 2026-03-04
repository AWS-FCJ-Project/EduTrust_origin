from datetime import datetime

from pydantic_ai import RunContext
from src.crew.agents import (
    humanities_agent,
    quiz_agent,
    stem_logic_agent,
    tutor_agent,
    web_search_agent,
)
from src.crew.orchestrator import OrchestratorDeps, orchestrator
from src.logger import console, log_agent_response, log_delegation


def _get_current_datetime() -> str:
    time_now = datetime.now().astimezone()
    return f"Current date and time: {time_now.strftime('%Y-%m-%d %H:%M:%S %z')}"


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
    Use for questions where the answer requires quantitative reasoning, logical proof,
    or scientific explanation — questions that have an objectively correct answer based
    on formulas, calculations, empirical evidence, or structured logical deduction.
    After receiving the response, call final_stem_logic_response.
    """
    log_delegation("Orchestrator", "STEM Logic", question)
    result = await stem_logic_agent.run(question, usage=ctx.usage)
    log_agent_response("STEM Logic Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_humanities(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """
    Use for questions where the answer requires interpreting human experience, culture,
    or meaning — questions whose answers depend on context, perspective, and values
    rather than calculation or empirical proof (e.g. literary analysis, historical
    narrative, philosophical argument, social phenomena).
    After receiving the response, call final_humanities_response.
    """
    log_delegation("Orchestrator", "Humanities", question)
    result = await humanities_agent.run(question, usage=ctx.usage)
    log_agent_response("Humanities Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_quiz(ctx: RunContext[OrchestratorDeps], topic: str) -> str:
    """
    Use this tool when the user explicitly asks to generate quiz questions, practice tests,
    or assessment items on any topic (STEM or Humanities).
    After receiving the response, call final_quiz_response.
    """
    log_delegation("Orchestrator", "Quiz Generator", topic)
    result = await quiz_agent.run(
        f"Generate quiz questions about: {topic}", usage=ctx.usage
    )
    log_agent_response("Quiz Agent", result.output)
    return result.output


@orchestrator.tool
async def delegate_tutor(ctx: RunContext[OrchestratorDeps], question: str) -> str:
    """
    Use this tool when the user wants step-by-step guided learning, Socratic-style tutoring,
    or general academic support that does not specifically require STEM or Humanities expertise.
    After receiving the response, call final_tutor_response.
    """
    log_delegation("Orchestrator", "Tutor", question)
    result = await tutor_agent.run(question, usage=ctx.usage)
    log_agent_response("Tutor Agent", result.output)
    return result.output
