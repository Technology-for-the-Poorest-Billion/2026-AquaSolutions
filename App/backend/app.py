"""Flask app for the Gen-1 water-safety pipeline.

Routes
------
GET  /health      — liveness probe
POST /sms         — Twilio webhook for inbound illness reports
GET  /dashboard   — recent readings + recent reports (debug view)
POST /ingest      — sensor reading ingest (via sensor_ingest blueprint)
"""

from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from flask import Flask, render_template, request
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from database import connection, init_db
from labels import label_readings_for_report
from sensor_ingest import sensor_bp

load_dotenv()

app = Flask(__name__)
app.register_blueprint(sensor_bp)
init_db()


STATION_PARSER_VERSION = "lenient_first_int_v1"
STATION_RE = re.compile(r"\b(\d{1,4})\b")


def _parse_station_id(message: str) -> int | None:
    """Lenient parser: first 1–4 digit integer in the message.

    See ``issues_v3.md`` §C5 for the strictness trade-off. Rejected
    messages are still stored in ``illness_reports`` so a human can
    review them later.
    """
    match = STATION_RE.search(message or "")
    if match is None:
        return None
    return int(match.group(1))


def _verify_twilio_signature(req) -> bool:
    if os.environ.get("TWILIO_VALIDATE_SIGNATURES", "false").lower() != "true":
        return True

    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not auth_token:
        return False

    public_base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    if not public_base:
        return False

    url = f"{public_base}{req.path}"
    signature = req.headers.get("X-Twilio-Signature", "")
    validator = RequestValidator(auth_token)
    return validator.validate(url, req.form, signature)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/sms")
def sms_webhook():
    if not _verify_twilio_signature(request):
        return ("forbidden", 403)

    raw_message = request.form.get("Body", "") or ""
    reporter_phone = request.form.get("From", "") or ""
    station_id = _parse_station_id(raw_message)
    now = datetime.now(timezone.utc)

    reply = MessagingResponse()

    with connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO illness_reports
                (station_id, reporter_phone, raw_message, parser_version)
            VALUES (?, ?, ?, ?)
            """,
            (station_id, reporter_phone, raw_message, STATION_PARSER_VERSION),
        )
        report_id = cursor.lastrowid

        if station_id is None:
            reply.message(
                "We received your message but could not identify a station "
                "number. Please reply with the station number "
                "(e.g. '4'). Thank you."
            )
            return str(reply)

        station = conn.execute(
            "SELECT name FROM stations WHERE station_id = ?", (station_id,)
        ).fetchone()
        if station is None:
            reply.message(
                f"Station {station_id} is not in our system. Please check "
                "the number and try again. Thank you."
            )
            return str(reply)

        labelled = label_readings_for_report(
            conn, report_id=report_id, station_id=station_id, report_time=now
        )

    reply.message(
        f"Report received for {station['name']} (station {station_id}). "
        f"Thank you. {labelled} recent reading(s) flagged for review. "
        "Reply STOP to opt out."
    )
    return str(reply)


@app.get("/dashboard")
def dashboard():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

    with connection() as conn:
        readings = conn.execute(
            """
            SELECT r.reading_id, r.station_id, s.name AS station_name,
                   r.recorded_at, r.ph, r.turbidity_ntu, r.temperature_c,
                   r.rainfall_mm,
                   (SELECT label FROM reading_labels
                     WHERE reading_id = r.reading_id LIMIT 1) AS label
            FROM sensor_readings r
            JOIN stations s USING (station_id)
            WHERE r.received_at >= ?
            ORDER BY r.recorded_at DESC
            LIMIT 50
            """,
            (cutoff,),
        ).fetchall()

        reports = conn.execute(
            """
            SELECT ir.report_id, ir.station_id, s.name AS station_name,
                   ir.reporter_phone, ir.raw_message, ir.received_at,
                   (SELECT COUNT(*) FROM reading_labels
                     WHERE report_id = ir.report_id) AS readings_labelled
            FROM illness_reports ir
            LEFT JOIN stations s USING (station_id)
            ORDER BY ir.received_at DESC
            LIMIT 50
            """
        ).fetchall()

    return render_template(
        "dashboard.html",
        readings=readings,
        reports=reports,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
