from crewai import Crew, Task
from fastapi import APIRouter
from src.crew.agents import CustomAgents
from src.schemas.tutor_agent_schema import TutorAgentRequest, TutorAgentResponse

router = APIRouter(prefix="/tutor", tags=["Tutor Agent"])


@router.post("/ask", response_model=TutorAgentResponse)
async def ask_tutor(request: TutorAgentRequest):
    """Ask tutor agent a question."""
    agents = CustomAgents()
    tutor = agents.tutor_agent()

    task = Task(
        description=request.question,
        expected_output="Support student questions for homework",
        agent=tutor,
    )

    crew = Crew(agents=[tutor], tasks=[task])
    result = crew.kickoff()

    return TutorAgentResponse(answer=str(result))
