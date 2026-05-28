def test_stations_has_is_closed_column(app):
    from database import connection
    with connection() as c:
        cols = {r["name"] for r in c.execute("PRAGMA table_info(stations)").fetchall()}
        assert "is_closed" in cols
        row = c.execute("SELECT is_closed FROM stations WHERE station_id = 1").fetchone()
        assert row["is_closed"] == 0  # default


def test_interventions_table_exists_and_constrains_action(app):
    from database import connection
    import sqlite3
    with connection() as c:
        cols = {r["name"] for r in c.execute("PRAGMA table_info(interventions)").fetchall()}
        assert {"station_id", "action_type", "triggered_by",
                "triggered_at", "related_report_id", "notes"}.issubset(cols)
        c.execute(
            "INSERT INTO interventions (station_id, action_type, triggered_by) "
            "VALUES (1, 'close_borehole', 'official.jones')"
        )
        try:
            c.execute(
                "INSERT INTO interventions (station_id, action_type, triggered_by) "
                "VALUES (1, 'bogus_action', 'x')"
            )
            assert False, "CHECK should have rejected bogus action_type"
        except sqlite3.IntegrityError:
            pass


def test_illness_reports_has_dialog_state_column(app):
    from database import connection
    import sqlite3
    with connection() as c:
        cols = {r["name"] for r in c.execute("PRAGMA table_info(illness_reports)").fetchall()}
        assert "dialog_state" in cols

        valid = ["awaiting_case_count", "awaiting_symptoms", "awaiting_onset",
                 "complete", "abandoned"]
        for s in valid:
            c.execute(
                "INSERT INTO illness_reports (raw_message, parser_version, dialog_state) "
                "VALUES (?, 'v', ?)", ("t", s)
            )
        try:
            c.execute(
                "INSERT INTO illness_reports (raw_message, parser_version, dialog_state) "
                "VALUES ('t', 'v', 'bogus')"
            )
            assert False, "CHECK should reject bogus state"
        except sqlite3.IntegrityError:
            pass


def test_illness_reports_has_risk_tier_column(app):
    """risk_tier must exist on illness_reports; NULL allowed; CHECK enforced."""
    from database import connection
    with connection() as c:
        cols = {r["name"]: r for r in c.execute("PRAGMA table_info(illness_reports)").fetchall()}
        assert "risk_tier" in cols
        # CHECK is enforced at INSERT time
        c.execute(
            "INSERT INTO illness_reports (raw_message, parser_version, risk_tier) "
            "VALUES ('test', 'v', 'low')"
        )
        c.execute(
            "INSERT INTO illness_reports (raw_message, parser_version, risk_tier) "
            "VALUES ('test', 'v', NULL)"
        )
        import sqlite3
        try:
            c.execute(
                "INSERT INTO illness_reports (raw_message, parser_version, risk_tier) "
                "VALUES ('test', 'v', 'bogus')"
            )
            assert False, "CHECK constraint should have rejected 'bogus'"
        except sqlite3.IntegrityError:
            pass
