"""Runtime settings loaded from environment variables (.env supported)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    llm_provider: str
    llm_model: str
    gemini_api_key: str | None
    reference_date: date
    history_ttl_days: int
    db_path: Path
    data_dir: Path


def _resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def get_settings() -> Settings:
    return Settings(
        llm_provider=os.getenv("LLM_PROVIDER", "gemini"),
        llm_model=os.getenv("LLM_MODEL", "gemini-3.5-flash-lite"),
        gemini_api_key=os.getenv("GEMINI_API_KEY") or None,
        reference_date=date.fromisoformat(os.getenv("REFERENCE_DATE", "2026-03-25")),
        history_ttl_days=int(os.getenv("HISTORY_TTL_DAYS", "7")),
        db_path=_resolve(os.getenv("DB_PATH", "var/conversations.sqlite3")),
        data_dir=_resolve(os.getenv("DATA_DIR", "data/raw")),
    )
