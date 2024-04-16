"""Runtime settings, read from the environment (and `.env` when present)."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/llmdatabase.db"))
    store_prompts: bool = field(
        default_factory=lambda: os.getenv("STORE_PROMPTS", "true").lower() in ("1", "true", "yes")
    )
    cors_origins: list[str] = field(default_factory=_origins)


settings = Settings()
