"""Schema definition + init for the Gen-1 water-safety backend.

Schema is declared as SQLAlchemy MetaData/Table objects so the same code
emits SQLite DDL locally and Postgres DDL on Railway. init_db() is
idempotent: it creates any missing tables, adds any newly-added columns
on existing tables, and seeds the 32 stations row by row with
ON CONFLICT DO UPDATE.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import (
    CheckConstraint, Column, Float, ForeignKey, Index, Integer, MetaData,
    Table, Text, UniqueConstraint, func, inspect, text,
)
from sqlalchemy.engine import Connection

from engine import get_engine


metadata = MetaData()


stations = Table(
    "stations", metadata,
    Column("station_id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, nullable=False),
    Column("latitude", Float),
    Column("longitude", Float),
    Column("is_closed", Integer, nullable=False, server_default=text("0")),
    Column("neighborhood_id", Integer, ForeignKey("neighborhoods.neighborhood_id")),
    Column("created_at", Text, nullable=False, server_default=func.current_timestamp()),
)


sensor_readings = Table(
    "sensor_readings", metadata,
    Column("reading_id", Integer, primary_key=True, autoincrement=True),
    Column("station_id", Integer, ForeignKey("stations.station_id"), nullable=False),
    Column("recorded_at", Text, nullable=False),
    Column("ph", Float),
    Column("turbidity_ntu", Float),
    Column("temperature_c", Float),
    Column("rainfall_mm", Float),
    # Additional water-quality indicators (added 2026-06-01). All nullable
    # so older readings remain valid.
    Column("chlorine_mg_l", Float),     # free chlorine residual, mg/L
    Column("orp_mv", Float),            # oxidation-reduction potential, mV
    Column("uv_absorbance", Float),     # UV absorbance at 254 nm (organic-matter proxy)
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


user_preferences = Table(
    "user_preferences", metadata,
    Column("username", Text, primary_key=True),
    Column("language", Text),
)


neighborhoods = Table(
    "neighborhoods", metadata,
    Column("neighborhood_id", Integer, primary_key=True, autoincrement=False),
    Column("name", Text, unique=True, nullable=False),
)


SEED_NEIGHBORHOODS = [
    (1, "Central Harare"),
    (2, "Northern Suburbs"),
    (3, "Southern Areas"),
    (4, "Eastern Suburbs"),
]


# 32 demo stations across 4 Harare neighborhoods (spec §4). All
# coordinates sit inside the dashboard's Leaflet zoom-12 view.
# Each tuple is (station_id, name, lat, lon, neighborhood_id).
SEED_STATIONS = [
    # Central Harare (neighborhood 1)
    (1,  "Avenues — central clinic",          -17.815, 31.050, 1),
    (2,  "Belvedere — community hall",        -17.840, 31.025, 1),
    (7,  "Milton Park — health post",         -17.832, 31.030, 1),
    (11, "Causeway — government complex",     -17.831, 31.048, 1),
    (12, "Kopje — civic hall",                -17.835, 31.038, 1),
    (13, "CBD — central market",              -17.828, 31.052, 1),
    (14, "Africa Unity Square — fountain",    -17.830, 31.054, 1),
    (15, "Workington — industrial water",     -17.840, 31.030, 1),

    # Northern Suburbs (neighborhood 2)
    (6,  "Newlands — shopping centre",        -17.810, 31.067, 2),
    (9,  "Mt Pleasant — north well",          -17.795, 31.045, 2),
    (16, "Avondale — north clinic",           -17.797, 31.038, 2),
    (17, "Belgravia — community well",        -17.800, 31.038, 2),
    (18, "Mt Pleasant Heights — school",      -17.785, 31.040, 2),
    (19, "Marlborough — clinic",              -17.795, 31.025, 2),
    (20, "Strathaven — water point",          -17.797, 31.045, 2),
    (21, "Pomona — north settlement",         -17.787, 31.060, 2),

    # Southern Areas (neighborhood 3)
    (4,  "Mbare — Musika market",             -17.860, 31.045, 3),
    (5,  "Hatfield — community borehole",     -17.852, 31.072, 3),
    (22, "Waterfalls — south clinic",         -17.870, 31.058, 3),
    (23, "Sunningdale — water point",         -17.875, 31.078, 3),
    (24, "Lichendale — primary school",       -17.875, 31.050, 3),
    (25, "Southerton — community well",       -17.865, 31.020, 3),
    (26, "Aspindale Park — water point",      -17.870, 31.025, 3),
    (27, "Prospect — health post",            -17.878, 31.015, 3),

    # Eastern Suburbs (neighborhood 4)
    (3,  "Eastlea — primary school",          -17.825, 31.062, 4),
    (8,  "Hillside — water point",            -17.847, 31.058, 4),
    (10, "Greendale — east settlement",       -17.835, 31.082, 4),
    (28, "Highlands — east clinic",           -17.820, 31.075, 4),
    (29, "Athlone — primary school",          -17.825, 31.085, 4),
    (30, "Cranborne — water point",           -17.850, 31.075, 4),
    (31, "Donnybrook — community hall",       -17.855, 31.085, 4),
    (32, "Msasa — industrial water point",    -17.830, 31.090, 4),
]


# Columns that may be missing from an existing illness_reports table on a
# pre-Phase-C deploy. CHECK constraints are inlined so an ALTER-TABLE
# upgrade path lands them on the column, matching the Table-level
# CheckConstraints that fire on a fresh CREATE TABLE.
_REPORT_BACKFILL_COLUMNS = [
    ("report_source", "TEXT NOT NULL DEFAULT 'sms'"),
    ("submitter",     "TEXT"),
    ("case_count",    "INTEGER"),
    ("onset_date",    "TEXT"),
    ("symptoms",      "TEXT"),
    ("risk_tier",     "TEXT CHECK (risk_tier IS NULL OR risk_tier IN "
                      "('low','medium','high','severe'))"),
    ("dialog_state",  "TEXT CHECK (dialog_state IS NULL OR dialog_state IN "
                      "('awaiting_case_count','awaiting_symptoms',"
                      "'awaiting_onset','complete','abandoned'))"),
]


@contextmanager
def connection() -> Iterator[Connection]:
    """Yield a SQLAlchemy 2.x Connection.

    Writes must be committed explicitly. SQLAlchemy 2.x auto-begins a
    transaction on the first statement and silently rolls it back when
    the Connection closes, so callers either need ``conn.commit()`` or,
    preferably, ``with conn.begin():`` around their write block.
    Read-only callers can ignore the transaction.
    """
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

    if "neighborhood_id" not in existing_station_cols:
        conn.execute(text(
            "ALTER TABLE stations ADD COLUMN neighborhood_id INTEGER "
            "REFERENCES neighborhoods(neighborhood_id)"
        ))

    # Sensor-readings backfill: the three water-quality indicators added
    # 2026-06-01 may be missing from a pre-existing table.
    existing_reading_cols = {c["name"] for c in insp.get_columns("sensor_readings")}
    for col_name in ("chlorine_mg_l", "orp_mv", "uv_absorbance"):
        if col_name not in existing_reading_cols:
            conn.execute(text(
                f"ALTER TABLE sensor_readings ADD COLUMN {col_name} REAL"
            ))

    # Postgres-only: stations.station_id was created with autoincrement=False,
    # so there is no sequence. New rows inserted via the dashboard's Add
    # Station POST need an auto-assigned id. Create the sequence if missing,
    # wire it as the column's DEFAULT, and advance it past the highest
    # currently-seeded id.
    if conn.engine.dialect.name == "postgresql":
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_sequences WHERE sequencename = 'stations_station_id_seq'
                ) THEN
                    CREATE SEQUENCE stations_station_id_seq;
                    ALTER TABLE stations
                        ALTER COLUMN station_id SET DEFAULT nextval('stations_station_id_seq');
                END IF;
                PERFORM setval(
                    'stations_station_id_seq',
                    GREATEST(
                        (SELECT COALESCE(MAX(station_id), 0) FROM stations),
                        32
                    )
                );
            END;
            $$;
        """))


def init_db() -> None:
    """Create all tables, run any needed column-level migrations, and seed stations.

    Safe to call repeatedly. Designed to run on every Flask startup. All
    DDL runs in one transaction so a Postgres failure mid-migration rolls
    back cleanly.
    """
    engine = get_engine()
    with engine.begin() as conn:
        metadata.create_all(conn)
        _migrate(conn)

        # Seed neighborhoods first — stations FK depends on them.
        for nid, name in SEED_NEIGHBORHOODS:
            conn.execute(
                text(
                    "INSERT INTO neighborhoods (neighborhood_id, name) "
                    "VALUES (:nid, :name) "
                    "ON CONFLICT (neighborhood_id) DO UPDATE SET "
                    "    name = excluded.name"
                ),
                {"nid": nid, "name": name},
            )

        # Seed stations, including the new neighborhood_id assignment.
        for sid, name, lat, lon, nid in SEED_STATIONS:
            conn.execute(
                text(
                    "INSERT INTO stations "
                    "(station_id, name, latitude, longitude, neighborhood_id) "
                    "VALUES (:sid, :name, :lat, :lon, :nid) "
                    "ON CONFLICT (station_id) DO UPDATE SET "
                    "    name = excluded.name, "
                    "    latitude = excluded.latitude, "
                    "    longitude = excluded.longitude, "
                    "    neighborhood_id = excluded.neighborhood_id"
                ),
                {"sid": sid, "name": name, "lat": lat, "lon": lon, "nid": nid},
            )



if __name__ == "__main__":
    init_db()
    print(f"Initialised database at {get_engine().url}")
