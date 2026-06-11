# Reports + Partner-Labelled Water Datasets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce two linked CSVs — `reports.csv` (one row per DHIS2 illness report, symptoms as 0/1 columns + timestamp) and `labeled_water_readings.csv` (synthetic water readings labelled by the project partner's decay-scoring logic) — joined on `station_id`.

**Architecture:** A small ETL package `App/dhis2/etl/` with focused, mostly-pure modules: `simulate` (synthetic readings), `reports` (pull + flatten DHIS2 events), `labeller` (dynamically import the partner's `label_readings()` from `Data/Labelling/Labelling Logic.py`, untouched), and `build` (orchestrate → two CSVs). Pure logic is unit-tested; DHIS2-dependent steps are integration tests that skip when the instance is down.

**Tech Stack:** Python 3 (`requests`, `pytest`, stdlib `csv`/`datetime`/`importlib`), reusing `App/dhis2/metadata/import_metadata.py` for DHIS2 auth, and the committed `metadata/program_illness.json` + `metadata/org_units.json` as the data-element/org-unit maps.

**Scope:** This is Plan 1 of 2 from `App/docs/superpowers/specs/2026-06-07-reports-csv-labelling-sms-design.md`. Plan 2 = the SMS→DHIS2 bridge.

**Prerequisites:** DHIS2 running at `http://localhost:8080` (`admin`/`district`) with the illness program + the ~96 demo reports. Tests run from `App/dhis2/` (its `pytest.ini` sets `pythonpath = .`). Verify:
`curl -fsu admin:district "http://localhost:8080/api/tracker/events.json?program=eWh8gc8ubdW&pageSize=1&totalPages=true" | python3 -c "import sys,json;print(json.load(sys.stdin)['pager']['total'],'events')"` → a non-zero count.

## File Structure

| File | Responsibility |
|------|----------------|
| `App/dhis2/etl/__init__.py` | package marker |
| `App/dhis2/etl/simulate.py` | pure: synthetic water readings for stations over a date range |
| `App/dhis2/etl/labeller.py` | dynamically load the partner's `label_readings()` (filename has a space) |
| `App/dhis2/etl/reports.py` | pure `report_event_to_row()` + DHIS2 fetch + `reports.csv` writer |
| `App/dhis2/etl/build.py` | orchestrate: reports → simulate → label → both CSVs |
| `App/dhis2/tests/test_simulate.py` | unit tests for `simulate` |
| `App/dhis2/tests/test_labeller.py` | verify we're calling the partner's logic |
| `App/dhis2/tests/test_reports_mapping.py` | unit tests for `report_event_to_row` |
| `App/dhis2/tests/test_datasets_smoke.py` | end-to-end integration (skips if DHIS2 down) |
| `App/dhis2/Makefile` | add `datasets` target |
| `App/dhis2/.gitignore` | ignore generated `data/` outputs |

Outputs: `App/dhis2/data/reports.csv`, `App/dhis2/data/labeled_water_readings.csv` (generated, git-ignored).

---

### Task 1: Synthetic water readings (`etl/simulate.py`)

Pure and deterministic — no DHIS2 needed. Generates readings per station across a date range.

**Files:**
- Create: `App/dhis2/etl/__init__.py`
- Create: `App/dhis2/etl/simulate.py`
- Test: `App/dhis2/tests/test_simulate.py`

- [ ] **Step 1: Write the failing test**

Create `App/dhis2/tests/test_simulate.py`:

```python
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
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/dhis2 && python -m pytest tests/test_simulate.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.simulate'`.

- [ ] **Step 3: Implement**

Create empty `App/dhis2/etl/__init__.py`.

Create `App/dhis2/etl/simulate.py`:

```python
"""Synthetic borehole water-quality readings. SYNTHETIC DATA ONLY — there is no
real sensor feed yet; this exercises the labelling pipeline, not real measurements.

Deterministic given (stations, date range, per_day, seed). Timestamps are spread
through each day so multiple readings per day are distinct.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta


def _daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def simulate_readings(station_ids, start: date, end: date, per_day: int = 1, seed: int = 0):
    rng = random.Random(seed)
    readings = []
    for station_id in station_ids:
        for day in _daterange(start, end):
            for k in range(per_day):
                # spread readings across the working day
                hour = 8 + int(k * (10 / max(per_day, 1)))
                ts = datetime(day.year, day.month, day.day, hour, 0, 0)
                readings.append({
                    "id": f"R-{station_id}-{day.isoformat()}-{k}",
                    "station_id": station_id,
                    "timestamp": ts,
                    "turbidity_ntu": round(rng.uniform(0.5, 12.0), 2),
                    "ph": round(rng.uniform(6.0, 8.5), 2),
                    "temperature_c": round(rng.uniform(18.0, 30.0), 1),
                    "rainfall_mm": round(rng.uniform(0.0, 25.0), 1),
                    "chlorine_mg_l": round(rng.uniform(0.0, 1.5), 2),
                })
    return readings
```

- [ ] **Step 4: Run it — expect pass**

Run: `cd App/dhis2 && python -m pytest tests/test_simulate.py -q`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add App/dhis2/etl/__init__.py App/dhis2/etl/simulate.py App/dhis2/tests/test_simulate.py
git commit -m "Add synthetic water-reading simulator (etl/simulate)"
```

---

### Task 2: Load the partner's labeller (`etl/labeller.py`)

We must **call the partner's logic, not copy it.** The file `Data/Labelling/Labelling Logic.py` has a space in its name, so import it via `importlib`.

**Files:**
- Create: `App/dhis2/etl/labeller.py`
- Test: `App/dhis2/tests/test_labeller.py`

- [ ] **Step 1: Write the failing test**

Create `App/dhis2/tests/test_labeller.py`:

```python
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
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/dhis2 && python -m pytest tests/test_labeller.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.labeller'`.

- [ ] **Step 3: Implement**

Create `App/dhis2/etl/labeller.py`:

```python
"""Thin loader around the project partner's labelling logic. We import and call
their `label_readings()` UNCHANGED — the labelling scheme is partner-owned
(spec D15 / E4). The source file's name contains a space, so we load it by path.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

# App/dhis2/etl/labeller.py -> parents[3] is the repo root
_PARTNER_FILE = Path(__file__).resolve().parents[3] / "Data" / "Labelling" / "Labelling Logic.py"


def _load_partner_module():
    spec = importlib.util.spec_from_file_location("partner_labelling", str(_PARTNER_FILE))
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load partner labelling logic at {_PARTNER_FILE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def label_readings(readings, reports):
    """Delegate to the partner's batch labeller. Returns their result verbatim:
    [{reading_id, station_id, timestamp, label, confidence, score}, ...]."""
    return _load_partner_module().label_readings(readings, reports)
```

- [ ] **Step 4: Run it — expect pass**

Run: `cd App/dhis2 && python -m pytest tests/test_labeller.py -q`
Expected: PASS (3 passed). If `test_three_fresh_reports_label_at_risk` fails on the confidence value, the partner changed their tiers — read the failure and align the test to their current output (do NOT change their logic).

- [ ] **Step 5: Commit**

```bash
git add App/dhis2/etl/labeller.py App/dhis2/tests/test_labeller.py
git commit -m "Add loader for partner labelling logic (etl/labeller)"
```

---

### Task 3: Flatten a DHIS2 report event to a CSV row (`etl/reports.py`, pure part)

The pure mapping is unit-testable without DHIS2. It turns one event + the committed metadata maps into a flat dict.

**Files:**
- Create: `App/dhis2/etl/reports.py`
- Test: `App/dhis2/tests/test_reports_mapping.py`

- [ ] **Step 1: Write the failing test**

Create `App/dhis2/tests/test_reports_mapping.py`:

```python
from etl.reports import report_event_to_row, SYMPTOM_PREFIX

DE = {
    "deCASE": "Illness - Case Count",
    "deONSET": "Illness - Onset Date",
    "deDIAR": "Symptom: Diarrhoea",
    "deVOM": "Symptom: Vomiting",
}
OU = {
    "ouBORE": {"name": "Milton Park — health post", "code": "STATION-7", "parent": "ouNBH"},
    "ouNBH": {"name": "Central Harare", "code": None, "parent": "ouDIST"},
}
SYMPTOMS = ["Diarrhoea", "Vomiting"]


def _event():
    return {
        "event": "evt1",
        "occurredAt": "2026-06-05T00:00:00.000",
        "orgUnit": "ouBORE",
        "dataValues": [
            {"dataElement": "deCASE", "value": "5"},
            {"dataElement": "deONSET", "value": "2026-06-03"},
            {"dataElement": "deDIAR", "value": "true"},
        ],
    }


def test_row_core_fields():
    row = report_event_to_row(_event(), DE, OU, SYMPTOMS)
    assert row["event_id"] == "evt1"
    assert row["timestamp"] == "2026-06-05T00:00:00.000"
    assert row["onset_date"] == "2026-06-03"
    assert row["station_id"] == 7
    assert row["borehole"] == "Milton Park — health post"
    assert row["neighbourhood"] == "Central Harare"
    assert row["case_count"] == 5


def test_symptom_columns_are_0_or_1():
    row = report_event_to_row(_event(), DE, OU, SYMPTOMS)
    assert row["diarrhoea"] == 1   # ticked
    assert row["vomiting"] == 0    # absent
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/dhis2 && python -m pytest tests/test_reports_mapping.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'etl.reports'`.

- [ ] **Step 3: Implement (pure part + map loaders)**

Create `App/dhis2/etl/reports.py`:

```python
"""Pull DHIS2 Community Illness Reports events and flatten them to CSV rows.

The pure `report_event_to_row` is unit-tested; `fetch_report_events` + the maps
require a running DHIS2 and are covered by the smoke test.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import requests

from metadata import import_metadata as im

SYMPTOM_PREFIX = "Symptom: "
METADATA_DIR = Path(__file__).resolve().parents[1] / "metadata"
PROGRAM_FILE = METADATA_DIR / "program_illness.json"
ORG_UNITS_FILE = METADATA_DIR / "org_units.json"


def load_maps():
    """Return (de_by_id, ou_by_id, symptom_names) from the committed metadata."""
    prog = json.loads(PROGRAM_FILE.read_text())
    de_by_id = {d["id"]: d["name"] for d in prog["dataElements"]}
    symptom_names = sorted(
        n[len(SYMPTOM_PREFIX):] for n in de_by_id.values() if n.startswith(SYMPTOM_PREFIX)
    )
    ous = json.loads(ORG_UNITS_FILE.read_text())["organisationUnits"]
    ou_by_id = {
        o["id"]: {"name": o["name"], "code": o.get("code"),
                  "parent": (o.get("parent") or {}).get("id")}
        for o in ous
    }
    return de_by_id, ou_by_id, symptom_names


def report_event_to_row(event, de_by_id, ou_by_id, symptom_names):
    values = {dv["dataElement"]: dv["value"] for dv in event.get("dataValues", [])}
    name_to_value = {de_by_id.get(de_id, de_id): val for de_id, val in values.items()}

    ou = ou_by_id[event["orgUnit"]]
    parent = ou_by_id.get(ou["parent"], {})
    station_id = int(ou["code"].split("-")[1]) if ou.get("code") else None

    case_raw = name_to_value.get("Illness - Case Count")
    row = {
        "event_id": event["event"],
        "timestamp": event["occurredAt"],
        "onset_date": name_to_value.get("Illness - Onset Date", ""),
        "station_id": station_id,
        "borehole": ou["name"],
        "neighbourhood": parent.get("name", ""),
        "case_count": int(case_raw) if case_raw not in (None, "") else None,
    }
    for sym in symptom_names:
        row[sym.lower().replace(" ", "_")] = 1 if name_to_value.get(SYMPTOM_PREFIX + sym) == "true" else 0
    return row


def fetch_report_events(program_uid="eWh8gc8ubdW"):
    """Fetch all illness-report events from DHIS2 (requires a running instance)."""
    root = json.loads(ORG_UNITS_FILE.read_text())["organisationUnits"]
    root_uid = next(o["id"] for o in root if o["level"] == 1)
    r = requests.get(
        f"{im.base_url()}/api/tracker/events.json",
        params={"program": program_uid, "orgUnit": root_uid, "ouMode": "DESCENDANTS",
                "fields": "event,occurredAt,orgUnit,dataValues[dataElement,value]",
                "pageSize": 10000, "skipPaging": "true"},
        auth=im.auth(), timeout=60,
    )
    r.raise_for_status()
    return r.json().get("events", [])


def build_report_rows():
    """Fetch events + maps, return (rows, reports_for_labelling)."""
    de_by_id, ou_by_id, symptom_names = load_maps()
    rows = [report_event_to_row(e, de_by_id, ou_by_id, symptom_names)
            for e in fetch_report_events()]
    return rows, symptom_names


def write_csv(rows, fieldnames, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
```

- [ ] **Step 4: Run it — expect pass**

Run: `cd App/dhis2 && python -m pytest tests/test_reports_mapping.py -q`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add App/dhis2/etl/reports.py App/dhis2/tests/test_reports_mapping.py
git commit -m "Add DHIS2 report event -> CSV row mapping + fetch (etl/reports)"
```

---

### Task 4: Orchestrate both CSVs (`etl/build.py`)

Ties it together: fetch reports → write `reports.csv`; simulate readings over the reports' date span → label via the partner → write `labeled_water_readings.csv` (joined to reports by `station_id`).

**Files:**
- Create: `App/dhis2/etl/build.py`

- [ ] **Step 1: Implement**

Create `App/dhis2/etl/build.py`:

```python
"""Build the two linked datasets:
  data/reports.csv                 (one row per DHIS2 illness report)
  data/labeled_water_readings.csv  (synthetic readings labelled by the partner)
Linked by station_id (+ the partner's 7-day window).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from etl import reports as R
from etl.labeller import label_readings
from etl.simulate import simulate_readings

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SEED = 7
PER_DAY = 1


def _parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "").split(".")[0])


def main():
    de_by_id, ou_by_id, symptom_names = R.load_maps()
    events = R.fetch_report_events()
    rows = [R.report_event_to_row(e, de_by_id, ou_by_id, symptom_names) for e in events]

    report_fields = ["event_id", "timestamp", "onset_date", "station_id", "borehole",
                     "neighbourhood", "case_count"] + [s.lower().replace(" ", "_") for s in symptom_names]
    R.write_csv(rows, report_fields, DATA_DIR / "reports.csv")
    print(f"wrote {len(rows)} reports -> {DATA_DIR/'reports.csv'}")

    # reports for the partner labeller: station_id + timestamp(datetime)
    reports_for_label = [{"station_id": r["station_id"], "timestamp": _parse_ts(r["timestamp"])}
                         for r in rows if r["station_id"] is not None]

    # simulate readings across the reports' date span, for the stations that reported
    if rows:
        dates = sorted(_parse_ts(r["timestamp"]).date() for r in rows)
        start, end = dates[0], dates[-1]
    else:
        from datetime import date
        start = end = date.today()
    station_ids = sorted({r["station_id"] for r in rows if r["station_id"] is not None})
    readings = simulate_readings(station_ids, start, end, per_day=PER_DAY, seed=SEED)

    labels = label_readings(readings, reports_for_label)
    label_by_id = {l["reading_id"]: l for l in labels}

    out = []
    for rd in readings:
        lab = label_by_id.get(rd["id"], {})
        out.append({
            "reading_id": rd["id"], "station_id": rd["station_id"],
            "timestamp": rd["timestamp"].isoformat(),
            "turbidity_ntu": rd["turbidity_ntu"], "ph": rd["ph"],
            "temperature_c": rd["temperature_c"], "rainfall_mm": rd["rainfall_mm"],
            "chlorine_mg_l": rd["chlorine_mg_l"],
            "score": lab.get("score"), "confidence": lab.get("confidence"),
            "label": lab.get("label", "unlabelled"),
            "unsafe": 1 if lab.get("label") == "at_risk" else 0,
        })
    water_fields = ["reading_id", "station_id", "timestamp", "turbidity_ntu", "ph",
                    "temperature_c", "rainfall_mm", "chlorine_mg_l",
                    "score", "confidence", "label", "unsafe"]
    R.write_csv(out, water_fields, DATA_DIR / "labeled_water_readings.csv")
    n_atrisk = sum(1 for o in out if o["label"] == "at_risk")
    print(f"wrote {len(out)} readings ({n_atrisk} at_risk) -> {DATA_DIR/'labeled_water_readings.csv'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Commit (no unit test here — covered by the Task 5 smoke test)**

```bash
git add App/dhis2/etl/build.py
git commit -m "Add dataset orchestrator producing both linked CSVs (etl/build)"
```

---

### Task 5: End-to-end smoke test + Makefile target + .gitignore

**Files:**
- Create: `App/dhis2/tests/test_datasets_smoke.py`
- Modify: `App/dhis2/Makefile`
- Modify: `App/dhis2/.gitignore`

- [ ] **Step 1: Write the smoke test**

Create `App/dhis2/tests/test_datasets_smoke.py`:

```python
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
```

- [ ] **Step 2: Run it against the live instance**

Run: `cd App/dhis2 && python -m pytest tests/test_datasets_smoke.py -v`
Expected: PASS (1 passed, not skipped, since DHIS2 is up). If it skips, start DHIS2 (`docker compose up -d`) and re-run.

- [ ] **Step 3: Add the Makefile target**

In `App/dhis2/Makefile`, add `datasets` to `.PHONY` and this target:

```makefile
datasets:
	PYTHONPATH=. python -m etl.build
```

- [ ] **Step 4: Ignore generated outputs**

Append to `App/dhis2/.gitignore`:

```
data/
```

- [ ] **Step 5: Run the whole dhis2 suite + the target end-to-end**

Run: `cd App/dhis2 && python -m pytest -q && make datasets`
Expected: all tests pass (new + existing); `make datasets` prints the two "wrote …" lines.

- [ ] **Step 6: Commit**

```bash
git add App/dhis2/tests/test_datasets_smoke.py App/dhis2/Makefile App/dhis2/.gitignore
git commit -m "Add datasets smoke test + make datasets target + ignore data/ outputs"
```

---

## Self-Review

**Spec coverage (against 2026-06-07 spec):**
- §1.1 reports CSV, one row/report, symptoms 0/1 + timestamp → Tasks 3–4 (`reports.csv`). ✅
- §1.2 labelled water CSV via partner logic, linked by `station_id` → Tasks 1,2,4 + smoke linkage assertion. ✅
- §2 E4 import partner logic untouched → Task 2 (`importlib`, delegates verbatim). ✅
- §2 E5 simulated readings, clearly marked → Task 1 (docstring) + `.gitignore data/`. ✅
- §2 E6 two linked CSVs joined on `station_id` → Task 4 + smoke test. ✅
- Framing: label stays `at_risk`; optional `unsafe` alias column included (Task 4). ✅
- §6 testing: pure unit tests (1,2,3) + skip-aware integration (5). ✅
- **Deferred (correct):** SMS bridge → Plan 2; pushing readings into DHIS2 Water Quality → out of scope (§7).

**Placeholder scan:** none — every step has runnable code/commands. The `eWh8gc8ubdW` program UID and root-org-unit lookup are concrete (UID matches the live instance; verify in the prereq command).

**Type/name consistency:** `report_event_to_row(event, de_by_id, ou_by_id, symptom_names)` and `load_maps()`/`fetch_report_events()`/`write_csv()` signatures match across `reports.py`, `build.py`, and tests. `label_readings(readings, reports)` matches the partner's contract and `labeller.py`. Reading dicts carry `id`/`station_id`/`timestamp` consistently between `simulate.py`, `labeller.py`, and `build.py`. Symptom column naming (`name.lower().replace(" ", "_")`) is identical in `reports.py` and `build.py`'s header.
