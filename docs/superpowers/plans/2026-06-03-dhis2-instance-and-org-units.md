# DHIS2 Instance + Org-Unit Tree Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up a local, empty, self-hosted DHIS2 instance and load the project's 4-neighbourhood / 32-borehole geography into it as a version-controlled organisation-unit tree, verified through the DHIS2 Web API.

**Architecture:** A new top-level `dhis2/` entity (separate from the frozen `App/backend` demo, per the design spec). `docker-compose.yml` brings up DHIS2 (`dhis2/core`) on PostGIS. A small, fully-tested Python generator turns copied seed data into DHIS2 organisation-unit metadata JSON; an import script POSTs it to the running instance; an API smoke test asserts the resulting hierarchy.

**Tech Stack:** Docker Compose, DHIS2 (`dhis2/core`), PostgreSQL+PostGIS, Python 3 (`requests`, `pytest`).

**Scope note:** This is Plan 1 of 4 from `docs/superpowers/specs/2026-06-03-dhis2-vhw-water-surveillance-design.md`. Plan 2 = event programs/data elements/roles; Plan 3 = Flask gateway + labelling job; Plan 4 = forked Capture App. This plan produces working, API-verifiable software on its own.

---

### Task 1: Scaffold the `dhis2/` project entity

**Files:**
- Create: `dhis2/README.md`
- Create: `dhis2/.gitignore`
- Create: `dhis2/requirements.txt`
- Create: `dhis2/tests/__init__.py`

- [ ] **Step 1: Create the directory skeleton and Python deps**

Create `dhis2/requirements.txt`:

```
requests==2.32.3
pytest==8.3.3
```

Create `dhis2/.gitignore`:

```
__pycache__/
*.pyc
.pytest_cache/
.venv/
dhis2-data/
```

Create empty `dhis2/tests/__init__.py` (no content).

- [ ] **Step 2: Write the README with pinned-version + provenance notes**

Create `dhis2/README.md`:

```markdown
# DHIS2 VHW + Water Surveillance (parallel track)

Greenfield entity, separate from the frozen `App/backend` Railway demo.
See `docs/superpowers/specs/2026-06-03-dhis2-vhw-water-surveillance-design.md`.

## Pinned versions
- DHIS2 image: `dhis2/core:<TAG>`  (set in docker-compose.yml; see Task 2)
- Forked Android Capture App upstream tag: _TBD in Plan 4_

## Provenance of copied data
- `metadata/seed_data.py` is COPIED from `App/backend/database.py`
  (SEED_NEIGHBORHOODS / SEED_STATIONS). The two projects are deliberately
  separate; this copy is intentional, not shared code.

## Local dev
    cd dhis2
    docker compose up -d            # boots DHIS2 (slow first run; see Task 2)
    python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
    make orgunits                   # generate + import org units
    pytest                          # unit + API smoke tests
```

- [ ] **Step 3: Commit**

```bash
git add dhis2/README.md dhis2/.gitignore dhis2/requirements.txt dhis2/tests/__init__.py
git commit -m "Scaffold dhis2/ parallel-track project entity"
```

---

### Task 2: Local DHIS2 instance via Docker Compose

**Files:**
- Create: `dhis2/docker-compose.yml`
- Create: `dhis2/config/dhis.conf`

**Why upstream-based:** DHIS2's multi-service compose (web + PostGIS + config) is intricate and version-specific. Start from the canonical upstream file and apply the exact edits below rather than hand-writing it.

- [ ] **Step 1: Confirm the current stable image tag**

Open https://hub.docker.com/r/dhis2/core/tags and pick the newest **stable** tag (a fixed version, not `-dev`/`-canary`/`latest`). Record it as `<TAG>` and write it into `dhis2/README.md` (replace the `<TAG>` placeholder from Task 1).

Expected: a concrete tag string, e.g. `41.3.0` (verify — do not assume).

- [ ] **Step 2: Fetch the canonical compose as a starting point**

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/dhis2/dhis2-core/master/docker-compose.yml -o dhis2/docker-compose.yml
```

Expected: `dhis2/docker-compose.yml` created (a `web` service + a `db` PostGIS service).

- [ ] **Step 3: Apply these exact edits to `dhis2/docker-compose.yml`**

1. Pin the web image: set it to `dhis2/core:<TAG>` from Step 1 (remove any `${DHIS2_IMAGE}` indirection / default to the pinned tag).
2. **Empty instance:** ensure there is **no** `DHIS2_DB_DUMP_URL` / demo-database seeding for the `db` service. We want an empty system, not the Sierra Leone demo. If the upstream file pulls a dump, delete that env var / init step.
3. Map the web port to the host: under the `web` service `ports:` ensure `- "8080:8080"`.
4. Persist DB data: ensure the `db` service has a named volume (e.g. `db-data:/var/lib/postgresql/data`) and that the volume is declared under top-level `volumes:`.
5. Mount our config: under `web` add `volumes: - ./config/dhis.conf:/opt/dhis2/dhis.conf:ro` (adjust the right-hand path to the `DHIS2_HOME` the image expects — check the upstream file's existing conf mount and match it).

- [ ] **Step 4: Write `dhis2/config/dhis.conf`**

Create `dhis2/config/dhis.conf` (match DB credentials to the `db` service in compose):

```properties
connection.dialect = org.hibernate.dialect.PostgreSQLDialect
connection.driver_class = org.postgresql.Driver
connection.url = jdbc:postgresql://db/dhis2
connection.username = dhis
connection.password = dhis
# 24+ char secret for at-rest field encryption; replace before any real use.
encryption.password = local-dev-only-change-me-please-32
server.base.url = http://localhost:8080
```

If the upstream compose already supplies these via environment variables, keep this file minimal and rely on those instead — do not duplicate conflicting config. The goal: web connects to `db`, instance reachable at `http://localhost:8080`.

- [ ] **Step 5: Boot and verify (first run is slow — Flyway migrations build the empty schema)**

Run:

```bash
cd dhis2 && docker compose up -d && cd ..
# DHIS2 takes several minutes on first boot. Poll until ready:
until curl -fsu admin:district http://localhost:8080/api/system/info.json >/dev/null 2>&1; do echo "waiting for DHIS2..."; sleep 15; done
curl -fsu admin:district http://localhost:8080/api/system/info.json | python -m json.tool | head -20
```

Expected: after a few minutes, JSON system info prints (version, etc.). Default superuser is `admin` / `district` on an empty instance.

- [ ] **Step 6: Commit**

```bash
git add dhis2/docker-compose.yml dhis2/config/dhis.conf dhis2/README.md
git commit -m "Add local empty DHIS2 docker-compose + dhis.conf"
```

---

### Task 3: Deterministic DHIS2 UID generator

DHIS2 object IDs ("UIDs") are exactly 11 chars: first char a letter `[A-Za-z]`, remaining 10 alphanumeric `[A-Za-z0-9]`. We generate them deterministically from a stable seed string so the metadata file is reproducible and parent references are stable across regenerations.

**Files:**
- Create: `dhis2/metadata/__init__.py`
- Create: `dhis2/metadata/uid.py`
- Test: `dhis2/tests/test_uid.py`

- [ ] **Step 1: Write the failing test**

Create `dhis2/tests/test_uid.py`:

```python
import re

from metadata.uid import dhis2_uid

UID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{10}$")


def test_uid_matches_dhis2_format():
    assert UID_RE.match(dhis2_uid("zimbabwe"))


def test_uid_is_deterministic():
    assert dhis2_uid("station-7") == dhis2_uid("station-7")


def test_distinct_seeds_give_distinct_uids():
    seeds = ["country", "district-harare", "nbh-1", "nbh-2", "station-1", "station-32"]
    uids = [dhis2_uid(s) for s in seeds]
    assert len(set(uids)) == len(seeds)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd dhis2 && pytest tests/test_uid.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'metadata.uid'`.

- [ ] **Step 3: Write the minimal implementation**

Create empty `dhis2/metadata/__init__.py` (no content).

Create `dhis2/metadata/uid.py`:

```python
"""Deterministic DHIS2 UID generation.

A DHIS2 UID is 11 chars: first is a letter, the rest are alphanumeric.
We derive it from a SHA-256 of the seed so the same seed always yields the
same UID — making the generated metadata reproducible and parent refs stable.
"""

from __future__ import annotations

import hashlib

_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ALNUM = _LETTERS + "0123456789"


def dhis2_uid(seed: str) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    first = _LETTERS[digest[0] % len(_LETTERS)]
    rest = "".join(_ALNUM[b % len(_ALNUM)] for b in digest[1:11])
    return first + rest
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd dhis2 && pytest tests/test_uid.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add dhis2/metadata/__init__.py dhis2/metadata/uid.py dhis2/tests/test_uid.py
git commit -m "Add deterministic DHIS2 UID generator"
```

---

### Task 4: Copy seed geography into the new project

**Files:**
- Create: `dhis2/metadata/seed_data.py`
- Test: `dhis2/tests/test_seed_data.py`

- [ ] **Step 1: Write the failing test**

Create `dhis2/tests/test_seed_data.py`:

```python
from metadata.seed_data import SEED_NEIGHBORHOODS, SEED_STATIONS


def test_neighborhood_count():
    assert len(SEED_NEIGHBORHOODS) == 4


def test_station_count():
    assert len(SEED_STATIONS) == 32


def test_every_station_references_a_real_neighborhood():
    nbh_ids = {nid for nid, _ in SEED_NEIGHBORHOODS}
    for station_id, name, lat, lon, nbh_id in SEED_STATIONS:
        assert nbh_id in nbh_ids, f"station {station_id} has unknown neighbourhood {nbh_id}"


def test_station_ids_unique():
    ids = [s[0] for s in SEED_STATIONS]
    assert len(set(ids)) == len(ids)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd dhis2 && pytest tests/test_seed_data.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'metadata.seed_data'`.

- [ ] **Step 3: Create the seed module (copied from App/backend/database.py)**

Create `dhis2/metadata/seed_data.py`:

```python
"""Geography seed COPIED from App/backend/database.py (SEED_NEIGHBORHOODS /
SEED_STATIONS). Deliberately duplicated: the DHIS2 track is a separate entity
from the frozen demo. If the demo's geography changes, re-sync this by hand.
"""

# (neighborhood_id, name)
SEED_NEIGHBORHOODS = [
    (1, "Central Harare"),
    (2, "Northern Suburbs"),
    (3, "Southern Areas"),
    (4, "Eastern Suburbs"),
]

# (station_id, name, lat, lon, neighborhood_id)
SEED_STATIONS = [
    (1,  "Avenues — central clinic",          -17.815, 31.050, 1),
    (2,  "Belvedere — community hall",        -17.840, 31.025, 1),
    (7,  "Milton Park — health post",         -17.832, 31.030, 1),
    (11, "Causeway — government complex",     -17.831, 31.048, 1),
    (12, "Kopje — civic hall",                -17.835, 31.038, 1),
    (13, "CBD — central market",              -17.828, 31.052, 1),
    (14, "Africa Unity Square — fountain",    -17.830, 31.054, 1),
    (15, "Workington — industrial water",     -17.840, 31.030, 1),
    (6,  "Newlands — shopping centre",        -17.810, 31.067, 2),
    (9,  "Mt Pleasant — north well",          -17.795, 31.045, 2),
    (16, "Avondale — north clinic",           -17.797, 31.038, 2),
    (17, "Belgravia — community well",        -17.800, 31.038, 2),
    (18, "Mt Pleasant Heights — school",      -17.785, 31.040, 2),
    (19, "Marlborough — clinic",              -17.795, 31.025, 2),
    (20, "Strathaven — water point",          -17.797, 31.045, 2),
    (21, "Pomona — north settlement",         -17.787, 31.060, 2),
    (4,  "Mbare — Musika market",             -17.860, 31.045, 3),
    (5,  "Hatfield — community borehole",     -17.852, 31.072, 3),
    (22, "Waterfalls — south clinic",         -17.870, 31.058, 3),
    (23, "Sunningdale — water point",         -17.875, 31.078, 3),
    (24, "Lichendale — primary school",       -17.875, 31.050, 3),
    (25, "Southerton — community well",       -17.865, 31.020, 3),
    (26, "Aspindale Park — water point",      -17.870, 31.025, 3),
    (27, "Prospect — health post",            -17.878, 31.015, 3),
    (3,  "Eastlea — primary school",          -17.825, 31.062, 4),
    (8,  "Hillside — water point",            -17.847, 31.058, 4),
    (10, "Greendale — east settlement",       -17.835, 31.082, 4),
    (28, "Highlands — east clinic",           -17.820, 31.075, 4),
    (29, "Athlone — primary school",          -17.825, 31.085, 4),
    (30, "Cranborne — water point",           -17.850, 31.075, 4),
    (31, "Donnybrook — community hall",       -17.855, 31.085, 4),
    (32, "Msasa — industrial water point",    -17.830, 31.090, 4),
]
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd dhis2 && pytest tests/test_seed_data.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add dhis2/metadata/seed_data.py dhis2/tests/test_seed_data.py
git commit -m "Copy neighbourhood/station seed geography into dhis2/"
```

---

### Task 5: Generate the org-unit metadata JSON

Builds a 4-level tree: Zimbabwe (L1) → Harare district (L2) → 4 neighbourhoods (L3) → 32 boreholes (L4, each with a GeoJSON Point). Boreholes carry their `station_id` in the `code` field so other systems can map to them.

**Files:**
- Create: `dhis2/metadata/generate_org_units.py`
- Test: `dhis2/tests/test_generate_org_units.py`

- [ ] **Step 1: Write the failing test**

Create `dhis2/tests/test_generate_org_units.py`:

```python
from metadata.generate_org_units import build_org_units

OPENING_DATE = "2020-01-01T00:00:00.000"


def _by_name(units, name):
    return next(u for u in units if u["name"] == name)


def test_total_unit_count():
    # 1 country + 1 district + 4 neighbourhoods + 32 boreholes
    units = build_org_units()["organisationUnits"]
    assert len(units) == 38


def test_levels_are_assigned():
    units = build_org_units()["organisationUnits"]
    levels = sorted({u["level"] for u in units})
    assert levels == [1, 2, 3, 4]


def test_country_has_no_parent():
    units = build_org_units()["organisationUnits"]
    assert "parent" not in _by_name(units, "Zimbabwe")


def test_neighbourhood_parent_is_district():
    units = build_org_units()["organisationUnits"]
    district = _by_name(units, "Harare")
    central = _by_name(units, "Central Harare")
    assert central["parent"]["id"] == district["id"]
    assert central["level"] == 3


def test_borehole_has_point_geometry_and_station_code():
    units = build_org_units()["organisationUnits"]
    borehole = _by_name(units, "Milton Park — health post")
    assert borehole["level"] == 4
    assert borehole["code"] == "STATION-7"
    assert borehole["geometry"]["type"] == "Point"
    # GeoJSON order is [longitude, latitude]
    assert borehole["geometry"]["coordinates"] == [31.030, -17.832]


def test_all_units_have_required_fields():
    units = build_org_units()["organisationUnits"]
    for u in units:
        assert len(u["id"]) == 11
        assert u["name"]
        assert len(u["shortName"]) <= 50
        assert u["openingDate"] == OPENING_DATE


def test_all_ids_unique():
    units = build_org_units()["organisationUnits"]
    ids = [u["id"] for u in units]
    assert len(set(ids)) == len(ids)
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd dhis2 && pytest tests/test_generate_org_units.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'metadata.generate_org_units'`.

- [ ] **Step 3: Write the implementation**

Create `dhis2/metadata/generate_org_units.py`:

```python
"""Generate DHIS2 organisation-unit metadata from the seed geography.

Hierarchy: Zimbabwe (L1) > Harare (L2, district) > neighbourhood (L3) >
borehole (L4). Boreholes carry station_id as `code` (STATION-<id>) and a
GeoJSON Point geometry. UIDs are deterministic so re-running is idempotent.

Run as a script to (re)write metadata/org_units.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from metadata.seed_data import SEED_NEIGHBORHOODS, SEED_STATIONS
from metadata.uid import dhis2_uid

OPENING_DATE = "2020-01-01T00:00:00.000"
COUNTRY_NAME = "Zimbabwe"
DISTRICT_NAME = "Harare"

OUT_PATH = Path(__file__).resolve().parent / "org_units.json"


def _short(name: str) -> str:
    return name[:50]


def build_org_units() -> dict:
    units: list[dict] = []

    country_id = dhis2_uid("country-zimbabwe")
    units.append({
        "id": country_id,
        "name": COUNTRY_NAME,
        "shortName": _short(COUNTRY_NAME),
        "openingDate": OPENING_DATE,
        "level": 1,
    })

    district_id = dhis2_uid("district-harare")
    units.append({
        "id": district_id,
        "name": DISTRICT_NAME,
        "shortName": _short(DISTRICT_NAME),
        "openingDate": OPENING_DATE,
        "level": 2,
        "parent": {"id": country_id},
    })

    nbh_ids: dict[int, str] = {}
    for nbh_id, name in SEED_NEIGHBORHOODS:
        uid = dhis2_uid(f"neighbourhood-{nbh_id}")
        nbh_ids[nbh_id] = uid
        units.append({
            "id": uid,
            "name": name,
            "shortName": _short(name),
            "openingDate": OPENING_DATE,
            "level": 3,
            "parent": {"id": district_id},
        })

    for station_id, name, lat, lon, nbh_id in SEED_STATIONS:
        uid = dhis2_uid(f"station-{station_id}")
        units.append({
            "id": uid,
            "name": name,
            "shortName": _short(name),
            "code": f"STATION-{station_id}",
            "openingDate": OPENING_DATE,
            "level": 4,
            "parent": {"id": nbh_ids[nbh_id]},
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
        })

    return {"organisationUnits": units}


def main() -> None:
    payload = build_org_units()
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {len(payload['organisationUnits'])} org units to {OUT_PATH}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `cd dhis2 && pytest tests/test_generate_org_units.py -v`
Expected: PASS (7 passed).

- [ ] **Step 5: Generate the JSON artifact and commit**

Run:

```bash
cd dhis2 && PYTHONPATH=. python -m metadata.generate_org_units && cd ..
```

Expected: `wrote 38 org units to .../dhis2/metadata/org_units.json`.

```bash
git add dhis2/metadata/generate_org_units.py dhis2/tests/test_generate_org_units.py dhis2/metadata/org_units.json
git commit -m "Generate DHIS2 org-unit tree from seed geography"
```

---

### Task 6: Import script + API smoke test

Imports `org_units.json` into the running instance and verifies the hierarchy through the Web API. The smoke test **skips** automatically if no DHIS2 is reachable, so unit tests still run in CI without Docker.

**Files:**
- Create: `dhis2/metadata/import_metadata.py`
- Create: `dhis2/Makefile`
- Test: `dhis2/tests/test_import_smoke.py`

- [ ] **Step 1: Write the import client**

Create `dhis2/metadata/import_metadata.py`:

```python
"""Import a DHIS2 metadata JSON file via POST /api/metadata.

Usage:
    PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json
Env (defaults shown):
    DHIS2_BASE_URL=http://localhost:8080
    DHIS2_USER=admin
    DHIS2_PASSWORD=district
"""

from __future__ import annotations

import json
import os
import sys

import requests


def base_url() -> str:
    return os.environ.get("DHIS2_BASE_URL", "http://localhost:8080").rstrip("/")


def auth() -> tuple[str, str]:
    return (
        os.environ.get("DHIS2_USER", "admin"),
        os.environ.get("DHIS2_PASSWORD", "district"),
    )


def import_metadata(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        payload = json.load(fh)
    resp = requests.post(
        f"{base_url()}/api/metadata",
        params={"importStrategy": "CREATE_AND_UPDATE", "atomicMode": "ALL"},
        json=payload,
        auth=auth(),
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m metadata.import_metadata <file.json>")
    result = import_metadata(sys.argv[1])
    status = result.get("status")
    stats = result.get("stats", {})
    print(f"import status={status} stats={stats}")
    if status not in ("OK", "SUCCESS"):
        raise SystemExit(f"metadata import failed: {json.dumps(result)[:2000]}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Write the API smoke test**

Create `dhis2/tests/test_import_smoke.py`:

```python
"""Integration smoke test. Requires a running DHIS2 (docker compose up).
Skips automatically when the instance is unreachable so unit tests still run.
"""

import pytest
import requests

from metadata import import_metadata as im
from metadata.generate_org_units import build_org_units


def _dhis2_up() -> bool:
    try:
        r = requests.get(f"{im.base_url()}/api/system/info.json", auth=im.auth(), timeout=5)
        return r.ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")


def _fetch_units():
    r = requests.get(
        f"{im.base_url()}/api/organisationUnits.json",
        params={"fields": "id,name,level,code", "paging": "false"},
        auth=im.auth(),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["organisationUnits"]


def test_import_then_hierarchy_present():
    result = im.import_metadata("metadata/org_units.json")
    assert result.get("status") in ("OK", "SUCCESS"), result

    units = _fetch_units()
    by_level = {}
    for u in units:
        by_level.setdefault(u["level"], []).append(u)

    assert len(by_level.get(1, [])) >= 1   # Zimbabwe
    assert len(by_level.get(2, [])) >= 1   # Harare
    assert len(by_level.get(3, [])) >= 4   # neighbourhoods
    assert len(by_level.get(4, [])) >= 32  # boreholes

    codes = {u.get("code") for u in by_level.get(4, [])}
    assert "STATION-7" in codes


def test_reimport_is_idempotent():
    # Deterministic UIDs => second import updates in place, no duplicates.
    im.import_metadata("metadata/org_units.json")
    expected = len(build_org_units()["organisationUnits"])
    units = _fetch_units()
    assert len([u for u in units if u["level"] in (1, 2, 3, 4)]) == expected
```

- [ ] **Step 3: Add a Makefile convenience target**

Create `dhis2/Makefile`:

```makefile
.PHONY: orgunits test

orgunits:
	PYTHONPATH=. python -m metadata.generate_org_units
	PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json

test:
	PYTHONPATH=. pytest -v
```

- [ ] **Step 4: Run the full suite against the live instance**

Ensure DHIS2 is up (`cd dhis2 && docker compose up -d`, wait per Task 2 Step 5), then run:

Run: `cd dhis2 && PYTHONPATH=. pytest -v`
Expected: all unit tests PASS; the two `test_import_smoke` tests PASS (not skipped) because DHIS2 is reachable. If DHIS2 is down they SKIP with reason "DHIS2 not reachable".

- [ ] **Step 5: Verify by eye in the DHIS2 UI (optional but recommended)**

Open http://localhost:8080 (login `admin`/`district`) → Maintenance app → Organisation unit → confirm the Zimbabwe → Harare → neighbourhood → borehole tree, and that a borehole shows a map location.

- [ ] **Step 6: Commit**

```bash
git add dhis2/metadata/import_metadata.py dhis2/tests/test_import_smoke.py dhis2/Makefile
git commit -m "Add metadata import script + DHIS2 API smoke test"
```

---

## Self-Review

**Spec coverage (against the 2026-06-03 design spec):**
- §4 org-unit hierarchy (borehole = leaf, GPS, station identity) → Tasks 4–6. ✅
- §4 config-as-code under `dhis2/metadata/` → Tasks 5–6 (`org_units.json`). ✅
- §2 D2 self-hosted DHIS2 (Docker) → Task 2. ✅
- §2 D8 new `dhis2/` dir in this repo → Task 1. ✅
- §6 project layout (`dhis2/`, `docker-compose.yml`, `metadata/`) → Tasks 1–6. ✅
- §8 metadata smoke test → Task 6. ✅
- **Deferred to later plans (intentional, not gaps):** the three event programs + roles (§4) → Plan 2; gateway + labelling (§5) → Plan 3; forked app (§7) → Plan 4.

**Placeholder scan:** The only `<...>` token is the DHIS2 image `<TAG>`, which Task 2 Step 1 resolves to a concrete value via Docker Hub — it is an explicit lookup action, not a hand-wave. The `dhis.conf` `encryption.password` is a real (clearly-marked dev-only) value, not a placeholder.

**Type/name consistency:** `dhis2_uid` (Task 3) used by `generate_org_units` (Task 5); `build_org_units()` returns `{"organisationUnits": [...]}` consumed identically by tests (Tasks 5–6); `import_metadata(path)` / `base_url()` / `auth()` defined in Task 6 Step 1 and used unchanged in Task 6 Step 2. Borehole `code` is `STATION-<id>` in both the generator and the smoke test. Consistent.
