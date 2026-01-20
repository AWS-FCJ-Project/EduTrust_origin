from typing import AsyncGenerator, List, Optional

import yaml
from crewai import LLM
from litellm import acompletion, completion
from src.app_config import app_config


class LLMProvider:
    """Provider for LLM."""

    _config: Optional[dict] = None

    def __init__(self):
        if LLMProvider._config is None:
            LLMProvider._config = self._load_config()

    def _load_config(self) -> dict:
        """Load config from YAML."""
        with open(app_config.LLMS_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)

    def get_model(self, model_name: Optional[str] = None) -> str:
        """Get model from config."""
        models = self._config["model_list"]
        if model_name is None:
            return models[0]["litellm_params"]["model"]
        for m in models:
            if m["model_name"] == model_name:
                return m["litellm_params"]["model"]
        return models[0]["litellm_params"]["model"]

    def get_llm(self, model: Optional[str] = None, temperature: float = 0.5) -> LLM:
        """Get CrewAI LLM."""
        return LLM(model=self.get_model(model), temperature=temperature)

    async def achat(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> str:
        """Async chat completion."""
        response = await acompletion(
            model=self.get_model(model), messages=messages, temperature=temperature
        )
        return response.choices[0].message.content

    async def astream(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.5,
    ) -> AsyncGenerator[str, None]:
        """Async streaming chat."""
        response = await acompletion(
            model=self.get_model(model),
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
