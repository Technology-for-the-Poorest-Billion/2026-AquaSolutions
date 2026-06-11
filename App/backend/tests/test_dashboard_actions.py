def test_dashboard_has_action_buttons_per_station(gov_session):
    r = gov_session.get("/dashboard")
    body = r.data.decode("utf-8")
    assert "close_borehole" in body
    assert "dispatch_sample_team" in body
    assert "dispatch_medical_team" in body


def test_dashboard_shows_lock_badge_for_closed_station(gov_session):
    gov_session.post("/actions", data={"action_type": "close_borehole", "station_id": "1"})
    r = gov_session.get("/dashboard")
    body = r.data.decode("utf-8")
    assert "\U0001F512" in body or "lock" in body.lower()


def test_closed_station_shows_reopen_not_close(gov_session):
    gov_session.post("/actions", data={"action_type": "close_borehole", "station_id": "1"})
    r = gov_session.get("/dashboard")
    body = r.data.decode("utf-8")
    assert "reopen_borehole" in body
