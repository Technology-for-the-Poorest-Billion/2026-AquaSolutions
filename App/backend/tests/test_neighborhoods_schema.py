"""Schema changes for the neighborhoods feature.

Verifies that init_db() creates the neighborhoods table and adds the
neighborhood_id column to stations. Seed-data correctness is checked
in test_neighborhoods_seed.py — this module is structural only.
"""

from __future__ import annotations

from sqlalchemy import inspect

from database import connection, init_db


def test_neighborhoods_table_exists(tmp_db_path):
    init_db()
    with connection() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("neighborhoods")}
    assert cols == {"neighborhood_id", "name"}


def test_stations_has_neighborhood_id_column(tmp_db_path):
    init_db()
    with connection() as conn:
        cols = {c["name"] for c in inspect(conn).get_columns("stations")}
    assert "neighborhood_id" in cols
