from crewai import Crew, Task
from fastapi import APIRouter
from src.crew.agents import CustomAgents
from src.crew.tools import CustomTools
from src.schemas.math_agent_schema import MathAgentRequest, MathAgentResponse

router = APIRouter(prefix="/math", tags=["Math Agent"])


@router.post("/ask", response_model=MathAgentResponse)
async def ask_math_agent(request: MathAgentRequest):
    """Ask math agent a question."""
    agents = CustomAgents()
    # Add tools to the agent
    tools = [CustomTools.web_search, CustomTools.get_current_datetime]                
    math_agent = agents.math_agent(tools=tools)

    
    task = Task(
        description=request.question,
        expected_output="Support student questions for math",   
        agent=math_agent,
    )   

    crew = Crew(agents=[math_agent], tasks=[task])
    result = crew.kickoff()

    return MathAgentResponse(answer=str(result))
