from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FootballIQ"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./footballiq.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    SEED_DEMO_DATA: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


settings = Settings()
