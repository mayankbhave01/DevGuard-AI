from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "devguard-local-secret-change-me"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./devguard.db"
    frontend_origin: str = "http://localhost:5173"

    llm_provider: str = "disabled"
    llm_model: str = ""
    llm_api_key: str = ""
    llm_base_url: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
