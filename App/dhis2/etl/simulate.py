"""Synthetic borehole water-quality readings. SYNTHETIC DATA ONLY — there is no
real sensor feed yet; this exercises the labelling pipeline, not real measurements.

Deterministic given (stations, date range, per_day, seed). Timestamps are spread
through each day so multiple readings per day are distinct.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta


def _daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def simulate_readings(station_ids, start: date, end: date, per_day: int = 1, seed: int = 0):
    rng = random.Random(seed)
    readings = []
    for station_id in station_ids:
        for day in _daterange(start, end):
            for k in range(per_day):
                # spread readings across the working day
                hour = 8 + int(k * (10 / max(per_day, 1)))
                ts = datetime(day.year, day.month, day.day, hour, 0, 0)
                readings.append({
                    "id": f"R-{station_id}-{day.isoformat()}-{k}",
                    "station_id": station_id,
                    "timestamp": ts,
                    "turbidity_ntu": round(rng.uniform(0.5, 12.0), 2),
                    "ph": round(rng.uniform(6.0, 8.5), 2),
                    "temperature_c": round(rng.uniform(18.0, 30.0), 1),
                    "rainfall_mm": round(rng.uniform(0.0, 25.0), 1),
                    "chlorine_mg_l": round(rng.uniform(0.0, 1.5), 2),
                })
    return readings
