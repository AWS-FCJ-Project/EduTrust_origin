from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    # API Key Settings
    LITELLM_API_KEY: str
    LITELLM_BASE_URL: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    # Config Paths
    AGENTS_CONFIG_PATH: str
    LLMS_CONFIG_PATH: str

    # Model Settings
    ORCHESTRATOR_MODEL: str
    AGENT_MODEL: str
    TRANSLATE_MODEL: str
    LOGFIRE_TOKEN: str

    # Database Settings
    MONGO_URI: str
    MONGO_USERNAME: str
    MONGO_PASSWORD: str
    MONGO_PORT: str
    MONGO_DB_NAME: str

    # Auth Settings
    SECRET_KEY: str

    # Email for OTP
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str

    # OTP Settings
    OTP_EXPIRE_SECONDS: str

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


app_config = AppConfig()
