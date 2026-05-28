"""Smoke test for the SQLAlchemy engine factory."""

from __future__ import annotations

import os
import sys

from sqlalchemy import text


def test_engine_runs_select_one_against_sqlite(monkeypatch, tmp_path):
    """get_engine() returns an Engine that executes SELECT 1 = 1 on a tempfile SQLite."""
    sys.modules.pop("engine", None)
    db_file = tmp_path / "engine-smoke.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    # Import lazily so the env var is honoured.
    from engine import get_engine

    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS one")).scalar_one()
    assert result == 1


def test_engine_defaults_to_sqlite_data_path(monkeypatch, tmp_path):
    """With no DATABASE_URL set, get_engine() falls back to data/water_safety.db relative to backend dir."""
    sys.modules.pop("engine", None)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)

    from engine import get_engine

    engine = get_engine()
    # SQLite engines expose their URL with .url; the path should end in water_safety.db
    assert str(engine.url).endswith("water_safety.db")
    assert engine.url.drivername.startswith("sqlite")
