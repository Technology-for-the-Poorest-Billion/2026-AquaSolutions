"""Seed data for the neighborhoods feature: 4 neighborhoods, 32 stations,
each neighborhood gets exactly 8 stations, and the stations sequence is
advanced past the highest seeded id."""

from __future__ import annotations

import sys

from sqlalchemy import text

from database import connection, init_db


def test_four_neighborhoods_seeded(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        rows = conn.execute(text(
            "SELECT neighborhood_id, name FROM neighborhoods ORDER BY neighborhood_id"
        )).fetchall()
    assert [r[0] for r in rows] == [1, 2, 3, 4]
    assert [r[1] for r in rows] == [
        "Central Harare",
        "Northern Suburbs",
        "Southern Areas",
        "Eastern Suburbs",
    ]


def test_thirty_two_stations_seeded(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM stations")).scalar()
    assert total == 32


def test_each_neighborhood_has_eight_stations(tmp_db_path):
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        rows = conn.execute(text(
            "SELECT neighborhood_id, COUNT(*) FROM stations "
            "GROUP BY neighborhood_id ORDER BY neighborhood_id"
        )).fetchall()
    assert rows == [(1, 8), (2, 8), (3, 8), (4, 8)]


def test_insert_after_seed_does_not_collide(tmp_db_path):
    """After seeding stations 1-32 with explicit IDs, an INSERT without
    an explicit station_id must produce id >= 33. On SQLite this is the
    AUTOINCREMENT default; on Postgres it requires the sequence to have
    been advanced by setval()."""
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        with conn.begin():
            new_id = conn.execute(text(
                "INSERT INTO stations (name, latitude, longitude, neighborhood_id) "
                "VALUES ('test-station', -17.83, 31.05, 1) RETURNING station_id"
            )).scalar()
    assert new_id >= 33, f"expected id >= 33, got {new_id}"


def test_existing_station_ids_reassigned_to_neighborhoods(tmp_db_path):
    """Stations 1-10 (the pre-feature seed) get assigned to their
    correct neighborhood via ON CONFLICT DO UPDATE."""
    sys.modules.pop("engine", None)
    sys.modules.pop("database", None)
    from database import init_db, connection

    init_db()
    with connection() as conn:
        rows = dict(conn.execute(text(
            "SELECT station_id, neighborhood_id FROM stations "
            "WHERE station_id <= 10 ORDER BY station_id"
        )).fetchall())
    # From spec §4:
    expected = {
        1: 1,   # Avenues          Central Harare
        2: 1,   # Belvedere        Central Harare
        3: 4,   # Eastlea          Eastern Suburbs
        4: 3,   # Mbare            Southern Areas
        5: 3,   # Hatfield         Southern Areas
        6: 2,   # Newlands         Northern Suburbs
        7: 1,   # Milton Park      Central Harare
        8: 4,   # Hillside         Eastern Suburbs
        9: 2,   # Mt Pleasant      Northern Suburbs
        10: 4,  # Greendale        Eastern Suburbs
    }
    assert rows == expected
