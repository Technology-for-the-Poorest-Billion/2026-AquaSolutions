"""SQLite schema and connection helpers for the Gen-1 water-safety backend."""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

BACKEND_DIR = Path(__file__).resolve().parent


def _resolve_db_path() -> Path:
    raw = os.environ.get("DATABASE_PATH", "data/water_safety.db")
    p = Path(raw)
    if not p.is_absolute():
        p = BACKEND_DIR / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


SCHEMA = """
CREATE TABLE IF NOT EXISTS stations (
    station_id     INTEGER PRIMARY KEY,
    name           TEXT NOT NULL,
    latitude       REAL,
    longitude      REAL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sensor_readings (
    reading_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id        INTEGER NOT NULL REFERENCES stations(station_id),
    recorded_at       TEXT    NOT NULL,
    ph                REAL,
    turbidity_ntu     REAL,
    temperature_c     REAL,
    rainfall_mm       REAL,
    provenance        TEXT    NOT NULL DEFAULT 'unknown',
    received_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_readings_station_time
    ON sensor_readings(station_id, recorded_at);

CREATE TABLE IF NOT EXISTS illness_reports (
    report_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id        INTEGER REFERENCES stations(station_id),
    reporter_phone    TEXT,
    raw_message       TEXT    NOT NULL,
    parser_version    TEXT    NOT NULL,
    received_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    report_source     TEXT    NOT NULL DEFAULT 'sms'
        CHECK (report_source IN ('sms', 'medical_portal')),
    submitter         TEXT,
    case_count        INTEGER,
    onset_date        TEXT,
    symptoms          TEXT
);

CREATE INDEX IF NOT EXISTS idx_reports_station_time
    ON illness_reports(station_id, received_at);

CREATE TABLE IF NOT EXISTS reading_labels (
    label_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    reading_id        INTEGER NOT NULL REFERENCES sensor_readings(reading_id),
    report_id         INTEGER NOT NULL REFERENCES illness_reports(report_id),
    label             TEXT    NOT NULL CHECK (label IN ('unsafe', 'suspect')),
    rule_description  TEXT    NOT NULL,
    labelled_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE(reading_id, report_id)
);

CREATE INDEX IF NOT EXISTS idx_labels_reading
    ON reading_labels(reading_id);
"""


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


def get_connection() -> sqlite3.Connection:
    """Open a new SQLite connection with sensible defaults."""
    conn = sqlite3.connect(_resolve_db_path(), isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def connection() -> Iterator[sqlite3.Connection]:
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the original schema, idempotently.

    SQLite's CREATE TABLE IF NOT EXISTS skips existing tables, so new
    columns must be added via ALTER. We guard each with PRAGMA so the
    function is safe to run repeatedly on any DB state.
    """
    existing = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(illness_reports)").fetchall()
    }

    added_columns = [
        ("report_source", "TEXT NOT NULL DEFAULT 'sms'"),
        ("submitter",     "TEXT"),
        ("case_count",    "INTEGER"),
        ("onset_date",    "TEXT"),
        ("symptoms",      "TEXT"),
    ]

    for col_name, col_type in added_columns:
        if col_name not in existing:
            conn.execute(
                f"ALTER TABLE illness_reports ADD COLUMN {col_name} {col_type}"
            )


def init_db() -> None:
    """Create tables, run migrations, and (idempotently) seed stations.

    INSERT OR IGNORE so existing rows are preserved when new stations
    are added to SEED_STATIONS between runs.
    """
    with connection() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.executemany(
            "INSERT OR IGNORE INTO stations "
            "(station_id, name, latitude, longitude) "
            "VALUES (?, ?, ?, ?)",
            SEED_STATIONS,
        )


if __name__ == "__main__":
    init_db()
    print(f"Initialised database at {_resolve_db_path()}")
