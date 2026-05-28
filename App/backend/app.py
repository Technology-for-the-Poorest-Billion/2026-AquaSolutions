"""Flask app for the Gen-1 water-safety pipeline.

Routes
------
GET  /                — landing redirect (login or role default)
GET  /health          — liveness probe
GET  /login           — sign-in form
POST /login           — sign-in submit
GET  /logout          — clear session
GET  /dashboard       — station status (government role)
GET  /medical/report  — medical report form (medical role)
POST /medical/report  — medical report submit (medical role)
POST /sms             — Twilio webhook for inbound illness reports
POST /ingest          — sensor reading ingest (via sensor_ingest blueprint)
"""

from __future__ import annotations

import hmac
import json
import os
import re
import secrets
from datetime import date as date_cls, datetime, timedelta, timezone
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask, abort, redirect, render_template, request, session, url_for,
)
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from database import connection, init_db
from labels import label_readings_for_report
from sensor_ingest import sensor_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.register_blueprint(sensor_bp)
init_db()


STATION_PARSER_VERSION = "lenient_first_int_v1"
STATION_RE = re.compile(r"\b(\d{1,4})\b")


# ---------------------------------------------------------------------------
# Auth — hardcoded users with passwords from env (see issues_v3.md §D4 for
# the consent + storage caveats; this is demo-grade, not production).
# ---------------------------------------------------------------------------

DEMO_USERS: dict[str, dict[str, str]] = {
    "dr.smith": {
        "password": os.environ.get("MEDICAL_PASSWORD", "demo-medical-2026"),
        "role": "medical",
        "display_name": "Dr. Smith",
    },
    "official.jones": {
        "password": os.environ.get("GOV_PASSWORD", "demo-gov-2026"),
        "role": "government",
        "display_name": "Official Jones",
    },
}

ROLE_HOME = {
    "medical": "medical_report_form",
    "government": "dashboard",
}

SYMPTOMS = [
    ("diarrhoea",   "Diarrhoea"),
    ("vomiting",    "Vomiting"),
    ("fever",       "Fever"),
    ("dehydration", "Dehydration"),
]


def _authenticate(username: str, password: str) -> dict | None:
    user = DEMO_USERS.get(username)
    if user is None:
        return None
    # constant-time compare so login latency does not leak which usernames exist
    if not hmac.compare_digest(user["password"], password):
        return None
    return user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def role_required(role: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "username" not in session:
                return redirect(url_for("login", next=request.path))
            if session.get("role") != role:
                return ("forbidden — this page requires the "
                        f"'{role}' role", 403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


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


def _resolve_tier(report) -> dict:
    """Decide which tier to render and how. See spec §5 'Where the output is displayed'.

    Caller must pass a dict (use dict(row) for sqlite3.Row inputs)
    so .get() is available for the optional dialog_state field.
    """
    from estimator import estimate_risk_tier
    if report["risk_tier"] is not None:
        return {
            "tier_source": "reporter",
            "tier": report["risk_tier"],
            "tier_rationale": "",
            "tier_pending_text": "",
        }
    # No reporter tier — decide whether to estimate or show pending/incomplete.
    if report["report_source"] == "medical_portal":
        run_estimator = True
    else:  # sms
        run_estimator = (report.get("dialog_state") == "complete")

    if run_estimator:
        try:
            symptoms = json.loads(report["symptoms"] or "[]")
        except (json.JSONDecodeError, TypeError):
            symptoms = []
        onset = None
        if report["onset_date"]:
            try:
                onset = date_cls.fromisoformat(report["onset_date"])
            except ValueError:
                onset = None
        tier, rationale = estimate_risk_tier(
            symptoms=symptoms,
            onset_date=onset,
            case_count=report["case_count"] or 1,
        )
        return {
            "tier_source": "estimated",
            "tier": tier,
            "tier_rationale": rationale,
            "tier_pending_text": "",
        }

    # SMS, not complete
    state = report.get("dialog_state")
    if state in ("awaiting_case_count", "awaiting_symptoms", "awaiting_onset"):
        pending = "pending — awaiting reporter follow-up"
    else:
        pending = "incomplete — no structured data available"
    return {
        "tier_source": "pending",
        "tier": None,
        "tier_rationale": "",
        "tier_pending_text": pending,
    }


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


@app.get("/")
def index():
    if "role" in session:
        return redirect(url_for(ROLE_HOME[session["role"]]))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html", error=None)

    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""
    user = _authenticate(username, password)
    if user is None:
        return render_template(
            "login.html",
            error="Unknown username or wrong password.",
        ), 401

    session.clear()
    session["username"] = username
    session["display_name"] = user["display_name"]
    session["role"] = user["role"]

    next_path = request.args.get("next") or request.form.get("next") or ""
    # only allow internal redirects
    if next_path.startswith("/") and not next_path.startswith("//"):
        return redirect(next_path)
    return redirect(url_for(ROLE_HOME[user["role"]]))


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/medical/report")
@role_required("medical")
def medical_report_form():
    with connection() as conn:
        stations = conn.execute(
            "SELECT station_id, name FROM stations ORDER BY station_id"
        ).fetchall()
    return render_template(
        "medical_report.html",
        stations=stations,
        symptoms=SYMPTOMS,
        success_message=None,
        error_message=None,
    )


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
                "SELECT station_id, name FROM stations ORDER BY station_id"
            ).fetchall()
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

    # Anchor the labelling window at the end of the onset date when
    # provided (a partial implementation of the exposure-anchored rule
    # in labels.py option 1). Falls back to now.
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

    # Validate the selected symptoms against the canonical list.
    valid_keys = {key for key, _label in SYMPTOMS}
    symptoms_selected = [s for s in symptoms_selected if s in valid_keys]

    raw_message = (
        f"medical_portal | cases={case_count} | "
        f"symptoms={','.join(symptoms_selected) or 'none'} | "
        f"onset={onset_date_raw or 'n/a'} | notes={notes[:200]}"
    )

    with connection() as conn:
        station = conn.execute(
            "SELECT name FROM stations WHERE station_id = ?", (station_id,)
        ).fetchone()
        if station is None:
            return render(error=f"Station {station_id} is not in the system.")

        cursor = conn.execute(
            """
            INSERT INTO illness_reports
                (station_id, reporter_phone, raw_message, parser_version,
                 report_source, submitter, case_count, onset_date, symptoms,
                 risk_tier)
            VALUES (?, NULL, ?, ?, 'medical_portal', ?, ?, ?, ?, ?)
            """,
            (
                station_id,
                raw_message,
                STATION_PARSER_VERSION,
                session.get("username"),
                case_count,
                onset_date_raw or None,
                json.dumps(symptoms_selected),
                risk_tier_value,
            ),
        )
        report_id = cursor.lastrowid

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
        station = None
        if station_id is not None:
            station = conn.execute(
                "SELECT name FROM stations WHERE station_id = ?",
                (station_id,),
            ).fetchone()

        # Record the report regardless of whether the station resolved.
        # Persist station_id only when it actually exists, so the FK holds
        # and unparsed / unknown-station messages remain available for
        # human review via the dashboard's "unparsed" badge.
        resolved_station_id = station_id if station is not None else None
        cursor = conn.execute(
            """
            INSERT INTO illness_reports
                (station_id, reporter_phone, raw_message, parser_version)
            VALUES (?, ?, ?, ?)
            """,
            (resolved_station_id, reporter_phone, raw_message,
             STATION_PARSER_VERSION),
        )
        report_id = cursor.lastrowid

        if station_id is None:
            reply.message(
                "We received your message but could not identify a station "
                "number. Please reply with the station number "
                "(e.g. '4'). Thank you."
            )
            return str(reply)

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


STATION_STATUS_WINDOW_DAYS = 7


@app.get("/dashboard")
@role_required("government")
def dashboard():
    status_cutoff = (
        datetime.now(timezone.utc) - timedelta(days=STATION_STATUS_WINDOW_DAYS)
    ).isoformat()

    with connection() as conn:
        # One row per station: latest reading + a station-level status pill.
        # A station is `unsafe` if any illness report at that station landed
        # in the trailing STATION_STATUS_WINDOW_DAYS window — this is a
        # rollup, not a per-reading label, so newly-arriving readings do
        # not flip the pill back to `clear`.
        stations = conn.execute(
            """
            WITH latest AS (
                SELECT station_id, MAX(recorded_at) AS latest_at
                FROM sensor_readings
                GROUP BY station_id
            )
            SELECT s.station_id,
                   s.name,
                   r.recorded_at,
                   r.ph,
                   r.turbidity_ntu,
                   r.temperature_c,
                   r.rainfall_mm,
                   EXISTS (
                       SELECT 1 FROM illness_reports ir
                       WHERE ir.station_id = s.station_id
                         AND ir.received_at >= ?
                   ) AS is_unsafe
            FROM stations s
            LEFT JOIN latest l USING (station_id)
            LEFT JOIN sensor_readings r
                ON r.station_id = s.station_id
               AND r.recorded_at = l.latest_at
            ORDER BY s.station_id
            """,
            (status_cutoff,),
        ).fetchall()

        reports = conn.execute(
            """
            SELECT ir.report_id, ir.station_id, s.name AS station_name,
                   ir.reporter_phone, ir.raw_message, ir.received_at,
                   ir.risk_tier, ir.report_source,
                   ir.case_count, ir.symptoms, ir.onset_date,
                   (SELECT COUNT(*) FROM reading_labels
                     WHERE report_id = ir.report_id) AS readings_labelled
            FROM illness_reports ir
            LEFT JOIN stations s USING (station_id)
            ORDER BY ir.received_at DESC
            LIMIT 50
            """
        ).fetchall()

        # Compute the tier display for each report at render time.
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
            """
            SELECT ir.*, s.name AS station_name
            FROM illness_reports ir
            LEFT JOIN stations s USING (station_id)
            WHERE ir.report_id = ?
            """,
            (report_id,),
        ).fetchone()
        if row is None:
            abort(404)
        labelled_readings = conn.execute(
            """
            SELECT rl.reading_id, rl.rule_description,
                   sr.recorded_at, sr.ph, sr.turbidity_ntu, sr.temperature_c
            FROM reading_labels rl
            JOIN sensor_readings sr USING (reading_id)
            WHERE rl.report_id = ?
            ORDER BY sr.recorded_at DESC
            """,
            (report_id,),
        ).fetchall()

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
        **tier_block,
    )


@app.get("/medical/history")
@role_required("medical")
def medical_history():
    with connection() as conn:
        report_rows = conn.execute(
            """
            SELECT ir.*, s.name AS station_name
            FROM illness_reports ir
            LEFT JOIN stations s USING (station_id)
            WHERE ir.report_source = 'medical_portal'
            ORDER BY ir.received_at DESC
            LIMIT 50
            """,
        ).fetchall()
        stations = conn.execute(
            """
            SELECT s.station_id, s.name, s.latitude, s.longitude,
                   (SELECT COUNT(*) FROM illness_reports
                      WHERE station_id = s.station_id
                        AND report_source = 'medical_portal') AS report_count,
                   (SELECT MAX(received_at) FROM illness_reports
                      WHERE station_id = s.station_id
                        AND report_source = 'medical_portal') AS last_report
            FROM stations s
            ORDER BY s.station_id
            """,
        ).fetchall()

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
            """
            SELECT ir.*, s.name AS station_name
            FROM illness_reports ir
            LEFT JOIN stations s USING (station_id)
            WHERE ir.report_id = ?
            """,
            (report_id,),
        ).fetchone()
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


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug)
