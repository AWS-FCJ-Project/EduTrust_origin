from crewai import Crew, Task
from fastapi import APIRouter
from src.crew.agents import CustomAgents
from src.crew.tools import CustomTools
from src.schemas.physics_chemistry_agent_schema import PhysicsChemistryAgentRequest, PhysicsChemistryAgentResponse

router = APIRouter(prefix="/physics_chemistry", tags=["Physics and Chemistry Agent"])


@router.post("/ask", response_model=PhysicsChemistryAgentResponse)
async def ask_physics_chemistry_agent(request: PhysicsChemistryAgentRequest):
    """Ask physics and chemistry agent a question."""
    agents = CustomAgents()
    # Add tools to the agent
    tools = [CustomTools.web_search, CustomTools.get_current_datetime]                
    physics_chemistry_agent = agents.physics_chemistry_agent(tools=tools)

    
    task = Task(
        description=request.question,
        expected_output="Support student questions for physics and chemistry",   
        agent=physics_chemistry_agent,
    )   

    crew = Crew(agents=[physics_chemistry_agent], tasks=[task])
    result = crew.kickoff()

    return PhysicsChemistryAgentResponse(answer=str(result))
