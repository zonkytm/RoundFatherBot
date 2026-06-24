from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str
    BOT_USERNAME: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bot_qwen"

    ADMIN_IDS: list[int] = []

    WEBAPP_URL: str = "http://localhost:8000"
    DASHBOARD_TOKEN: str = ""

    VIDEO_MAX_SIZE_MB: int = 50
    VIDEO_MAX_DURATION: int = 60
    VIDEO_NOTE_SIZE: int = 360
    RATE_LIMIT_PER_MINUTE: int = 5

    TEMP_DIR: str = "/tmp/bot_media"

    LOG_FILE: str = "/var/log/bot/bot.log"
    LOG_LEVEL: str = "INFO"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5


settings = Settings()
