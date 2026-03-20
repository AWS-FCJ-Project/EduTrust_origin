from typing import Any

import yaml
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from backend.src.app_config import app_config


class LLM:
    """Interface for LLM chat models."""

    def __init__(self) -> None:
        self._llms_config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        with open(app_config.LLMS_CONFIG_PATH) as file:
            return yaml.safe_load(file) or {}

    def init_chat_model(self, model_name: str) -> OpenAIChatModel:
        """Return a configured OpenAIChatModel."""
        provider = OpenAIProvider(api_key=app_config.OPENAI_API_KEY)
        return OpenAIChatModel(model_name, provider=provider)
