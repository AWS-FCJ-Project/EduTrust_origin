from typing import Optional

import yaml
from crewai import Agent
from src.app_config import app_config
from src.llm import LLMProvider


class CustomAgents:
    """Factory for creating CrewAI agents from YAML config."""

    def __init__(self):
        self.llm_provider = LLMProvider()
        self.agents_config = self._load_config()

    def _load_config(self) -> dict:
        """Load agents config from YAML file."""
        config_path = app_config.AGENTS_CONFIG_PATH
        if config_path:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    def get_agent(
        self,
        agent_name: str,
        tools: Optional[list] = None,
        model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> Agent:
        """Create agent from YAML config by name."""
        if agent_name not in self.agents_config:
            raise ValueError(f"Agent '{agent_name}' not found in config")
        config = self.agents_config[agent_name]
        return Agent(
            role=config["role"],
            goal=config["goal"],
            backstory=config["backstory"],
            llm=self.llm_provider.get_llm(model=model, temperature=temperature),
            tools=tools or [],
            verbose=config.get("verbose", True),
        )

    def tutor_agent(
        self,
        tools: Optional[list] = None,
        model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> Agent:
        """Create tutor agent from config."""
        return self.get_agent(
            "tutor_agent", tools=tools, model=model, temperature=temperature
        )
