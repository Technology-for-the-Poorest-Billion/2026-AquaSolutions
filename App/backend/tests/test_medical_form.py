"""Tests for /medical/report — the risk-tier segmented control and its persistence."""


def test_form_renders_risk_tier_segmented(med_session):
    r = med_session.get("/medical/report")
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    # Hidden input carries the submitted value; segmented control holds the tiers.
    assert 'name="risk_tier"' in body
    # All five tiers must be present (hidden input default "" + four data-tier spans).
    assert 'data-tier=""' in body                # "Not assessed"
    assert 'data-tier="low"' in body
    assert 'data-tier="medium"' in body
    assert 'data-tier="high"' in body
    assert 'data-tier="severe"' in body


def test_submitting_with_risk_tier_persists_it(med_session):
    from sqlalchemy import text
    r = med_session.post("/medical/report", data={
        "station_id": "1",
        "case_count": "3",
        "symptoms": ["diarrhoea"],
        "onset_date": "",
        "notes": "",
        "risk_tier": "high",
    })
    assert r.status_code == 200
    from database import connection
    with connection() as c:
        row = c.execute(text("SELECT risk_tier FROM illness_reports ORDER BY report_id DESC LIMIT 1")).fetchone()
        assert row[0] == "high"


def test_submitting_without_risk_tier_stores_null(med_session):
    from sqlalchemy import text
    r = med_session.post("/medical/report", data={
        "station_id": "2",
        "case_count": "1",
        "symptoms": [],
        "onset_date": "",
        "notes": "",
        "risk_tier": "",
    })
    assert r.status_code == 200
    from database import connection
    with connection() as c:
        row = c.execute(text("SELECT risk_tier FROM illness_reports ORDER BY report_id DESC LIMIT 1")).fetchone()
        assert row[0] is None


def test_submitting_bogus_risk_tier_is_rejected(med_session):
    r = med_session.post("/medical/report", data={
        "station_id": "1",
        "case_count": "1",
        "symptoms": [],
        "onset_date": "",
        "notes": "",
        "risk_tier": "bogus_value",
    })
    # Should be rejected at render-time validation, not crash on DB CHECK.
    assert r.status_code == 200
    body = r.data.decode("utf-8")
    assert "error" in body.lower() or "invalid" in body.lower()
