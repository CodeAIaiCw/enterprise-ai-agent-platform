from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Integration Agent Platform"
    app_version: str = "0.1.0"
    environment: str = "dev"

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_ai"
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-5"
    planner_mode: str = "mock"
    salesforce_mode: str = "mock"

    mule_experience_api_url: str = ""
    mule_request_timeout_seconds: float = 15.0

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )


settings = Settings()