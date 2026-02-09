import yaml
from pydantic_ai import Agent
from pydantic_ai_litellm import LiteLLMModel
from src.app_config import app_config
from src.search_services.unified_search import UnifiedSearch

with open(app_config.AGENTS_CONFIG_PATH) as f:
    prompts = yaml.safe_load(f)

with open(app_config.LLMS_CONFIG_PATH) as f:
    llm_config = yaml.safe_load(f)

model_name = app_config.AGENT_MODEL or llm_config.get("agent_model")
model = LiteLLMModel(model_name)

search_service = UnifiedSearch()

# ============================================================================
# OLD AGENTS (DEPRECATED - Commented out for reference)
# ============================================================================
# math_agent = Agent(
#     model, name="math_agent", instructions=prompts["math_agent"]["backstory"]
# )
# physics_agent = Agent(
#     model,
#     name="physics_agent",
#     instructions=prompts["physics_chemistry_agent"]["backstory"],
# )
# literature_agent = Agent(
#     model,
#     name="literature_agent",
#     instructions=prompts["literature_history_agent"]["backstory"],
# )
# ============================================================================

# ============================================================================
# NEW CONSOLIDATED AGENTS
# ============================================================================
stem_logic_agent = Agent(
    model,
    name="stem_logic_agent",
    instructions=prompts["stem_logic_agent"]["backstory"],
)
humanities_agent = Agent(
    model,
    name="humanities_agent",
    instructions=prompts["humanities_agent"]["backstory"],
)
# ============================================================================
quiz_agent = Agent(
    model, name="quiz_agent", instructions=prompts["question_generator_ai"]["backstory"]
)
general_chat_agent = Agent(
    model,
    name="general_chat_agent",
    instructions=prompts["general_chat_agent"]["backstory"],
)

web_search_agent = Agent(
    model,
    name="web_search_agent",
    instructions=prompts["web_search_agent"]["backstory"],
)

for tool_func in search_service.get_search_tools():
    web_search_agent.tool(tool_func)
