"""user_preferences table is created and is upsertable by username."""

from __future__ import annotations

import sys

from sqlalchemy import inspect, text

from database import connection, init_db


def test_user_preferences_table_exists(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db

    init_db()
    with connection() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("user_preferences")}
    assert cols == {"username", "language"}


def test_user_preferences_upsert_by_username(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        with conn.begin():
            conn.execute(
                text(
                    "INSERT INTO user_preferences (username, language) "
                    "VALUES (:u, :c) "
                    "ON CONFLICT (username) DO UPDATE SET language = excluded.language"
                ),
                {"u": "dr.smith", "c": "sn"},
            )
            conn.execute(
                text(
                    "INSERT INTO user_preferences (username, language) "
                    "VALUES (:u, :c) "
                    "ON CONFLICT (username) DO UPDATE SET language = excluded.language"
                ),
                {"u": "dr.smith", "c": "nd"},
            )
        rows = conn.execute(
            text("SELECT username, language FROM user_preferences")
        ).fetchall()
    assert rows == [("dr.smith", "nd")]
