from crewai import Crew, Task
from fastapi import APIRouter
from src.crew.agents import CustomAgents
from src.crew.tools import CustomTools
from src.schemas.literature_history_agent_schema import LiteratureHistoryAgentRequest, LiteratureHistoryAgentResponse

router = APIRouter(prefix="/literature_history", tags=["Literature and History Agent"])


@router.post("/ask", response_model=LiteratureHistoryAgentResponse)
async def ask_literature_history_agent(request: LiteratureHistoryAgentRequest):
    """Ask literature and history agent a question."""
    agents = CustomAgents()
    # Add tools to the agent
    tools = [CustomTools.web_search, CustomTools.get_current_datetime]                
    literature_history_agent = agents.literature_history_agent(tools=tools)

    
    task = Task(
        description=request.question,
        expected_output="Support student questions for literature and history",   
        agent=literature_history_agent,
    )   

    crew = Crew(agents=[literature_history_agent], tasks=[task])
    result = crew.kickoff()

    return LiteratureHistoryAgentResponse(answer=str(result))
