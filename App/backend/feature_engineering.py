"""
feature_engineering.py

Turns raw SQLite sensor readings into a labelled feature matrix
ready for XGBoost training.

One row per (station_id, 7-day window). Features are hourly sensor
readings across the window — ph_h0, ph_h1 ... ph_h167, turbidity_h0 ...
plus a matching set of _missing flags for imputed slots.

Total features: 7 days x 24 hours x 4 sensors x 2 (value + missing) = 1,344

Usage:
    from feature_engineering import build_training_windows
    df = build_training_windows("data/water_safety.db")
"""

import sqlite3
from contextlib import contextmanager

import numpy as np
import pandas as pd


SENSORS = ["ph", "turbidity_ntu", "temperature_c", "rainfall_mm"]
WINDOW_DAYS = 7
HOURS_PER_WINDOW = WINDOW_DAYS * 24  # 168


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_training_windows(
    db_path: str,
    window_days: int = WINDOW_DAYS,
    min_coverage: float = 0.5,
) -> pd.DataFrame:
    """
    Query the database and return a labelled feature matrix.

    Parameters
    ----------
    db_path : str
        Path to water_safety.db.
    window_days : int
        Length of each training window in days.
    min_coverage : float
        Minimum fraction of hourly slots that must have a real (non-imputed)
        reading. Windows below this are dropped.

    Returns
    -------
    pd.DataFrame
        Columns: station_id, window_start, window_end, data_coverage,
                 ph_h0 ... rainfall_mm_h167,
                 ph_h0_missing ... rainfall_mm_h167_missing,
                 label.
        label = 1 if any reading in the window was flagged unsafe/suspect.
        label = 0 otherwise.
    """
    with _connect(db_path) as conn:
        all_readings = _fetch_all_readings(conn)
        all_labels = _fetch_all_labels(conn)
        station_ids = _fetch_station_ids(conn)

    rows = []
    for station_id in station_ids:
        station_readings = all_readings[all_readings["station_id"] == station_id]
        if station_readings.empty:
            continue

        station_labels = all_labels[all_labels["station_id"] == station_id]

        # Slide a window from first to last reading date, 1-day step
        first_day = station_readings["recorded_at"].min().normalize()
        last_day = station_readings["recorded_at"].max().normalize()
        window_start = first_day

        while window_start + pd.Timedelta(days=window_days) <= last_day + pd.Timedelta(days=1):
            window_end = window_start + pd.Timedelta(days=window_days)

            window_readings = station_readings[
                (station_readings["recorded_at"] >= window_start)
                & (station_readings["recorded_at"] < window_end)
            ]

            if window_readings.empty:
                window_start += pd.Timedelta(days=1)
                continue

            features, coverage = _build_feature_vector(window_readings, window_start, window_end)

            if coverage < min_coverage:
                window_start += pd.Timedelta(days=1)
                continue

            features["station_id"] = station_id
            features["window_start"] = window_start
            features["window_end"] = window_end
            features["data_coverage"] = round(coverage, 3)
            features["label"] = _get_window_label(station_labels, window_start, window_end)

            rows.append(features)
            window_start += pd.Timedelta(days=1)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).reset_index(drop=True)
    meta = ["station_id", "window_start", "window_end", "data_coverage"]
    feature_cols = [c for c in df.columns if c not in meta + ["label"]]
    return df[meta + feature_cols + ["label"]]


def get_inference_features(
    db_path: str,
    station_id: int,
    as_of: pd.Timestamp | None = None,
    window_days: int = WINDOW_DAYS,
    min_coverage: float = 0.3,
) -> dict | None:
    """
    Build a feature vector for a single station using the most recent window.
    Called by Flask after each new reading is stored.

    Returns None if there is insufficient data (cold start or low coverage).
    The caller should respond with "insufficient data — send sample to lab."
    """
    if as_of is None:
        as_of = pd.Timestamp.utcnow().tz_localize(None)

    window_start = (as_of - pd.Timedelta(days=window_days)).normalize()
    window_end = as_of

    with _connect(db_path) as conn:
        df = pd.read_sql_query(
            """
            SELECT recorded_at, ph, turbidity_ntu, temperature_c, rainfall_mm
            FROM sensor_readings
            WHERE station_id = ? AND recorded_at >= ? AND recorded_at < ?
            ORDER BY recorded_at
            """,
            conn,
            params=(station_id, window_start.isoformat(), window_end.isoformat()),
        )

    if df.empty:
        return None

    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    features, coverage = _build_feature_vector(df, window_start, window_end)

    if coverage < min_coverage:
        return None

    features["data_coverage"] = round(coverage, 3)
    return features


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_feature_vector(
    readings: pd.DataFrame,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> tuple[dict, float]:
    """
    Resample readings to an hourly grid, impute gaps, and return a flat
    feature dict plus the coverage fraction.

    Feature names: ph_h0, ph_h1 ... ph_h167 (value at each hour slot)
                   ph_h0_missing, ph_h1_missing ... (1 if imputed, 0 if real)
    """
    indexed = readings.set_index("recorded_at").sort_index()

    # Build the 168-slot hourly grid
    n_hours = int((window_end - window_start).total_seconds() / 3600)
    grid = pd.date_range(start=window_start, periods=n_hours, freq="h")
    grid_df = pd.DataFrame(index=grid)

    for sensor in SENSORS:
        if sensor in indexed.columns:
            resampled = indexed[sensor].resample("h").mean()
            grid_df[sensor] = resampled.reindex(grid)
        else:
            grid_df[sensor] = np.nan

    # Coverage before imputation
    any_real = grid_df[SENSORS].notna().any(axis=1)
    coverage = float(any_real.mean())

    # Missingness flags
    missing_flags = {}
    for sensor in SENSORS:
        missing_flags[sensor] = grid_df[sensor].isna().astype(int)

    # Impute: forward-fill then median
    for sensor in SENSORS:
        grid_df[sensor] = grid_df[sensor].ffill()
        grid_df[sensor] = grid_df[sensor].fillna(grid_df[sensor].median())

    # Flatten to a dict: ph_h0, ph_h1, ..., ph_h0_missing, ...
    features = {}
    for sensor in SENSORS:
        for h, val in enumerate(grid_df[sensor]):
            features[f"{sensor}_h{h}"] = float(val) if not np.isnan(val) else 0.0
        for h, val in enumerate(missing_flags[sensor]):
            features[f"{sensor}_h{h}_missing"] = int(val)

    return features, coverage


def _get_window_label(
    station_labels: pd.DataFrame,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> int:
    if station_labels.empty:
        return 0
    mask = (
        (station_labels["recorded_at"] >= window_start)
        & (station_labels["recorded_at"] < window_end)
    )
    return int(mask.any())


def _fetch_all_readings(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT station_id, recorded_at, ph, turbidity_ntu, temperature_c, rainfall_mm
        FROM sensor_readings
        ORDER BY station_id, recorded_at
        """,
        conn,
    )
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df


def _fetch_all_labels(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql_query(
        """
        SELECT sr.station_id, sr.recorded_at, rl.label
        FROM reading_labels rl
        JOIN sensor_readings sr ON rl.reading_id = sr.reading_id
        """,
        conn,
    )
    df["recorded_at"] = pd.to_datetime(df["recorded_at"])
    return df


def _fetch_station_ids(conn: sqlite3.Connection) -> list[int]:
    rows = conn.execute("SELECT station_id FROM stations").fetchall()
    return [r[0] for r in rows]


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    try:
        yield conn
    finally:
        conn.close()
