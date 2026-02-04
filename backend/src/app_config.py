from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    LITELLM_API_KEY: Optional[str] = None

    AGENTS_CONFIG_PATH: Optional[str] = None
    LLMS_CONFIG_PATH: Optional[str] = None

    ORCHESTRATOR_MODEL: Optional[str] = None
    AGENT_MODEL: Optional[str] = None
    LOGFIRE_TOKEN: Optional[str] = None

    MONGO_URI: Optional[str] = "mongodb://localhost:27017"
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_PORT: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = "proctoring_db"

    TAVILY_API_KEY: Optional[str] = None

    # Auth Settings
    SECRET_KEY: str = "your_secret_key_for_session_middleware" # Required for SessionMiddleware

    REDIS_URL: str = "redis://localhost:6379"
    EMAIL_SENDER: Optional[str] = None

    EMAIL_PASSWORD: Optional[str] = None
    
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    OTP_EXPIRE_SECONDS: int = 300
    OTP_RATE_LIMIT_SECONDS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
