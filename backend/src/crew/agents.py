import yaml
from pydantic_ai import Agent
from pydantic_ai_litellm import LiteLLMModel

from src.app_config import app_config

# Load configs
with open(app_config.AGENTS_CONFIG_PATH) as f:
    prompts = yaml.safe_load(f)

with open(app_config.LLMS_CONFIG_PATH) as f:
    llm_config = yaml.safe_load(f)

model = LiteLLMModel(llm_config["model_list"][0]["litellm_params"]["model"])

math_agent = Agent(
    model, name="math_agent", instructions=prompts["math_agent"]["backstory"]
)
physics_agent = Agent(
    model,
    name="physics_agent",
    instructions=prompts["physics_chemistry_agent"]["backstory"],
)
literature_agent = Agent(
    model,
    name="literature_agent",
    instructions=prompts["literature_history_agent"]["backstory"],
)
quiz_agent = Agent(
    model, name="quiz_agent", instructions=prompts["question_generator_ai"]["backstory"]
)
tutor_agent = Agent(
    model, name="tutor_agent", instructions=prompts["tutor_agent"]["backstory"]
)
