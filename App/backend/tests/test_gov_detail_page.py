"""Tests for /dashboard/reports/<id> — the government per-report detail page."""

import json
from datetime import date, timedelta


def _insert_report(reporter_supplied=False, source="medical_portal"):
    """Helper: insert a report directly via DB and return its id."""
    from database import connection
    with connection() as c:
        cur = c.execute(
            "INSERT INTO illness_reports "
            "(station_id, raw_message, parser_version, report_source, "
            " submitter, case_count, onset_date, symptoms, risk_tier) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                1,
                "test message",
                "test_parser_v1",
                source,
                "dr.smith" if source == "medical_portal" else None,
                3,
                date.today().isoformat(),
                json.dumps(["diarrhoea", "dehydration"]),
                "high" if reporter_supplied else None,
            ),
        )
        return cur.lastrowid


def test_anonymous_redirected_to_login(client):
    rid = _insert_report()
    r = client.get(f"/dashboard/reports/{rid}", follow_redirects=False)
    assert r.status_code == 302
    assert "/login" in r.headers["Location"]


def test_medical_user_gets_403_with_link(med_session):
    rid = _insert_report()
    r = med_session.get(f"/dashboard/reports/{rid}")
    assert r.status_code == 403
    assert f"/medical/reports/{rid}".encode() in r.data


def test_gov_user_sees_report(gov_session):
    rid = _insert_report()
    r = gov_session.get(f"/dashboard/reports/{rid}")
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert f"Report #{rid}" in body
    assert "diarrhoea" in body
    assert "dehydration" in body
    assert "Borehole A" in body  # station 1 name


def test_unknown_report_returns_404(gov_session):
    r = gov_session.get("/dashboard/reports/99999")
    assert r.status_code == 404


def test_reporter_supplied_tier_renders_without_estimator_banner(gov_session):
    rid = _insert_report(reporter_supplied=True)  # risk_tier='high'
    r = gov_session.get(f"/dashboard/reports/{rid}")
    body = r.data.decode("utf-8")
    assert "Reporter's clinical assessment" in body
    assert "Estimated by automated heuristic" not in body


def test_missing_tier_triggers_estimator_with_banner(gov_session):
    rid = _insert_report(reporter_supplied=False)  # risk_tier=NULL
    r = gov_session.get(f"/dashboard/reports/{rid}")
    body = r.data.decode("utf-8")
    assert "Estimated risk tier" in body
    assert "Estimated by automated heuristic" in body
    assert "not medical advice" in body.lower()
