"""Runtime settings, read from the environment (and `.env` when present)."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    return int(raw) if raw else default


def _origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    # "openai" calls the model; "demo" uses the offline name matcher. Without a key
    # the app falls back to demo so a fresh checkout still works end to end.
    llm_mode: str = field(default_factory=lambda: os.getenv("LLM_MODE", ""))
    database_url: str = field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./data/llmdatabase.db"))
    store_prompts: bool = field(
        default_factory=lambda: os.getenv("STORE_PROMPTS", "true").lower() in ("1", "true", "yes")
    )
    max_upload_bytes: int = field(default_factory=lambda: _int_env("MAX_UPLOAD_BYTES", 2 * 1024 * 1024))
    max_columns: int = field(default_factory=lambda: _int_env("MAX_COLUMNS", 200))
    script_timeout_seconds: int = field(default_factory=lambda: _int_env("SCRIPT_TIMEOUT_SECONDS", 10))
    cors_origins: list[str] = field(default_factory=_origins)

    @property
    def effective_llm_mode(self) -> str:
        if self.llm_mode in ("openai", "demo"):
            return self.llm_mode
        return "openai" if self.openai_api_key else "demo"


settings = Settings()
