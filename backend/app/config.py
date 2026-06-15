"""Runtime configuration. The OpenAI key is read from the environment only and
is never logged or returned to the client."""
from __future__ import annotations
import os
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env() -> str:
    """Locate the untracked .env by walking up from this file, so the app finds
    it whether launched from repo root, backend/, or a container workdir."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            return str(candidate)
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_find_env(), extra="ignore")

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"
    database_url: str = "sqlite:///./harness.db"
    max_live_personas: int = 6
    max_turns_per_skill: int = 6

    @property
    def live_enabled(self) -> bool:
        """True when a real key is present. When false the app runs in a
        deterministic mock mode so every screen still works end to end."""
        return bool(self.openai_api_key and self.openai_api_key.startswith("sk-"))


@lru_cache
def get_settings() -> Settings:
    # Railway provides DATABASE_URL via env; normalise the old postgres:// scheme.
    url = os.environ.get("DATABASE_URL", "")
    if url.startswith("postgres://"):
        os.environ["DATABASE_URL"] = url.replace("postgres://", "postgresql://", 1)
    return Settings()
