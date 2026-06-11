"""Migration / schema invariants — portable between SQLite and Postgres."""

from __future__ import annotations

import sys

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_stations_has_is_closed_column(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    cols = {c["name"] for c in inspect(get_engine()).get_columns("stations")}
    assert "is_closed" in cols


def test_interventions_table_exists_and_rejects_bad_action(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    engine = get_engine()

    tables = set(inspect(engine).get_table_names())
    assert "interventions" in tables

    cols = {c["name"] for c in inspect(engine).get_columns("interventions")}
    assert {
        "intervention_id", "station_id", "action_type", "triggered_by",
        "triggered_at", "related_report_id", "notes",
    }.issubset(cols)

    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO interventions (station_id, action_type, triggered_by) "
                    "VALUES (1, 'not_a_real_action', 'tester')"
                )
            )


def test_illness_reports_has_phase_d_e_f_columns(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    cols = {c["name"] for c in inspect(get_engine()).get_columns("illness_reports")}
    for expected in ("risk_tier", "dialog_state", "case_count", "symptoms", "onset_date"):
        assert expected in cols


def test_risk_tier_rejects_invalid_value(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine
    from sqlalchemy import text

    init_db()
    engine = get_engine()
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO illness_reports "
                    "(reporter_phone, raw_message, parser_version, risk_tier) "
                    "VALUES ('+1', 'msg', 'v', 'banana')"
                )
            )


def test_dialog_state_rejects_invalid_value(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db
    from engine import get_engine

    init_db()
    engine = get_engine()
    with pytest.raises(IntegrityError):
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO illness_reports "
                    "(reporter_phone, raw_message, parser_version, dialog_state) "
                    "VALUES ('+1', 'msg', 'v', 'orange')"
                )
            )
