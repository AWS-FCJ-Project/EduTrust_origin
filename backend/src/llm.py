import os
from typing import Any, Dict, Optional

import yaml

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.litellm import LiteLLMProvider
from pydantic_ai.providers.openai import OpenAIProvider
from src.app_config import app_config


class LLM:
    def __init__(self, config=app_config):
        self._config = config
        self._llms_config = self._load_llms_config()
        self._model_params_by_name = self._index_model_list()

    def _load_llms_config(self) -> Dict[str, Any]:
        with open(self._config.LLMS_CONFIG_PATH) as file:
            data = yaml.safe_load(file)
        return {} if data is None else data

    def _index_model_list(self) -> Dict[str, Dict[str, Any]]:
        model_list = self._llms_config.get("model_list")
        if not isinstance(model_list, list):
            return {}

        result: Dict[str, Dict[str, Any]] = {}
        for item in model_list:
            if not isinstance(item, dict):
                continue
            model_name = item.get("model_name")
            params = item.get("litellm_params")
            if isinstance(model_name, str) and isinstance(params, dict):
                result[model_name] = params
        return result

    def resolve_model_name(self, model_name_or_key: str) -> str:
        value = self._llms_config.get(model_name_or_key)
        return value if isinstance(value, str) and value else model_name_or_key

    def _resolve_secret_ref(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return value

        if value.startswith("app_config/") or value.startswith("app_config."):
            attribute_name = (
                value.split("/", 1)[1] if "/" in value else value.split(".", 1)[1]
            )
            return getattr(self._config, attribute_name, None)

        if value.startswith("env/") or value.startswith("env."):
            environment_key = (
                value.split("/", 1)[1] if "/" in value else value.split(".", 1)[1]
            )
            return os.getenv(environment_key)

        return value

    def chat_model(self, model_name_or_key: str) -> OpenAIChatModel:
        resolved_name = self.resolve_model_name(model_name_or_key)
        params = self._model_params_by_name.get(resolved_name, {})

        model_name = (
            params.get("model")
            if isinstance(params.get("model"), str) and params.get("model")
            else resolved_name
        )
        api_base = self._resolve_secret_ref(params.get("api_base")) or self._config.LITELLM_BASE_URL
        api_key = (
            self._resolve_secret_ref(params.get("api_key"))
            or self._config.LITELLM_API_KEY
            or self._config.OPENAI_API_KEY
        )

        openai_default_api_base = "https://api.openai.com/v1"
        using_litellm_proxy = bool(api_base) and api_base != openai_default_api_base
        if using_litellm_proxy:
            if model_name and "/" not in model_name:
                model_name = f"openai/{model_name}"
            provider = LiteLLMProvider(api_base=api_base, api_key=api_key)
            return OpenAIChatModel(model_name, provider=provider)

        if model_name and "/" in model_name:
            provider_prefix, suffix = model_name.split("/", 1)
            if provider_prefix != "openai":
                raise ValueError(
                    f"Model '{model_name}' requires a LiteLLM proxy (LITELLM_API_BASE)."
                )
            model_name = suffix

        provider = OpenAIProvider(api_key=self._config.OPENAI_API_KEY)
        return OpenAIChatModel(model_name, provider=provider)
