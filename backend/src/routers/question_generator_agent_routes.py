from crewai import Crew, Task
from fastapi import APIRouter
from src.crew.agents import CustomAgents
from src.schemas.question_generator_agent import (
    QuestionGeneratorAgentRequest,
    QuestionGeneratorAgentResponse,
)

router = APIRouter(prefix="/question_generator_ai", tags=["Question Generator AI Agent"])


@router.post("/ask", response_model=QuestionGeneratorAgentResponse)
async def ask_question_generator_ai(request: QuestionGeneratorAgentRequest):
    """Ask question generator AI agent a question."""
    agents = CustomAgents()
    question_generator_ai = agents.question_generator_ai()

    task = Task(
        description=request.question,
        expected_output="Generate high-quality, pedagogically sound questions that accurately measure comprehension and stimulate critical thinking.",
        agent=question_generator_ai,
    )

    crew = Crew(agents=[question_generator_ai], tasks=[task])
    result = crew.kickoff()

    return QuestionGeneratorAgentResponse(answer=str(result))
