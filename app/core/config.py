from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FootballIQ"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./footballiq.db"
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    SEED_DEMO_DATA: bool = True
    FOOTBALL_DATA_API_KEY: str = ""
    FOOTBALL_DATA_BASE_URL: str = "https://api.football-data.org/v4"
    DEFAULT_TIMEZONE: str = "Africa/Lagos"
    FIXTURE_SYNC_ENABLED: bool = True
    AUTO_SYNC_ON_STARTUP: bool = False
    SYNC_REQUEST_DELAY_SECONDS: float = 6.5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
