from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise AI Integration Agent Platform"
    app_version: str = "0.1.0"
    environment: str = "dev"

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/enterprise_ai"
    )

    openai_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()