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

    from engine import get_engine

    engine = get_engine()
    # SQLite engines expose their URL with .url; the path should end in water_safety.db
    assert str(engine.url).endswith("water_safety.db")
    assert engine.url.drivername.startswith("sqlite")


def test_engine_rewrites_postgresql_url_for_psycopg(monkeypatch):
    """Bare postgresql:// URLs are rewritten to postgresql+psycopg:// so SQLAlchemy 2.x routes through psycopg 3."""
    sys.modules.pop("engine", None)
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pw@host:5432/db")
    from engine import get_engine

    engine = get_engine()
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.url.host == "host"
        assert engine.url.database == "db"
    finally:
        engine.dispose()


def test_engine_rewrites_short_postgres_url_for_psycopg(monkeypatch):
    """The short postgres:// form (Heroku/older Railway) is also rewritten."""
    sys.modules.pop("engine", None)
    monkeypatch.setenv("DATABASE_URL", "postgres://user:pw@host:5432/db")
    from engine import get_engine

    engine = get_engine()
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.url.host == "host"
        assert engine.url.database == "db"
    finally:
        engine.dispose()
