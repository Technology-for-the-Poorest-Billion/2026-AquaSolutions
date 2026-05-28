"""SQLAlchemy engine factory.

A single module-level singleton engine is built lazily on first call to
get_engine(). The DB URL is read from DATABASE_URL — Railway sets this
to a postgresql+psycopg://… string; local dev and tests use sqlite:///.

If DATABASE_URL is unset, falls back to a SQLite file at
App/backend/data/water_safety.db so existing local workflows keep working.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

BACKEND_DIR = Path(__file__).resolve().parent

_engine: Optional[Engine] = None


def _resolve_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        # Railway historically supplies postgresql://; SQLAlchemy 2.x prefers the
        # explicit driver prefix postgresql+psycopg:// for psycopg 3.
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    # Fallback: local SQLite file.
    db_path = BACKEND_DIR / "data" / "water_safety.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path}"


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_resolve_url(), future=True)
    return _engine


def reset_engine_for_tests() -> None:
    """Drop the cached engine so the next get_engine() picks up new env vars.

    Used by the test fixture to rebuild the engine against the per-test
    DATABASE_URL.
    """
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
