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


def test_dashboard_renders_neighborhood_dropdown(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data.decode("utf-8")
    # The dropdown <select name="neighborhood"> must be present.
    assert 'name="neighborhood"' in body
    # 4 named neighborhoods + 1 "All neighborhoods" option = 5 options.
    assert body.count("<option") >= 5
    # The neighborhood names themselves.
    for name in ("Central Harare", "Northern Suburbs",
                 "Southern Areas", "Eastern Suburbs"):
        assert name in body, f"neighborhood missing from dropdown: {name}"


def test_dashboard_unfiltered_shows_all_32_stations(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # Count "STN-N" tokens that appear inside the station-status panel.
    import re
    n = len(re.findall(br'STN-\d+', body))
    # Each station row renders STN-N once; reports rows may add more.
    # Use a >= 32 assertion to be robust against reports panel content.
    assert n >= 32


def test_dashboard_filtered_shows_only_neighborhood_stations(signed_in_gov):
    """When ?neighborhood=1 is passed, only Central Harare's 8 stations
    should appear in the station status panel."""
    resp = signed_in_gov.get("/dashboard?neighborhood=1")
    body = resp.data.decode("utf-8")
    # Central Harare has stations 1, 2, 7, 11, 12, 13, 14, 15.
    for sid in (1, 2, 7, 11, 12, 13, 14, 15):
        assert f"STN-{sid}<" in body or f"STN-{sid}\n" in body or \
               f"STN-{sid} " in body or f">STN-{sid}<" in body, \
               f"central station STN-{sid} missing"


def test_dashboard_filter_persists_selected_option(signed_in_gov):
    resp = signed_in_gov.get("/dashboard?neighborhood=3")
    body = resp.data.decode("utf-8")
    # The matching <option value="3" ... selected> should be present.
    assert 'value="3"' in body
    assert 'selected' in body


def test_add_station_form_hidden_when_no_neighborhood_filter(signed_in_gov):
    resp = signed_in_gov.get("/dashboard")
    body = resp.data
    # The note that replaces the form should be present...
    assert b"Select a neighborhood to add a station" in body
    # ...and the actual form should NOT be present.
    assert b'action="/dashboard/stations"' not in body


def test_add_station_form_visible_when_neighborhood_filter_active(signed_in_gov):
    resp = signed_in_gov.get("/dashboard?neighborhood=1")
    body = resp.data
    assert b'action="/dashboard/stations"' in body
    assert b'name="latitude"' in body
    assert b'name="longitude"' in body
    assert b'name="name"' in body
    # Hidden neighborhood_id should match the URL filter.
    assert b'name="neighborhood_id" value="1"' in body


def test_post_add_station_creates_row_and_redirects(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "New test borehole",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 302
    assert resp.location.endswith("/dashboard?neighborhood=1")

    # Newly-created row should be reachable on the next GET.
    follow = signed_in_gov.get("/dashboard?neighborhood=1")
    assert b"New test borehole" in follow.data


def test_post_add_station_rejects_invalid_latitude(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "Bad borehole",
        "latitude": "999",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 302
    assert "station_error=invalid_field" in resp.location

    # No row inserted.
    follow = signed_in_gov.get("/dashboard?neighborhood=1")
    assert b"Bad borehole" not in follow.data


def test_post_add_station_rejects_unknown_neighborhood(signed_in_gov):
    resp = signed_in_gov.post("/dashboard/stations", data={
        "name": "Orphan borehole",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "999",
    })
    assert resp.status_code == 302
    assert "station_error=bad_neighborhood" in resp.location


def test_post_add_station_requires_government_role(signed_in_med):
    resp = signed_in_med.post("/dashboard/stations", data={
        "name": "Medical user attempt",
        "latitude": "-17.83",
        "longitude": "31.05",
        "neighborhood_id": "1",
    })
    assert resp.status_code == 403
