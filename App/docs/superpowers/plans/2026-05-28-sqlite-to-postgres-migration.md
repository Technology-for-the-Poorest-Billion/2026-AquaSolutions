# SQLite → Postgres Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the on-disk SQLite database with Railway Postgres so reports, sensor readings, interventions, and labels survive container restarts and redeploys.

**Architecture:** Introduce SQLAlchemy Core as a thin portability layer. Schema moves from a raw `CREATE TABLE` string to `MetaData` + `Table` objects so the same code emits SQLite DDL locally and Postgres DDL on Railway. All call sites switch from positional-`?` `sqlite3` calls to named-parameter `text()` calls. Backend selection is keyed off a single `DATABASE_URL` env var: `sqlite:///…` locally and in tests, `postgresql+psycopg://…` on Railway.

**Tech Stack:** Flask 3.0.3, SQLAlchemy 2.0.x, psycopg 3 (binary), Railway Postgres, gunicorn 23, pytest 8.3. SQLite via Python's stdlib stays as the default for local dev and the test suite — no Postgres install required for `pytest`.

**Out of scope:** `feature_engineering.py` (offline ML pipeline; opens its own SQLite connection, not part of the Flask request path — leave on SQLite for now, document the constraint). Alembic migrations. Test-running against a real Postgres instance (one optional smoke test only).

**Deadline context:** Interim presentation 2026-06-01, submission 2026-06-11. This plan is scoped to be done in a single focused day — about 10 tasks of 20–40 minutes each. If a task balloons, stop and revisit scope before continuing.

---

## File Structure

**Files created:**
- `App/backend/engine.py` — SQLAlchemy `Engine` factory keyed off `DATABASE_URL`. Single responsibility: build the engine and expose it as a module-level singleton.

**Files modified:**
- `App/backend/database.py` — schema strings → `MetaData` + `Table`s; `_migrate()` switches from `PRAGMA table_info` to `sqlalchemy.inspect`; `connection()` yields a SQLAlchemy `Connection`; `INSERT OR IGNORE` → `ON CONFLICT DO NOTHING`.
- `App/backend/app.py` — every `conn.execute(sql, tuple)` → `conn.execute(text(sql), dict)`; `cursor.lastrowid` → `RETURNING` clause; commits inside `with conn.begin()` blocks where writes happen.
- `App/backend/sensor_ingest.py` — same porting pattern as `app.py`.
- `App/backend/labels.py` — same; the type hint `sqlite3.Connection` becomes `sqlalchemy.Connection`.
- `App/backend/conftest.py` — `DATABASE_PATH` env var → `DATABASE_URL`; tempfile path becomes `sqlite:///<path>` URL.
- `App/backend/tests/test_migrations.py` — `PRAGMA table_info(t)` → `inspect(engine).get_columns('t')`; `sqlite3.IntegrityError` → `sqlalchemy.exc.IntegrityError`.
- `App/backend/requirements.txt` — add `SQLAlchemy==2.0.36` and `psycopg[binary]==3.2.3`.
- `App/backend/Procfile` — add a release-phase command to run `init_db()` so schema exists before first request.

**Files NOT modified (intentionally):**
- `App/backend/feature_engineering.py` — offline pipeline, separate concern, stays on SQLite. Add a one-line comment at the top of `_open_db` clarifying this.
- `App/backend/sms_dialog.py`, `App/backend/estimator.py` — pure parsing/logic, no DB touched.

**Railway-side change (manual, outside repo):**
- Add a Postgres database service to the Railway project.
- Set `DATABASE_URL` env var on the web service to point at the Postgres service's internal URL (Railway exposes it as a templated reference).

---

## Conventions used in this plan

- All test commands assume `cd App/backend` then `pytest`. The conftest adds `App/backend` to `sys.path`.
- All SQL in code uses **named parameters** (`:foo`) so the same `text()` runs on both SQLite and Postgres.
- Commits are atomic per task; messages follow the existing `Phase X: …` convention but use `Postgres: …` as the prefix for this migration.

---

## Task 1: Add deps and create the engine module

**Files:**
- Modify: `App/backend/requirements.txt`
- Create: `App/backend/engine.py`
- Create: `App/backend/tests/test_engine.py`

- [ ] **Step 1: Write the failing test**

Create `App/backend/tests/test_engine.py`:

```python
"""Smoke test for the SQLAlchemy engine factory."""

from __future__ import annotations

import os

from sqlalchemy import text


def test_engine_runs_select_one_against_sqlite(monkeypatch, tmp_path):
    """get_engine() returns an Engine that executes SELECT 1 = 1 on a tempfile SQLite."""
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
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_PATH", raising=False)

    from engine import get_engine

    engine = get_engine()
    # SQLite engines expose their URL with .url; the path should end in water_safety.db
    assert str(engine.url).endswith("water_safety.db")
    assert engine.url.drivername.startswith("sqlite")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd App/backend && pytest tests/test_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engine'` (and `sqlalchemy` if not yet installed).

- [ ] **Step 3: Install new deps**

Update `App/backend/requirements.txt`:

```
Flask==3.0.3
twilio==9.3.7
gunicorn==23.0.0
python-dotenv==1.0.1
SQLAlchemy==2.0.36
psycopg[binary]==3.2.3
pandas>=2.0
numpy>=1.26
scikit-learn>=1.4
xgboost>=2.0
pytest==8.3.3
```

Then install in the active venv:

```bash
.venv/bin/pip install SQLAlchemy==2.0.36 'psycopg[binary]==3.2.3'
```

- [ ] **Step 4: Implement `engine.py`**

Create `App/backend/engine.py`:

```python
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd App/backend && pytest tests/test_engine.py -v`
Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add App/backend/engine.py App/backend/tests/test_engine.py App/backend/requirements.txt
git commit -m "Postgres: add SQLAlchemy engine factory keyed off DATABASE_URL"
```

---

## Task 2: Define schema via SQLAlchemy MetaData

**Files:**
- Modify: `App/backend/database.py`
- Create: `App/backend/tests/test_schema.py`

**Why this is its own task:** The schema definition is the highest-leverage piece — it has to emit valid DDL for both SQLite and Postgres. Doing it first means every subsequent task has a working schema to insert into.

- [ ] **Step 1: Write the failing test**

Create `App/backend/tests/test_schema.py`:

```python
"""Tests that the SQLAlchemy schema can be created on a fresh SQLite DB
and that the expected tables and columns exist."""

from __future__ import annotations

from sqlalchemy import inspect


EXPECTED_TABLES = {
    "stations",
    "sensor_readings",
    "illness_reports",
    "reading_labels",
    "interventions",
}

EXPECTED_REPORT_COLUMNS = {
    "report_id", "station_id", "reporter_phone", "raw_message",
    "parser_version", "received_at", "report_source", "submitter",
    "case_count", "onset_date", "symptoms", "risk_tier", "dialog_state",
}


def test_schema_creates_all_tables(tmp_db_path):
    from database import init_db
    from engine import get_engine

    init_db()
    insp = inspect(get_engine())
    assert EXPECTED_TABLES.issubset(set(insp.get_table_names()))


def test_illness_reports_has_all_columns(tmp_db_path):
    from database import init_db
    from engine import get_engine

    init_db()
    insp = inspect(get_engine())
    cols = {c["name"] for c in insp.get_columns("illness_reports")}
    assert EXPECTED_REPORT_COLUMNS.issubset(cols)


def test_stations_seeded_idempotently(tmp_db_path):
    """init_db() seeds 10 stations and re-running does not duplicate them."""
    from database import init_db
    from engine import get_engine
    from sqlalchemy import text

    init_db()
    init_db()  # second call should be a no-op for seed
    with get_engine().connect() as conn:
        n = conn.execute(text("SELECT COUNT(*) FROM stations")).scalar_one()
    assert n == 10
```

(The `tmp_db_path` fixture is updated in Task 8 to point `DATABASE_URL` at the scratch SQLite file. This test will start failing-for-wrong-reasons until then — that's expected and noted in Step 2 below.)

- [ ] **Step 2: Run test to verify it fails**

Run: `cd App/backend && pytest tests/test_schema.py -v`
Expected: FAIL — the existing `tmp_db_path` fixture sets `DATABASE_PATH` (which `engine.py` ignores), so the new engine still points at the default `data/water_safety.db` file. The fixture rewrite in Task 8 closes this gap; for now confirm the failure is "schema mismatch" / "engine pointing at wrong file" rather than an import error.

(If you want a clean run for this task only, set `DATABASE_URL=sqlite:///:memory:` in front of the pytest command and the test should pass once Step 4 lands. Don't commit the env var — it's only for local verification.)

- [ ] **Step 3: Rewrite `database.py` using MetaData**

Replace the entire contents of `App/backend/database.py` with:

```python
"""Schema definition + init for the Gen-1 water-safety backend.

Schema is declared as SQLAlchemy MetaData/Table objects so the same code
emits SQLite DDL locally and Postgres DDL on Railway. init_db() is
idempotent: it creates any missing tables, adds any newly-added columns
on existing tables, and seeds the 10 stations row by row with
ON CONFLICT DO NOTHING.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import (
    CheckConstraint, Column, ForeignKey, Index, Integer, MetaData, Table,
    Text, UniqueConstraint, func, inspect, text,
)
from sqlalchemy.engine import Connection

from engine import get_engine


metadata = MetaData()


stations = Table(
    "stations", metadata,
    Column("station_id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, nullable=False),
    Column("latitude", Integer),  # REAL in SQLite is sloppy; SQLAlchemy Float would be fine here
    Column("longitude", Integer),
    Column("is_closed", Integer, nullable=False, server_default=text("0")),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
)
# Note: latitude/longitude are stored as REAL/double precision. Use Integer here
# is wrong — fix below in Step 3a.


sensor_readings = Table(
    "sensor_readings", metadata,
    Column("reading_id", Integer, primary_key=True, autoincrement=True),
    Column("station_id", Integer, ForeignKey("stations.station_id"), nullable=False),
    Column("recorded_at", Text, nullable=False),
    Column("ph", Integer),
    Column("turbidity_ntu", Integer),
    Column("temperature_c", Integer),
    Column("rainfall_mm", Integer),
    Column("provenance", Text, nullable=False, server_default=text("'unknown'")),
    Column("received_at", Text, nullable=False, server_default=func.current_timestamp()),
    Index("idx_readings_station_time", "station_id", "recorded_at"),
)


illness_reports = Table(
    "illness_reports", metadata,
    Column("report_id", Integer, primary_key=True, autoincrement=True),
    Column("station_id", Integer, ForeignKey("stations.station_id")),
    Column("reporter_phone", Text),
    Column("raw_message", Text, nullable=False),
    Column("parser_version", Text, nullable=False),
    Column("received_at", Text, nullable=False, server_default=func.current_timestamp()),
    Column("report_source", Text, nullable=False, server_default=text("'sms'")),
    Column("submitter", Text),
    Column("case_count", Integer),
    Column("onset_date", Text),
    Column("symptoms", Text),
    Column("risk_tier", Text),
    Column("dialog_state", Text),
    CheckConstraint(
        "report_source IN ('sms', 'medical_portal')",
        name="ck_illness_reports_source",
    ),
    CheckConstraint(
        "risk_tier IS NULL OR risk_tier IN ('low','medium','high','severe')",
        name="ck_illness_reports_risk_tier",
    ),
    CheckConstraint(
        "dialog_state IS NULL OR dialog_state IN "
        "('awaiting_case_count','awaiting_symptoms','awaiting_onset','complete','abandoned')",
        name="ck_illness_reports_dialog_state",
    ),
    Index("idx_reports_station_time", "station_id", "received_at"),
)


reading_labels = Table(
    "reading_labels", metadata,
    Column("label_id", Integer, primary_key=True, autoincrement=True),
    Column("reading_id", Integer, ForeignKey("sensor_readings.reading_id"), nullable=False),
    Column("report_id", Integer, ForeignKey("illness_reports.report_id"), nullable=False),
    Column("label", Text, nullable=False),
    Column("rule_description", Text, nullable=False),
    Column("labelled_at", Text, nullable=False, server_default=func.current_timestamp()),
    CheckConstraint("label IN ('unsafe', 'suspect')", name="ck_reading_labels_label"),
    UniqueConstraint("reading_id", "report_id", name="uq_reading_labels_reading_report"),
    Index("idx_labels_reading", "reading_id"),
)


interventions = Table(
    "interventions", metadata,
    Column("intervention_id", Integer, primary_key=True, autoincrement=True),
    Column("station_id", Integer, ForeignKey("stations.station_id"), nullable=False),
    Column("action_type", Text, nullable=False),
    Column("triggered_by", Text, nullable=False),
    Column("triggered_at", Text, nullable=False, server_default=func.current_timestamp()),
    Column("related_report_id", Integer, ForeignKey("illness_reports.report_id")),
    Column("notes", Text),
    CheckConstraint(
        "action_type IN ('close_borehole', 'reopen_borehole', "
        "'dispatch_sample_team', 'dispatch_medical_team')",
        name="ck_interventions_action_type",
    ),
    Index("idx_interventions_station_time", "station_id", "triggered_at"),
    Index("idx_interventions_report", "related_report_id"),
)


SEED_STATIONS = [
    (1,  "Borehole A — village centre",   -17.829, 31.052),
    (2,  "Borehole B — clinic",           -17.831, 31.057),
    (3,  "Borehole C — school",           -17.828, 31.049),
    (4,  "Borehole D — market",           -17.833, 31.054),
    (5,  "Borehole E — north well",       -17.820, 31.060),
    (6,  "Borehole F — east settlement",  -17.836, 31.069),
    (7,  "Borehole G — south farm",       -17.847, 31.055),
    (8,  "Borehole H — west outpost",     -17.838, 31.041),
    (9,  "Borehole I — river crossing",   -17.826, 31.073),
    (10, "Borehole J — bus station",      -17.842, 31.062),
]


# Columns that may be missing from an existing illness_reports table on an
# older deploy. Re-applied idempotently in _migrate.
_REPORT_BACKFILL_COLUMNS = [
    ("report_source", "TEXT NOT NULL DEFAULT 'sms'"),
    ("submitter",     "TEXT"),
    ("case_count",    "INTEGER"),
    ("onset_date",    "TEXT"),
    ("symptoms",      "TEXT"),
    ("risk_tier",     "TEXT"),
    ("dialog_state",  "TEXT"),
]


@contextmanager
def connection() -> Iterator[Connection]:
    """Yield a SQLAlchemy connection. Callers wrap writes in conn.begin()."""
    conn = get_engine().connect()
    try:
        yield conn
    finally:
        conn.close()


def _migrate(conn: Connection) -> None:
    """Add columns introduced after the original schema, idempotently.

    Uses SQLAlchemy's inspect() so it works on both SQLite (PRAGMA-backed
    introspection) and Postgres (information_schema-backed).
    """
    insp = inspect(conn)
    existing_report_cols = {c["name"] for c in insp.get_columns("illness_reports")}
    for col_name, col_type in _REPORT_BACKFILL_COLUMNS:
        if col_name not in existing_report_cols:
            conn.execute(text(
                f"ALTER TABLE illness_reports ADD COLUMN {col_name} {col_type}"
            ))

    existing_station_cols = {c["name"] for c in insp.get_columns("stations")}
    if "is_closed" not in existing_station_cols:
        conn.execute(text(
            "ALTER TABLE stations ADD COLUMN is_closed INTEGER NOT NULL DEFAULT 0"
        ))


def init_db() -> None:
    """Create all tables, run any needed column-level migrations, and seed stations.

    Safe to call repeatedly. Designed to run on every Flask startup.
    """
    engine = get_engine()
    metadata.create_all(engine)
    with engine.begin() as conn:
        _migrate(conn)
        # ON CONFLICT DO NOTHING is portable across SQLite 3.24+ and Postgres 9.5+.
        # Bind as a parameterised statement to avoid SQL injection on the name field.
        for sid, name, lat, lon in SEED_STATIONS:
            conn.execute(
                text(
                    "INSERT INTO stations (station_id, name, latitude, longitude) "
                    "VALUES (:sid, :name, :lat, :lon) "
                    "ON CONFLICT (station_id) DO NOTHING"
                ),
                {"sid": sid, "name": name, "lat": lat, "lon": lon},
            )


if __name__ == "__main__":
    init_db()
    print(f"Initialised database at {get_engine().url}")
```

- [ ] **Step 3a: Fix the latitude/longitude column type**

Change the two `Column("latitude", Integer)` / `Column("longitude", Integer)` lines in the `stations` table definition to use `Float`:

```python
from sqlalchemy import Float  # add to the existing sqlalchemy import line at the top

# ... in the stations Table definition:
    Column("latitude", Float),
    Column("longitude", Float),
```

And do the same for the four numeric sensor columns in `sensor_readings` (`ph`, `turbidity_ntu`, `temperature_c`, `rainfall_mm`) — they're real-valued, not integers.

- [ ] **Step 4: Run the test**

Run: `cd App/backend && DATABASE_URL=sqlite:///:memory: pytest tests/test_schema.py -v`
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add App/backend/database.py App/backend/tests/test_schema.py
git commit -m "Postgres: declare schema via SQLAlchemy MetaData, portable to Postgres"
```

---

## Task 3: Update conftest to use DATABASE_URL

**Files:**
- Modify: `App/backend/conftest.py`

**Why now:** Every other task's test suite depends on the conftest fixture pointing at a per-test scratch DB via `DATABASE_URL` (not the old `DATABASE_PATH`). Do this before porting application code.

- [ ] **Step 1: Read the existing fixture** (already done — keep `tmp_db_path` name but switch the env var)

- [ ] **Step 2: Rewrite conftest.py**

Replace `App/backend/conftest.py`:

```python
"""Pytest fixtures.

Each test gets its own fresh SQLite DB at a tempfile path. The Flask
app reads DATABASE_URL from os.environ via engine.get_engine().
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture()
def tmp_db_path(monkeypatch):
    """Per-test scratch SQLite DB. The engine module's cached engine is
    reset so the next get_engine() picks up the new URL."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{path}")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("MEDICAL_PASSWORD", "med-pw")
    monkeypatch.setenv("GOV_PASSWORD", "gov-pw")
    monkeypatch.setenv("DEVICE_SECRET", "test-device-secret")
    monkeypatch.setenv("TWILIO_VALIDATE_SIGNATURES", "false")

    # Drop any cached engine from a previous test so the new URL is honoured.
    sys.modules.pop("engine", None)

    yield path
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@pytest.fixture()
def app(tmp_db_path):
    """Fresh Flask app bound to the scratch DB. Re-imports so module
    state (DEMO_USERS, init_db, the engine singleton) is rebuilt."""
    for mod in ("app", "database", "labels", "sensor_ingest", "engine"):
        sys.modules.pop(mod, None)
    import app as app_mod
    return app_mod.app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def gov_session(client):
    client.post("/login", data={"username": "official.jones", "password": "gov-pw"})
    return client


@pytest.fixture()
def med_session(client):
    client.post("/login", data={"username": "dr.smith", "password": "med-pw"})
    return client
```

- [ ] **Step 3: Run schema tests without the env var workaround**

Run: `cd App/backend && pytest tests/test_schema.py tests/test_engine.py -v`
Expected: 5 passed (no `DATABASE_URL=...` prefix needed now).

- [ ] **Step 4: Commit**

```bash
git add App/backend/conftest.py
git commit -m "Postgres: switch test fixture from DATABASE_PATH to DATABASE_URL"
```

---

## Task 4: Port `sensor_ingest.py`

**Files:**
- Modify: `App/backend/sensor_ingest.py`

- [ ] **Step 1: Run the existing /ingest tests to see them fail**

Run: `cd App/backend && pytest tests/test_smoke.py -v -k ingest` (adjust `-k` based on which tests exercise `/ingest`)
Expected: FAIL — old `sensor_ingest.py` calls `conn.execute(sql, (tuple,))` on a SQLAlchemy connection, which doesn't accept positional tuples.

(If the smoke tests don't already cover `/ingest`, write one in `tests/test_ingest.py` before porting: POST a valid payload, assert 201 + the row appears in `sensor_readings`.)

- [ ] **Step 2: Rewrite sensor_ingest.py**

Replace `App/backend/sensor_ingest.py`:

```python
"""Blueprint for POST /ingest — receives sensor readings from field nodes."""

from __future__ import annotations

import os
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import text

from database import connection

sensor_bp = Blueprint("sensor_ingest", __name__)


REQUIRED_FIELDS = ("station_id", "recorded_at")
OPTIONAL_NUMERIC = ("ph", "turbidity_ntu", "temperature_c", "rainfall_mm")


def _authorised(req) -> bool:
    expected = os.environ.get("DEVICE_SECRET", "")
    if not expected:
        return False
    return req.headers.get("X-Device-Secret") == expected


@sensor_bp.post("/ingest")
def ingest():
    if not _authorised(request):
        return jsonify(error="unauthorised"), 401

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="json body required"), 400

    for field in REQUIRED_FIELDS:
        if field not in payload:
            return jsonify(error=f"missing field: {field}"), 400

    try:
        station_id = int(payload["station_id"])
        recorded_at = datetime.fromisoformat(str(payload["recorded_at"]))
    except (TypeError, ValueError):
        return jsonify(error="invalid station_id or recorded_at"), 400

    numeric_values = {}
    for field in OPTIONAL_NUMERIC:
        raw = payload.get(field)
        if raw is None:
            numeric_values[field] = None
            continue
        try:
            numeric_values[field] = float(raw)
        except (TypeError, ValueError):
            return jsonify(error=f"invalid numeric value for {field}"), 400

    provenance = str(payload.get("provenance", "unknown"))

    with connection() as conn:
        with conn.begin():
            station = conn.execute(
                text("SELECT 1 FROM stations WHERE station_id = :sid"),
                {"sid": station_id},
            ).first()
            if station is None:
                return jsonify(error=f"unknown station_id: {station_id}"), 400

            reading_id = conn.execute(
                text(
                    "INSERT INTO sensor_readings "
                    "(station_id, recorded_at, ph, turbidity_ntu, "
                    " temperature_c, rainfall_mm, provenance) "
                    "VALUES (:station_id, :recorded_at, :ph, :turbidity_ntu, "
                    " :temperature_c, :rainfall_mm, :provenance) "
                    "RETURNING reading_id"
                ),
                {
                    "station_id": station_id,
                    "recorded_at": recorded_at.isoformat(),
                    "ph": numeric_values["ph"],
                    "turbidity_ntu": numeric_values["turbidity_ntu"],
                    "temperature_c": numeric_values["temperature_c"],
                    "rainfall_mm": numeric_values["rainfall_mm"],
                    "provenance": provenance,
                },
            ).scalar_one()

    return jsonify(status="ok", reading_id=reading_id), 201
```

**Note on `RETURNING`:** SQLite added `RETURNING` in 3.35 (March 2021). Modern Python ships with that or newer. Confirm with `python -c "import sqlite3; print(sqlite3.sqlite_version)"` if uncertain — must be ≥ 3.35.

- [ ] **Step 3: Run the tests**

Run: `cd App/backend && pytest tests/test_smoke.py -v -k ingest`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add App/backend/sensor_ingest.py
git commit -m "Postgres: port /ingest to SQLAlchemy text() with RETURNING"
```

---

## Task 5: Port `labels.py`

**Files:**
- Modify: `App/backend/labels.py`

- [ ] **Step 1: Run the existing label tests to see them fail**

Run: `cd App/backend && pytest tests/ -v -k label`
Expected: FAIL on the old `conn.execute(sql, tuple)` shape.

- [ ] **Step 2: Rewrite labels.py**

Replace the `label_readings_for_report` function body in `App/backend/labels.py` (keep the long docstring header and the STUDENT EXTENSION POINT block at the bottom unchanged). Replace the imports and function with:

```python
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

DEFAULT_WINDOW_DAYS = 7
DEFAULT_LABEL = "unsafe"
RULE_VERSION = "trailing_7d_v1"


def label_readings_for_report(
    conn: Connection,
    report_id: int,
    station_id: int,
    report_time: datetime,
    window_days: int = DEFAULT_WINDOW_DAYS,
) -> int:
    """Label the trailing window of readings at ``station_id`` as unsafe.

    Returns the number of readings newly labelled. Idempotent via the
    UNIQUE(reading_id, report_id) constraint on reading_labels.
    """
    window_start = report_time - timedelta(days=window_days)

    target_readings = conn.execute(
        text(
            "SELECT reading_id FROM sensor_readings "
            "WHERE station_id = :sid "
            "  AND recorded_at >= :ws "
            "  AND recorded_at <= :rt"
        ),
        {
            "sid": station_id,
            "ws": window_start.isoformat(),
            "rt": report_time.isoformat(),
        },
    ).all()

    if not target_readings:
        return 0

    rule_description = (
        f"{RULE_VERSION}: trailing {window_days}d window at station "
        f"{station_id} anchored at report receipt"
    )

    inserted = 0
    for row in target_readings:
        result = conn.execute(
            text(
                "INSERT INTO reading_labels "
                "(reading_id, report_id, label, rule_description) "
                "VALUES (:rid, :rep, :label, :rule) "
                "ON CONFLICT (reading_id, report_id) DO NOTHING"
            ),
            {
                "rid": row.reading_id,
                "rep": report_id,
                "label": DEFAULT_LABEL,
                "rule": rule_description,
            },
        )
        # SQLAlchemy reports rowcount as the number of rows affected;
        # an ON CONFLICT-skipped row reports 0.
        inserted += result.rowcount

    return inserted
```

- [ ] **Step 3: Run the tests**

Run: `cd App/backend && pytest tests/ -v -k label`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add App/backend/labels.py
git commit -m "Postgres: port label_readings_for_report to SQLAlchemy text()"
```

---

## Task 6: Port `app.py` — dashboard route

**Files:**
- Modify: `App/backend/app.py` (lines 588-658, the `dashboard()` view + its query)

**Why split app.py by route:** `app.py` has 15+ queries across 7 routes. Porting one route at a time keeps each change reviewable and lets each route's existing test suite act as the regression gate.

- [ ] **Step 1: Run dashboard tests, see them fail**

Run: `cd App/backend && pytest tests/test_dashboard_with_tier.py tests/test_dashboard_actions.py -v`
Expected: FAIL on `conn.execute(sql, tuple)`.

- [ ] **Step 2: Port the dashboard view**

In `App/backend/app.py`, replace the `dashboard()` function with:

```python
@app.get("/dashboard")
@role_required("government")
def dashboard():
    status_cutoff = (
        datetime.now(timezone.utc) - timedelta(days=STATION_STATUS_WINDOW_DAYS)
    ).isoformat()

    with connection() as conn:
        stations = conn.execute(
            text("""
                WITH latest AS (
                    SELECT station_id, MAX(recorded_at) AS latest_at
                    FROM sensor_readings
                    GROUP BY station_id
                )
                SELECT s.station_id,
                       s.name,
                       s.is_closed,
                       r.recorded_at,
                       r.ph,
                       r.turbidity_ntu,
                       r.temperature_c,
                       r.rainfall_mm,
                       EXISTS (
                           SELECT 1 FROM illness_reports ir
                           WHERE ir.station_id = s.station_id
                             AND ir.received_at >= :cutoff
                       ) AS is_unsafe
                FROM stations s
                LEFT JOIN latest l ON l.station_id = s.station_id
                LEFT JOIN sensor_readings r
                    ON r.station_id = s.station_id
                   AND r.recorded_at = l.latest_at
                ORDER BY s.station_id
            """),
            {"cutoff": status_cutoff},
        ).mappings().all()

        reports = conn.execute(
            text("""
                SELECT ir.report_id, ir.station_id, s.name AS station_name,
                       ir.reporter_phone, ir.raw_message, ir.received_at,
                       ir.risk_tier, ir.report_source,
                       ir.case_count, ir.symptoms, ir.onset_date,
                       (SELECT COUNT(*) FROM reading_labels
                         WHERE report_id = ir.report_id) AS readings_labelled
                FROM illness_reports ir
                LEFT JOIN stations s ON s.station_id = ir.station_id
                ORDER BY ir.received_at DESC
                LIMIT 50
            """),
        ).mappings().all()

        reports_with_tier = [
            {**dict(rep), "tier_block": _resolve_tier(dict(rep))}
            for rep in reports
        ]

    return render_template(
        "dashboard.html",
        stations=stations,
        reports=reports_with_tier,
        status_window_days=STATION_STATUS_WINDOW_DAYS,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
```

Also add to the imports at the top of `app.py`:

```python
from sqlalchemy import text
```

**Note on `.mappings().all()`:** Returns a list of dict-like `RowMapping` objects so the template's `s['station_id']` access still works. Without `.mappings()`, you'd get `Row` tuples and the template would break.

**Note on `LEFT JOIN ... USING`:** The original used `LEFT JOIN latest l USING (station_id)`. Postgres requires the join column to be the same type on both sides and isn't tolerant of mismatches — switching to explicit `ON l.station_id = s.station_id` avoids that whole class of footgun.

- [ ] **Step 3: Run dashboard tests**

Run: `cd App/backend && pytest tests/test_dashboard_with_tier.py tests/test_dashboard_actions.py -v`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add App/backend/app.py
git commit -m "Postgres: port /dashboard view to SQLAlchemy text()"
```

---

## Task 7: Port `app.py` — medical report routes

**Files:**
- Modify: `App/backend/app.py` (the `medical_report_form` GET, `medical_report_submit` POST, `medical_history` GET, `medical_report_detail` GET)

- [ ] **Step 1: Run medical tests, see them fail**

Run: `cd App/backend && pytest tests/test_medical_form.py tests/test_medical_history.py tests/test_medical_detail_page.py -v`
Expected: FAIL.

- [ ] **Step 2: Port `medical_report_form` (GET)**

Replace the function body:

```python
@app.get("/medical/report")
@role_required("medical")
def medical_report_form():
    with connection() as conn:
        stations = conn.execute(
            text("SELECT station_id, name FROM stations ORDER BY station_id")
        ).mappings().all()
    return render_template(
        "medical_report.html",
        stations=stations,
        symptoms=SYMPTOMS,
        success_message=None,
        error_message=None,
    )
```

- [ ] **Step 3: Port `medical_report_submit` (POST)**

Replace the function. The key changes are: wrap writes in `conn.begin()`, use `text()` + named params, capture `report_id` via `RETURNING`. The inner `render` helper also needs porting:

```python
@app.post("/medical/report")
@role_required("medical")
def medical_report_submit():
    raw_station = request.form.get("station_id", "")
    case_count_raw = request.form.get("case_count", "")
    onset_date_raw = (request.form.get("onset_date", "") or "").strip()
    notes = (request.form.get("notes", "") or "").strip()
    symptoms_selected = request.form.getlist("symptoms")
    risk_tier_raw = (request.form.get("risk_tier", "") or "").strip().lower()

    def render(success=None, error=None):
        with connection() as conn:
            stations = conn.execute(
                text("SELECT station_id, name FROM stations ORDER BY station_id")
            ).mappings().all()
        return render_template(
            "medical_report.html",
            stations=stations,
            symptoms=SYMPTOMS,
            success_message=success,
            error_message=error,
        )

    try:
        station_id = int(raw_station)
    except (TypeError, ValueError):
        return render(error="Please select a valid station.")

    try:
        case_count = int(case_count_raw) if case_count_raw else 1
        if case_count < 1:
            raise ValueError
    except ValueError:
        return render(error="Case count must be a positive integer.")

    report_time = datetime.now(timezone.utc)
    if onset_date_raw:
        try:
            onset_dt = datetime.fromisoformat(onset_date_raw).replace(
                tzinfo=timezone.utc
            )
            report_time = onset_dt + timedelta(days=1) - timedelta(seconds=1)
        except ValueError:
            return render(error="Onset date must be YYYY-MM-DD.")

    if risk_tier_raw not in ("", "low", "medium", "high", "severe"):
        return render(error="Invalid risk tier value.")
    risk_tier_value = risk_tier_raw or None

    valid_keys = {key for key, _label in SYMPTOMS}
    symptoms_selected = [s for s in symptoms_selected if s in valid_keys]

    raw_message = (
        f"medical_portal | cases={case_count} | "
        f"symptoms={','.join(symptoms_selected) or 'none'} | "
        f"onset={onset_date_raw or 'n/a'} | notes={notes[:200]}"
    )

    with connection() as conn:
        with conn.begin():
            station = conn.execute(
                text("SELECT name FROM stations WHERE station_id = :sid"),
                {"sid": station_id},
            ).mappings().first()
            if station is None:
                return render(error=f"Station {station_id} is not in the system.")

            report_id = conn.execute(
                text(
                    "INSERT INTO illness_reports "
                    "(station_id, reporter_phone, raw_message, parser_version, "
                    " report_source, submitter, case_count, onset_date, symptoms, "
                    " risk_tier) "
                    "VALUES (:sid, NULL, :msg, :ver, 'medical_portal', :sub, "
                    " :cc, :od, :sym, :rt) "
                    "RETURNING report_id"
                ),
                {
                    "sid": station_id,
                    "msg": raw_message,
                    "ver": STATION_PARSER_VERSION,
                    "sub": session.get("username"),
                    "cc": case_count,
                    "od": onset_date_raw or None,
                    "sym": json.dumps(symptoms_selected),
                    "rt": risk_tier_value,
                },
            ).scalar_one()

            labelled = label_readings_for_report(
                conn,
                report_id=report_id,
                station_id=station_id,
                report_time=report_time,
            )

    success = (
        f"Report received for {station['name']} (station {station_id}). "
        f"{labelled} reading(s) in the trailing-window were flagged. "
        f"Anchor: {onset_date_raw or 'now'}."
    )
    return render(success=success)
```

- [ ] **Step 4: Port `medical_history` and `medical_report_detail`**

Replace those two view functions:

```python
@app.get("/medical/history")
@role_required("medical")
def medical_history():
    with connection() as conn:
        report_rows = conn.execute(
            text("""
                SELECT ir.*, s.name AS station_name
                FROM illness_reports ir
                LEFT JOIN stations s ON s.station_id = ir.station_id
                WHERE ir.report_source = 'medical_portal'
                ORDER BY ir.received_at DESC
                LIMIT 50
            """),
        ).mappings().all()
        stations = conn.execute(
            text("""
                SELECT s.station_id, s.name, s.latitude, s.longitude,
                       (SELECT COUNT(*) FROM illness_reports
                          WHERE station_id = s.station_id
                            AND report_source = 'medical_portal') AS report_count,
                       (SELECT MAX(received_at) FROM illness_reports
                          WHERE station_id = s.station_id
                            AND report_source = 'medical_portal') AS last_report
                FROM stations s
                ORDER BY s.station_id
            """),
        ).mappings().all()

    reports_view = []
    for rep in report_rows:
        tier_block = _resolve_tier(dict(rep))
        try:
            symptoms_list = json.loads(rep["symptoms"] or "[]")
        except (json.JSONDecodeError, TypeError):
            symptoms_list = []
        reports_view.append({
            **dict(rep),
            **tier_block,
            "symptoms_display": ", ".join(symptoms_list) if symptoms_list else "—",
        })

    stations_json = json.dumps([dict(s) for s in stations])
    return render_template(
        "medical_history.html",
        reports=reports_view,
        stations_json=stations_json,
    )


@app.get("/medical/reports/<int:report_id>")
@role_required("medical")
def medical_report_detail(report_id: int):
    with connection() as conn:
        row = conn.execute(
            text("""
                SELECT ir.*, s.name AS station_name
                FROM illness_reports ir
                LEFT JOIN stations s ON s.station_id = ir.station_id
                WHERE ir.report_id = :rid
            """),
            {"rid": report_id},
        ).mappings().first()
        if row is None:
            abort(404)
    tier_block = _resolve_tier(dict(row))
    try:
        symptoms_list = json.loads(row["symptoms"] or "[]")
    except (json.JSONDecodeError, TypeError):
        symptoms_list = []
    symptoms_display = ", ".join(symptoms_list) if symptoms_list else "—"
    return render_template(
        "medical_report_detail.html",
        report=row,
        symptoms_display=symptoms_display,
        **tier_block,
    )
```

- [ ] **Step 5: Run tests**

Run: `cd App/backend && pytest tests/test_medical_form.py tests/test_medical_history.py tests/test_medical_detail_page.py -v`
Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add App/backend/app.py
git commit -m "Postgres: port /medical routes to SQLAlchemy text()"
```

---

## Task 8: Port `app.py` — SMS webhook

**Files:**
- Modify: `App/backend/app.py` (the `_find_open_conversation`, `_mark_abandoned`, and `sms_webhook` functions)

- [ ] **Step 1: Run SMS tests, see them fail**

Run: `cd App/backend && pytest tests/test_sms_dialog.py tests/test_sms_parsers.py -v`
Expected: FAIL on the route-level tests (parser-level tests should still pass).

- [ ] **Step 2: Port the SMS helpers and webhook**

Replace these three functions:

```python
def _find_open_conversation(conn, phone: str):
    if not phone:
        return None
    cutoff_dt = datetime.now(timezone.utc) - timedelta(minutes=SMS_WINDOW_MINUTES)
    cutoff = cutoff_dt.strftime("%Y-%m-%d %H:%M:%S")
    return conn.execute(
        text("""
            SELECT * FROM illness_reports
            WHERE reporter_phone = :phone
              AND received_at >= :cutoff
              AND dialog_state IN
                  ('awaiting_case_count','awaiting_symptoms','awaiting_onset')
            ORDER BY report_id DESC LIMIT 1
        """),
        {"phone": phone, "cutoff": cutoff},
    ).mappings().first()


def _mark_abandoned(conn, report_id):
    conn.execute(
        text(
            "UPDATE illness_reports SET dialog_state = 'abandoned' "
            "WHERE report_id = :rid"
        ),
        {"rid": report_id},
    )


@app.post("/sms")
def sms_webhook():
    if not _verify_twilio_signature(request):
        return ("forbidden", 403)

    from sms_dialog import parse_case_count, parse_symptoms, parse_onset

    raw_message = request.form.get("Body", "") or ""
    reporter_phone = request.form.get("From", "") or ""
    now = datetime.now(timezone.utc)
    reply = MessagingResponse()

    is_stop = re.search(r"\bstop\b", raw_message, re.IGNORECASE) is not None
    station_id = _parse_station_id(raw_message)
    explicit_station_id = _parse_explicit_station_id(raw_message)

    with connection() as conn:
        with conn.begin():
            open_conv = _find_open_conversation(conn, reporter_phone)

            if is_stop:
                if open_conv is None:
                    reply.message("No active conversation to opt out of. Thank you.")
                    return str(reply)
                _mark_abandoned(conn, open_conv["report_id"])
                reply.message("Opted out. We will no longer reply. Thank you.")
                return str(reply)

            if (explicit_station_id is not None
                    and open_conv is not None
                    and explicit_station_id != open_conv["station_id"]):
                _mark_abandoned(conn, open_conv["report_id"])
                open_conv = None
                station_id = explicit_station_id

            if open_conv is None:
                if station_id is None:
                    conn.execute(
                        text(
                            "INSERT INTO illness_reports "
                            "(station_id, reporter_phone, raw_message, parser_version, "
                            " report_source, dialog_state) "
                            "VALUES (NULL, :phone, :msg, :ver, 'sms', NULL)"
                        ),
                        {
                            "phone": reporter_phone,
                            "msg": raw_message,
                            "ver": STATION_PARSER_VERSION,
                        },
                    )
                    reply.message(
                        "We received your message but could not identify a station "
                        "number. Reply with the station number (e.g. '4'). Thank you."
                    )
                    return str(reply)

                station = conn.execute(
                    text("SELECT station_id, name FROM stations WHERE station_id = :sid"),
                    {"sid": station_id},
                ).mappings().first()
                if station is None:
                    conn.execute(
                        text(
                            "INSERT INTO illness_reports "
                            "(station_id, reporter_phone, raw_message, parser_version, "
                            " report_source, dialog_state) "
                            "VALUES (NULL, :phone, :msg, :ver, 'sms', NULL)"
                        ),
                        {
                            "phone": reporter_phone,
                            "msg": raw_message,
                            "ver": STATION_PARSER_VERSION,
                        },
                    )
                    reply.message(
                        f"Station {station_id} is not in our system. Please check "
                        "the number and try again. Thank you."
                    )
                    return str(reply)

                report_id = conn.execute(
                    text(
                        "INSERT INTO illness_reports "
                        "(station_id, reporter_phone, raw_message, parser_version, "
                        " report_source, dialog_state) "
                        "VALUES (:sid, :phone, :msg, :ver, 'sms', 'awaiting_case_count') "
                        "RETURNING report_id"
                    ),
                    {
                        "sid": station_id,
                        "phone": reporter_phone,
                        "msg": raw_message,
                        "ver": STATION_PARSER_VERSION,
                    },
                ).scalar_one()
                labelled = label_readings_for_report(
                    conn, report_id=report_id, station_id=station_id, report_time=now,
                )
                reply.message(
                    f"Report received for {station['name']} (station {station_id}). "
                    f"{labelled} reading(s) flagged. How many people are sick? "
                    "Reply with a number."
                )
                return str(reply)

            report_id = open_conv["report_id"]
            state = open_conv["dialog_state"]

            if state == "awaiting_case_count":
                n = parse_case_count(raw_message)
                if n is None:
                    reply.message(
                        "I didn't understand. How many people are sick? Reply with a number."
                    )
                    return str(reply)
                conn.execute(
                    text(
                        "UPDATE illness_reports "
                        "SET case_count = :n, dialog_state = 'awaiting_symptoms' "
                        "WHERE report_id = :rid"
                    ),
                    {"n": n, "rid": report_id},
                )
                reply.message(
                    f"Noted, {n} cases. Which symptoms? Reply with numbers, e.g. '1,3'. "
                    "1=diarrhoea 2=vomiting 3=fever 4=dehydration."
                )
                return str(reply)

            if state == "awaiting_symptoms":
                syms = parse_symptoms(raw_message)
                if syms is None:
                    reply.message(
                        "I didn't understand. Reply with numbers, e.g. '1,3'. "
                        "1=diarrhoea 2=vomiting 3=fever 4=dehydration."
                    )
                    return str(reply)
                conn.execute(
                    text(
                        "UPDATE illness_reports "
                        "SET symptoms = :s, dialog_state = 'awaiting_onset' "
                        "WHERE report_id = :rid"
                    ),
                    {"s": json.dumps(syms), "rid": report_id},
                )
                reply.message(
                    f"Noted: {', '.join(syms)}. When did symptoms start? "
                    "Reply 'today', 'yesterday', or DD/MM."
                )
                return str(reply)

            if state == "awaiting_onset":
                onset = parse_onset(raw_message)
                if onset is None:
                    reply.message(
                        "I didn't understand. Reply 'today', 'yesterday', or DD/MM."
                    )
                    return str(reply)
                conn.execute(
                    text(
                        "UPDATE illness_reports "
                        "SET onset_date = :od, dialog_state = 'complete' "
                        "WHERE report_id = :rid"
                    ),
                    {"od": onset.isoformat(), "rid": report_id},
                )
                reply.message("Report complete. Stay safe. Reply STOP to opt out.")
                return str(reply)

            reply.message(
                "Unexpected state. Reply STOP to opt out, or text a station number to start over."
            )
            return str(reply)
```

- [ ] **Step 3: Run SMS tests**

Run: `cd App/backend && pytest tests/test_sms_dialog.py tests/test_sms_parsers.py -v`
Expected: pass.

- [ ] **Step 4: Commit**

```bash
git add App/backend/app.py
git commit -m "Postgres: port /sms webhook + helpers to SQLAlchemy text()"
```

---

## Task 9: Port `app.py` — actions + dashboard report detail

**Files:**
- Modify: `App/backend/app.py` (`post_action` POST and `dashboard_report_detail` GET)

- [ ] **Step 1: Run action / detail tests, see them fail**

Run: `cd App/backend && pytest tests/test_actions.py tests/test_detail_actions.py tests/test_gov_detail_page.py -v`
Expected: FAIL.

- [ ] **Step 2: Port `post_action`**

```python
@app.post("/actions")
@role_required("government")
def post_action():
    action_type = (request.form.get("action_type", "") or "").strip()
    station_raw = (request.form.get("station_id", "") or "").strip()
    related_raw = (request.form.get("related_report_id", "") or "").strip()
    notes = (request.form.get("notes", "") or "").strip()[:500] or None

    if action_type not in ACTION_TYPES:
        return ("invalid action_type", 400)

    try:
        station_id = int(station_raw)
    except (TypeError, ValueError):
        return ("invalid station_id", 400)

    related_id = None
    if related_raw:
        try:
            related_id = int(related_raw)
        except (TypeError, ValueError):
            return ("invalid related_report_id", 400)

    with connection() as conn:
        with conn.begin():
            station = conn.execute(
                text("SELECT is_closed FROM stations WHERE station_id = :sid"),
                {"sid": station_id},
            ).mappings().first()
            if station is None:
                return (f"unknown station_id {station_id}", 400)

            if action_type == "close_borehole" and station["is_closed"]:
                return (f"station {station_id} is already closed", 400)
            if action_type == "reopen_borehole" and not station["is_closed"]:
                return (f"station {station_id} is already open", 400)

            conn.execute(
                text(
                    "INSERT INTO interventions "
                    "(station_id, action_type, triggered_by, related_report_id, notes) "
                    "VALUES (:sid, :at, :tb, :rid, :notes)"
                ),
                {
                    "sid": station_id,
                    "at": action_type,
                    "tb": session["username"],
                    "rid": related_id,
                    "notes": notes,
                },
            )
            if action_type == "close_borehole":
                conn.execute(
                    text("UPDATE stations SET is_closed = 1 WHERE station_id = :sid"),
                    {"sid": station_id},
                )
            elif action_type == "reopen_borehole":
                conn.execute(
                    text("UPDATE stations SET is_closed = 0 WHERE station_id = :sid"),
                    {"sid": station_id},
                )

    referrer = request.referrer or ""
    if referrer.startswith("/") or referrer.startswith(request.host_url):
        return redirect(referrer)
    return redirect(url_for("dashboard"))
```

- [ ] **Step 3: Port `dashboard_report_detail`**

```python
@app.get("/dashboard/reports/<int:report_id>")
def dashboard_report_detail(report_id: int):
    if "username" not in session:
        return redirect(url_for("login", next=request.path))
    if session.get("role") != "government":
        return (
            "This page is for government officials. "
            f"Medical staff can view this report at /medical/reports/{report_id}",
            403,
        )

    with connection() as conn:
        row = conn.execute(
            text("""
                SELECT ir.*, s.name AS station_name
                FROM illness_reports ir
                LEFT JOIN stations s ON s.station_id = ir.station_id
                WHERE ir.report_id = :rid
            """),
            {"rid": report_id},
        ).mappings().first()
        if row is None:
            abort(404)
        labelled_readings = conn.execute(
            text("""
                SELECT rl.reading_id, rl.rule_description,
                       sr.recorded_at, sr.ph, sr.turbidity_ntu, sr.temperature_c
                FROM reading_labels rl
                JOIN sensor_readings sr ON sr.reading_id = rl.reading_id
                WHERE rl.report_id = :rid
                ORDER BY sr.recorded_at DESC
            """),
            {"rid": report_id},
        ).mappings().all()
        interventions_rows = conn.execute(
            text("""
                SELECT intervention_id, action_type, triggered_by, triggered_at, notes
                FROM interventions
                WHERE related_report_id = :rid
                ORDER BY triggered_at ASC
            """),
            {"rid": report_id},
        ).mappings().all()

    tier_block = _resolve_tier(dict(row))
    try:
        symptoms_list = json.loads(row["symptoms"] or "[]")
    except (json.JSONDecodeError, TypeError):
        symptoms_list = []
    symptoms_display = ", ".join(symptoms_list) if symptoms_list else "—"

    return render_template(
        "dashboard_report_detail.html",
        report=row,
        symptoms_display=symptoms_display,
        labelled_readings=labelled_readings,
        interventions=interventions_rows,
        **tier_block,
    )
```

(Variable renamed from `interventions` to `interventions_rows` to avoid shadowing the `Table` import in `database.py` if we ever import it — defensive but harmless.)

- [ ] **Step 4: Run all app.py tests**

Run: `cd App/backend && pytest tests/test_actions.py tests/test_detail_actions.py tests/test_gov_detail_page.py -v`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add App/backend/app.py
git commit -m "Postgres: port /actions + /dashboard/reports/<id> to SQLAlchemy text()"
```

---

## Task 10: Port `tests/test_migrations.py`

**Files:**
- Modify: `App/backend/tests/test_migrations.py`

- [ ] **Step 1: Read the existing test to see what it asserts**

Run: `cat App/backend/tests/test_migrations.py`

Expected: it uses `PRAGMA table_info(...)` and catches `sqlite3.IntegrityError` from CHECK violations. Both are SQLite-specific.

- [ ] **Step 2: Rewrite the test**

Replace `App/backend/tests/test_migrations.py` with the SQLAlchemy-portable version. The asserts (which columns exist; CHECK constraints reject invalid values) stay the same — only the introspection mechanism changes:

```python
"""Migration / schema invariants — portable between SQLite and Postgres."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError


def test_stations_has_is_closed_column(tmp_db_path):
    from database import init_db
    from engine import get_engine

    init_db()
    cols = {c["name"] for c in inspect(get_engine()).get_columns("stations")}
    assert "is_closed" in cols


def test_interventions_table_exists_and_rejects_bad_action(tmp_db_path):
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
    from database import init_db
    from engine import get_engine

    init_db()
    cols = {c["name"] for c in inspect(get_engine()).get_columns("illness_reports")}
    for expected in ("risk_tier", "dialog_state", "case_count", "symptoms", "onset_date"):
        assert expected in cols


def test_risk_tier_rejects_invalid_value(tmp_db_path):
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
```

- [ ] **Step 3: Run the test**

Run: `cd App/backend && pytest tests/test_migrations.py -v`
Expected: 5 passed.

- [ ] **Step 4: Commit**

```bash
git add App/backend/tests/test_migrations.py
git commit -m "Postgres: port test_migrations to SQLAlchemy inspect + IntegrityError"
```

---

## Task 11: Run the full suite, fix any straggler

**Files:**
- Whatever the next failure points at.

- [ ] **Step 1: Run the whole test suite**

Run: `cd App/backend && pytest -v`
Expected: all tests pass. If anything still fails, that's the next port to do — by this point it should be small, e.g. a stray `conn.execute("...", tuple)` in a less-trafficked route, or a `cursor.lastrowid` we missed.

- [ ] **Step 2: Fix the failure**

Apply the same `text() + dict params + RETURNING` pattern used in the previous tasks. Resist the temptation to refactor anything else.

- [ ] **Step 3: Re-run, commit**

```bash
cd App/backend && pytest -v
git add -p App/backend/  # stage only the porting fix
git commit -m "Postgres: port remaining straggler queries surfaced by full test run"
```

(If the full run was already green, skip the commit.)

---

## Task 12: Add release-phase init_db to Procfile

**Files:**
- Modify: `App/backend/Procfile`

**Why:** On Railway, the web container starts, init_db() runs on first request — but if init_db() raises (e.g. Postgres extension missing, permissions wrong, schema CHECK conflict), the request fails. Running init_db() in a release phase makes the deploy fail loudly rather than silently 500ing on first traffic.

- [ ] **Step 1: Update Procfile**

Replace the contents of `App/backend/Procfile` with:

```
release: python -c "from database import init_db; init_db(); print('schema OK')"
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

**Note:** Railway runs the `release` command on every deploy before promoting the new container. If it exits non-zero, the deploy is aborted — so a bad schema change can't take down production.

- [ ] **Step 2: Verify the release command works locally**

Run: `cd App/backend && python -c "from database import init_db; init_db(); print('schema OK')"`
Expected: prints `schema OK`. (Against your local SQLite at `data/water_safety.db`.)

- [ ] **Step 3: Commit**

```bash
git add App/backend/Procfile
git commit -m "Postgres: add release-phase init_db so Railway deploys fail loudly on schema errors"
```

---

## Task 13: Provision Railway Postgres and deploy

**Files:** None (Railway dashboard work + git push).

**This is a manual step the user runs in the Railway dashboard, not something Claude or an agent can do.**

- [ ] **Step 1: Add Postgres to the Railway project**

In the Railway dashboard for the existing GM2 project:
1. Click `+ New` → `Database` → `PostgreSQL`.
2. Wait for the service to provision (≈30 seconds).

- [ ] **Step 2: Wire DATABASE_URL into the web service**

1. Open the **web** (Flask) service's `Variables` tab.
2. Add a new variable `DATABASE_URL` with value `${{ Postgres.DATABASE_URL }}` (Railway templating — this auto-resolves to the internal Postgres URL).
3. Save. Railway will redeploy.

- [ ] **Step 3: Watch the deploy logs for the release phase**

Expected lines in the build/deploy log:
- `Running release phase`
- `schema OK`
- `Starting web phase`
- `Listening at: http://0.0.0.0:$PORT` (or similar gunicorn line)

If `schema OK` does not appear, the deploy is broken — read the error, fix locally, push again. Do not skip this.

- [ ] **Step 4: Smoke-test the live URL**

After deploy succeeds:
```bash
curl -s https://gm2aquasolutions-production-aff9.up.railway.app/health
```
Expected: `{"status": "ok", "timestamp": "..."}`.

Sign in as the government user; the dashboard should show 10 stations (re-seeded by `init_db()`) with "no readings yet" and "no illness reports yet". That's correct — Postgres is empty.

- [ ] **Step 5: Push a few readings + send a test SMS**

```bash
# From your laptop:
python App/scripts/simulate_sensor.py --secret <DEVICE_SECRET> --interval 5 --stations 1,2,3
```
(Let it run 30 seconds, then ctrl-C.)

Send one SMS to the Twilio number, e.g. "4".

Refresh the dashboard. Both should now show data.

- [ ] **Step 6: Force a redeploy and confirm data persists**

In Railway, manually trigger a redeploy of the web service. After it comes back up, refresh the dashboard — readings and the SMS report should **still be there**. That's the durability invariant we're paying Postgres for.

If they're gone: `DATABASE_URL` is not being read, or it's still pointing at the ephemeral filesystem. Stop and debug before declaring this done.

---

## Task 14: Update CLAUDE.md and issues_v3.md

**Files:**
- Modify: `CLAUDE.md`
- Modify: `issues_v3.md`

- [ ] **Step 1: Note the new persistence layer in CLAUDE.md**

In `CLAUDE.md`, find the "Application-layer guardrails" section and add a bullet:

```
- The Railway deploy uses Postgres (provisioned as a Railway service). Local
  dev and the pytest suite use SQLite via the engine module's DATABASE_URL
  fallback. All DB code goes through SQLAlchemy Core text() with named
  parameters so the same SQL runs on both backends. Do not reintroduce raw
  sqlite3 calls in request-path code; feature_engineering.py is the only
  remaining sqlite3-only consumer and is offline-only.
```

- [ ] **Step 2: Close the ephemeral-filesystem risk in issues_v3.md**

In `issues_v3.md`, find the risk register entry covering Railway persistence (or add one if missing) and mark it resolved with the migration commit hash:

```
- Ephemeral Railway filesystem wiping the demo DB on every redeploy.
  RESOLVED 2026-05-28 by migrating to Railway Postgres. See plan
  docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md.
```

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md issues_v3.md
git commit -m "Postgres: document the migration in CLAUDE.md and close the ephemeral-DB risk"
```

---

## Self-review checklist (done before handing off to execution)

- [x] **Spec coverage.** Every requirement from "Migrate to Railway Postgres" is mapped to a task:
  - Engine + URL switching → Task 1
  - Portable schema → Task 2
  - Test fixture → Task 3
  - Every DB-touching app file → Tasks 4–9
  - Tests updated → Tasks 3, 10
  - Railway provisioning → Task 13
  - Documentation → Task 14
- [x] **No placeholders.** Every step has actual code or an actual command. No "TBD", no "implement appropriate error handling".
- [x] **Type consistency.** All ported routes return `RowMapping` via `.mappings().first()` / `.mappings().all()`, so template access like `row["station_id"]` keeps working. `RETURNING ... .scalar_one()` is the consistent lastrowid replacement.
- [x] **Scope-out documented.** `feature_engineering.py` and Alembic migrations explicitly excluded.

---

## Risks worth flagging before execution

1. **SQLite `RETURNING` requires 3.35+.** Most Python builds ship newer SQLite, but verify: `python -c "import sqlite3; print(sqlite3.sqlite_version)"` — must be ≥ 3.35.
2. **`INSERT OR IGNORE` → `ON CONFLICT DO NOTHING` requires SQLite 3.24+.** Same check passes the same Python.
3. **`stations.station_id` is not autoincrement** — the schema treats it as a manual primary key seeded with explicit integers 1–10. SQLAlchemy column has `autoincrement=False` for that reason. If anyone later inserts a station without specifying `station_id`, Postgres will raise NOT NULL violation rather than auto-generating an ID. That's a feature, not a bug — keep it.
4. **Timestamp storage stays as ISO strings, not native TIMESTAMP types.** Cleaner Postgres-native design would use TIMESTAMPTZ columns, but that would break the string-comparison logic in `_find_open_conversation` and template slices like `received_at[:19]`. Out of scope for this migration; flag as a future cleanup.
5. **`feature_engineering.py` opens its own SQLite connection** with raw `sqlite3.connect()`. Post-migration it can no longer be pointed at the production DB directly. If you want to run training over Railway data, dump Postgres to a local SQLite file first (or port feature_engineering.py in a separate plan). Note this in its module docstring as part of Task 11 or 14 if not already.

---
