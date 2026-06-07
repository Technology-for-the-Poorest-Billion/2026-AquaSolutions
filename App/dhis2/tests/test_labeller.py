from datetime import datetime, timedelta

from etl.labeller import label_readings


def test_three_fresh_reports_label_at_risk():
    now = datetime(2026, 6, 1, 12, 0, 0)
    readings = [{"id": "x1", "station_id": 7, "timestamp": now}]
    reports = [
        {"station_id": 7, "timestamp": now - timedelta(hours=1)},
        {"station_id": 7, "timestamp": now - timedelta(hours=3)},
        {"station_id": 7, "timestamp": now - timedelta(hours=5)},
    ]
    out = label_readings(readings, reports)
    assert len(out) == 1
    assert out[0]["label"] == "at_risk"
    assert out[0]["confidence"] == 0.9


def test_no_reports_unlabelled():
    now = datetime(2026, 6, 1, 12, 0, 0)
    out = label_readings([{"id": "x", "station_id": 1, "timestamp": now}], [])
    assert out[0]["label"] == "unlabelled"


def test_reports_at_other_station_do_not_leak():
    now = datetime(2026, 6, 1, 12, 0, 0)
    readings = [{"id": "x", "station_id": 1, "timestamp": now}]
    reports = [{"station_id": 2, "timestamp": now - timedelta(hours=1)}]
    assert label_readings(readings, reports)[0]["label"] == "unlabelled"
