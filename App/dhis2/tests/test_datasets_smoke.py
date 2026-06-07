"""End-to-end: build both CSVs against the live DHIS2. Skips if DHIS2 is down."""

import csv
from pathlib import Path

import pytest
import requests

from metadata import import_metadata as im
from etl import build


def _dhis2_up():
    try:
        return requests.get(f"{im.base_url()}/api/system/info.json", auth=im.auth(), timeout=5).ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")

DATA = Path(build.__file__).resolve().parents[1] / "data"


def _read(name):
    with open(DATA / name, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_build_produces_two_linked_csvs():
    build.main()
    reports = _read("reports.csv")
    water = _read("labeled_water_readings.csv")
    assert reports, "reports.csv is empty"
    assert water, "labeled_water_readings.csv is empty"

    # reports.csv has core + symptom columns
    assert {"event_id", "timestamp", "station_id", "case_count"} <= set(reports[0])
    assert "diarrhoea" in reports[0]

    # water CSV has the partner's label fields
    assert {"reading_id", "station_id", "label", "confidence", "score", "unsafe"} <= set(water[0])
    assert all(r["label"] in ("at_risk", "unlabelled") for r in water)

    # linkage: every water station_id appears among report station_ids
    report_stations = {r["station_id"] for r in reports}
    assert {r["station_id"] for r in water} <= report_stations

    # the labelling actually fired somewhere (clustered demo reports -> at_risk)
    assert any(r["label"] == "at_risk" for r in water)
