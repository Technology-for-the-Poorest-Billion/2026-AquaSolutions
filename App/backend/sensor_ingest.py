"""Blueprint for POST /ingest — receives sensor readings from field nodes."""

from __future__ import annotations

import os
from datetime import datetime

from flask import Blueprint, jsonify, request

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
        station = conn.execute(
            "SELECT 1 FROM stations WHERE station_id = ?", (station_id,)
        ).fetchone()
        if station is None:
            return jsonify(error=f"unknown station_id: {station_id}"), 400

        cursor = conn.execute(
            """
            INSERT INTO sensor_readings
                (station_id, recorded_at, ph, turbidity_ntu,
                 temperature_c, rainfall_mm, provenance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                station_id,
                recorded_at.isoformat(),
                numeric_values["ph"],
                numeric_values["turbidity_ntu"],
                numeric_values["temperature_c"],
                numeric_values["rainfall_mm"],
                provenance,
            ),
        )

    return jsonify(status="ok", reading_id=cursor.lastrowid), 201
