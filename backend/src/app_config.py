from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    LITELLM_API_KEY: Optional[str] = None

    AGENTS_CONFIG_PATH: Optional[str] = None
    LLMS_CONFIG_PATH: Optional[str] = None

    ORCHESTRATOR_MODEL: Optional[str] = None
    AGENT_MODEL: Optional[str] = None
    TRANSLATE_MODEL: Optional[str] = None
    LOGFIRE_TOKEN: Optional[str] = None
    ALLOWED_ORIGINS: list[str] = ["*"]

    MONGO_URI: Optional[str] = None
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_PORT: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = None

    TAVILY_API_KEY: Optional[str] = None

    # Auth Settings
    SECRET_KEY: Optional[str] = None

    # Email for OTP
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # OTP Settings
    OTP_EXPIRE_SECONDS: Optional[int] = None

    # RAG Settings
    RAG_ENABLED: Optional[bool] = True
    RAG_EMBEDDING_MODEL: Optional[str] = "BAAI/bge-small-en-v1.5"
    RAG_RERANKER_MODEL: Optional[str] = "BAAI/bge-reranker-base"
    RAG_LLM_MODEL: Optional[str] = "mistralai/Mistral-7B-Instruct-v0.2"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
