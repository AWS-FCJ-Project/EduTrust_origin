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

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
