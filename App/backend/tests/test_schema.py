"""Tests that the SQLAlchemy schema can be created on a fresh SQLite DB
and that the expected tables and columns exist."""

from __future__ import annotations

import sys

from sqlalchemy import inspect


EXPECTED_TABLES = {
    "stations",
    "sensor_readings",
    "illness_reports",
    "reading_labels",
    "interventions",
    "user_preferences",
}

EXPECTED_REPORT_COLUMNS = {
    "report_id", "station_id", "reporter_phone", "raw_message",
    "parser_version", "received_at", "report_source", "submitter",
    "case_count", "onset_date", "symptoms", "risk_tier", "dialog_state",
}


def test_schema_creates_all_tables(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    insp = inspect(get_engine())
    assert EXPECTED_TABLES.issubset(set(insp.get_table_names()))


def test_illness_reports_has_all_columns(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    insp = inspect(get_engine())
    cols = {c["name"] for c in insp.get_columns("illness_reports")}
    assert EXPECTED_REPORT_COLUMNS.issubset(cols)


def test_stations_seeded_idempotently(tmp_db_path):
    """init_db() seeds 10 stations and re-running does not duplicate them."""
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine
    from sqlalchemy import text

    init_db()
    init_db()  # second call should be a no-op for seed
    with get_engine().connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM stations")).scalar_one()
    assert n == 10
