from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    ENVIRONMENT: str = "local"

    LITELLM_API_KEY: Optional[str] = None

    AGENTS_CONFIG_PATH: Optional[str] = None
    LLMS_CONFIG_PATH: Optional[str] = None

    ORCHESTRATOR_MODEL: Optional[str] = None
    AGENT_MODEL: Optional[str] = None
    LOGFIRE_TOKEN: Optional[str] = None

    MONGO_URI: Optional[str] = None
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_PORT: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = None

    TAVILY_API_KEY: Optional[str] = None

    SECRET_KEY: Optional[str] = None

    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    OTP_EXPIRE_SECONDS: Optional[int] = 300

    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
