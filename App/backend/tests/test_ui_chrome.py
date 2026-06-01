"""Structural-markers regression net for the UI upgrade.

Walks the public routes and asserts the stable class hooks defined in
the spec (§10) are present. The test does not assert visual outcomes —
that's eyeballed manually. It asserts the *structural contract* so an
accidental rename of a class breaks the build instead of silently
breaking a page.

The set of pages this covers grows as templates convert (Tasks 4-7).
For Task 3 the only contract is "every page has the new topbar".
"""

from __future__ import annotations

import pytest


@pytest.fixture()
def signed_in_gov(client):
    client.post("/login", data={"username": "official.jones", "password": "gov-pw"})
    return client


@pytest.fixture()
def signed_in_med(client):
    client.post("/login", data={"username": "dr.smith", "password": "med-pw"})
    return client


def test_login_has_topbar_and_brand_mark(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_dashboard_has_topbar_and_brand_mark(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_medical_report_form_has_topbar_and_brand_mark(signed_in_med):
    resp = signed_in_med.get("/medical/report")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_medical_history_has_topbar_and_brand_mark(signed_in_med):
    resp = signed_in_med.get("/medical/history")
    assert resp.status_code == 200
    assert b'class="topbar"' in resp.data
    assert b'class="brand-mark"' in resp.data


def test_login_uses_login_card_and_no_disclaimer(client):
    """Login overrides the disclaimer block to empty and renders a
    centered card with the brand mark above the form."""
    resp = client.get("/login")
    body = resp.data
    assert b'class="login-card"' in body
    # The body class signals login layout so app.css can centre the card.
    assert b'app-login' in body
    # Disclaimer block is overridden to empty.
    assert b'class="disclaim"' not in body
    # Form fields still present.
    assert b'name="username"' in body
    assert b'name="password"' in body


def test_dashboard_uses_panels_rows_and_pills(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # Two-column grid for the two panels (65/35-ish split via grid-2-asym).
    assert b'class="grid-2-asym"' in body
    # Two panels (Station status + Recent illness reports).
    assert body.count(b'class="panel"') >= 2
    # At least one status pill (clear/severe/unsafe).
    assert (
        b'class="pill pill-clear"' in body
        or b'class="pill pill-severe"' in body
    )


def test_medical_report_form_uses_chips_and_segmented(signed_in_med):
    resp = signed_in_med.get("/medical/report")
    body = resp.data
    assert b'class="form-grid-3"' in body
    assert b'class="chip"' in body or b"class='chip'" in body
    assert b'class="segmented"' in body


def test_medical_history_uses_panels(signed_in_med):
    resp = signed_in_med.get("/medical/history")
    body = resp.data
    # Two panels: the map and the reports table.
    assert body.count(b'class="panel"') >= 2


def test_medical_report_detail_uses_kv(signed_in_med):
    # Need a report row to exist. Skip if none — that's a fixture problem,
    # not a UI bug.
    from sqlalchemy import text as sql_text
    import sys
    db = sys.modules['database']
    with db.connection() as conn:
        row = conn.execute(sql_text(
            "SELECT report_id FROM illness_reports "
            "WHERE report_source='medical_portal' LIMIT 1"
        )).fetchone()
    if row is None:
        pytest.skip("no medical_portal report fixture available")
    resp = signed_in_med.get(f"/medical/reports/{row[0]}")
    assert resp.status_code == 200
    assert b'class="kv"' in resp.data


def test_dashboard_report_detail_uses_grid_and_actions(signed_in_gov):
    from sqlalchemy import text as sql_text
    import sys
    db = sys.modules['database']
    with db.connection() as conn:
        row = conn.execute(sql_text(
            "SELECT report_id FROM illness_reports LIMIT 1"
        )).fetchone()
    if row is None:
        pytest.skip("no report fixture available")
    resp = signed_in_gov.get(f"/dashboard/reports/{row[0]}")
    assert resp.status_code == 200
    body = resp.data
    assert b'class="grid-2-asym"' in body
    assert b'class="kv"' in body
    assert b'class="btn' in body
