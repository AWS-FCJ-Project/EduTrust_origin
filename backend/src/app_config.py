from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    # API Key Settings
    LITELLM_API_KEY: Optional[str] = None
    LITELLM_BASE_URL: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    TAVILY_API_KEY: Optional[str] = None

    # Config Paths
    AGENTS_CONFIG_PATH: Optional[str] = None
    LLMS_CONFIG_PATH: Optional[str] = None

    # Model Settings
    ORCHESTRATOR_MODEL: Optional[str] = None
    AGENT_MODEL: Optional[str] = None
    TRANSLATE_MODEL: Optional[str] = None
    LOGFIRE_TOKEN: Optional[str] = None
    EMBEDDING_MODEL: Optional[str] = None

    # DynamoDB Settings (Phase 02 - Migration from MongoDB)
    DYNAMODB_TABLE_PREFIX: Optional[str] = "edutrust-backend"
    DYNAMODB_REGION: Optional[str] = "ap-southeast-1"
    DYNAMODB_ENDPOINT: Optional[str] = None  # For local testing: http://localhost:8000

    # Auth Settings
    SECRET_KEY: Optional[str] = None
    COGNITO_USER_POOL_ID: Optional[str] = None
    COGNITO_APP_CLIENT_ID: Optional[str] = None
    COGNITO_REGION: Optional[str] = None

    # Email for OTP
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # OTP Settings
    OTP_EXPIRE_SECONDS: Optional[int] = None

    # AWS / S3 Settings
    AWS_REGION: Optional[str] = "ap-southeast-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_SESSION_TOKEN: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None

    # Redis Settings
    REDIS_CLIENT_HOST: Optional[str] = None
    REDIS_CLIENT_PASSWORD: Optional[str] = None
    REDIS_PORT: Optional[int] = None
    REDIS_DB: Optional[int] = None
    REDIS_TLS: Optional[bool] = False
    REDIS_KEY_PREFIX: Optional[str] = None
    REDIS_CHAT_TTL: Optional[int] = None

    # Langfuse Settings
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_BASE_URL: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
