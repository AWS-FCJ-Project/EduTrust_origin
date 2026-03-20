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

    # Database Settings
    MONGO_URI: Optional[str] = None
    MONGO_USERNAME: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    MONGO_PORT: Optional[str] = None
    MONGO_DB_NAME: Optional[str] = None

    # Auth Settings
    SECRET_KEY: Optional[str] = None

    # Email for OTP
    EMAIL_SENDER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None

    # OTP Settings
    OTP_EXPIRE_SECONDS: Optional[int] = None

    # AWS Credentials
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = "ap-southeast-1"

    # Vector Search Settings
    S3_BUCKET_NAME: Optional[str] = None
    VECTOR_SEARCH_BUCKET: str = "my-vector-doc-search"
    VECTOR_SEARCH_PREFIX: str = "doc-search/"
    VECTOR_SEARCH_INDEX_NAME: str = "document-index"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
