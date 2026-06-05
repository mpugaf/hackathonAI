from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://reqflow_user:reqflow_pass@localhost:5432/reqflow"
    TCS_API_KEY: str = "PLACEHOLDER_KEY"
    SECRET_KEY: str = "cambiar_en_produccion_123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    TCS_LLM_BASE_URL: str = "https://genailab.tcs.in/v1/chat/completions"
    LLM_GENERATOR_MODEL: str = "genailab-maas-gpt-4o"
    LLM_REVIEWER_MODEL: str = "azure/genailab-maas-gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: int = 30
    LLM_MAX_RETRIES: int = 2
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


settings = Settings()
