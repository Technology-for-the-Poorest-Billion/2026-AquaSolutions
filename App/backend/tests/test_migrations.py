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
