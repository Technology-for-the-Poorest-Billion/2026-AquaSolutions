from datetime import date

from etl.simulate import simulate_readings


def test_count_and_coverage():
    readings = simulate_readings([1, 7, 12], date(2026, 5, 1), date(2026, 5, 3), per_day=2, seed=1)
    # 3 stations * 3 days * 2/day
    assert len(readings) == 18
    assert {r["station_id"] for r in readings} == {1, 7, 12}


def test_deterministic():
    a = simulate_readings([1], date(2026, 5, 1), date(2026, 5, 2), per_day=1, seed=1)
    b = simulate_readings([1], date(2026, 5, 1), date(2026, 5, 2), per_day=1, seed=1)
    assert a == b


def test_reading_shape_and_ranges():
    r = simulate_readings([1], date(2026, 5, 1), date(2026, 5, 1), per_day=1, seed=1)[0]
    assert set(r) >= {"id", "station_id", "timestamp", "turbidity_ntu", "ph",
                      "temperature_c", "rainfall_mm", "chlorine_mg_l"}
    assert 0 <= r["ph"] <= 14
    assert r["turbidity_ntu"] >= 0
    assert r["id"]  # non-empty unique id


def test_ids_unique():
    readings = simulate_readings([1, 2], date(2026, 5, 1), date(2026, 5, 2), per_day=3, seed=2)
    ids = [r["id"] for r in readings]
    assert len(set(ids)) == len(ids)
