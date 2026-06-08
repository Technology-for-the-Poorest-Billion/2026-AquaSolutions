# SMS → DHIS2 Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When an SMS illness-report conversation completes in the Flask app, also create the equivalent **DHIS2 Community Illness Reports event**, so texted reports show up in the DHIS2 demo alongside Capture-app reports.

**Architecture:** A new self-contained module `App/backend/dhis2_bridge.py` (stdlib `urllib` only — no new prod dependency) resolves DHIS2 program/stage/data-element/org-unit references at runtime and POSTs an event to `/api/tracker`. The Flask `/sms` handler gains **one guarded call** at the `complete` transition, behind a `DHIS2_BRIDGE_ENABLED` flag and wrapped so a bridge failure never breaks the SMS reply. The labelling logic is untouched (partner-owned).

**Tech Stack:** Python 3 stdlib (`urllib`, `json`, `base64`), Flask (existing `/sms`), pytest (`requests` available in dev for tests).

**Scope:** Plan 2 of 2 from `App/docs/superpowers/specs/2026-06-07-reports-csv-labelling-sms-design.md` (§5). Plan 1 (datasets) is merged.

**Prerequisites:** DHIS2 running at `http://localhost:8080` (`admin`/`district`) with the *Community Illness Reports* program + `STATION-<n>` borehole org units. Flask tests run from `App/backend/` with its existing conftest (SQLite). Twilio signature validation is off in tests (`TWILIO_VALIDATE_SIGNATURES=false`).

## Key facts from the existing code
- `/sms` in `App/backend/app.py` is a stateful dialog over `illness_reports.dialog_state`: `NULL → awaiting_case_count → awaiting_symptoms → awaiting_onset → complete`. Completion is the `awaiting_onset` branch after `SET ... dialog_state = 'complete'`, just before `reply.message("Report complete...")`.
- At completion the report row has: `station_id`, `case_count` (int), `symptoms` (JSON list of keys like `["diarrhoea","fever"]`), `onset_date` (ISO string).
- SMS symptom keys are the original four: `diarrhoea, vomiting, fever, dehydration`. DHIS2 symptom data elements are named `Symptom: Diarrhoea` etc. → DHIS2 name = `"Symptom: " + key.capitalize()`.
- Station identity is shared: SMS `station_id` N ↔ DHIS2 org unit `code = STATION-N`.

## File Structure

| File | Responsibility |
|------|----------------|
| `App/backend/dhis2_bridge.py` | config from env + pure `build_event_payload` + runtime ref resolution + `create_event_from_report` (POST) |
| `App/backend/app.py` | one guarded bridge call at the `/sms` complete transition + `import dhis2_bridge` |
| `App/backend/.env.example` | add `DHIS2_BRIDGE_ENABLED`, `DHIS2_BASE_URL`, `DHIS2_USER`, `DHIS2_PASSWORD` |
| `App/backend/tests/test_dhis2_bridge.py` | unit (pure builder) + integration (real event, skips if DHIS2 down) + hook (flag on, bridge monkeypatched) |
| `App/backend/README.md` (or a docs note) | how to run the SMS demo (flag + ngrok + Twilio) |

---

### Task 1: Bridge config + pure event-payload builder

**Files:**
- Create: `App/backend/dhis2_bridge.py`
- Test: `App/backend/tests/test_dhis2_bridge.py`

- [ ] **Step 1: Write the failing test**

Create `App/backend/tests/test_dhis2_bridge.py`:

```python
import dhis2_bridge


def test_enabled_reads_env(monkeypatch):
    monkeypatch.delenv("DHIS2_BRIDGE_ENABLED", raising=False)
    assert dhis2_bridge.enabled() is False
    monkeypatch.setenv("DHIS2_BRIDGE_ENABLED", "true")
    assert dhis2_bridge.enabled() is True


def test_build_event_payload_core():
    payload = dhis2_bridge.build_event_payload(
        program_uid="prog", stage_uid="stg", org_unit_uid="ou",
        case_de_uid="deCASE", onset_de_uid="deONSET",
        symptom_de_by_key={"diarrhoea": "deDIAR", "fever": "deFEVER"},
        case_count=5, symptoms=["diarrhoea", "fever"],
        onset_iso="2026-06-03", occurred_iso="2026-06-05T10:00:00+00:00",
    )
    ev = payload["events"][0]
    assert ev["program"] == "prog" and ev["programStage"] == "stg" and ev["orgUnit"] == "ou"
    assert ev["occurredAt"] == "2026-06-05T10:00:00+00:00"
    assert ev["status"] == "COMPLETED"
    dv = {d["dataElement"]: d["value"] for d in ev["dataValues"]}
    assert dv["deCASE"] == "5"
    assert dv["deONSET"] == "2026-06-03"
    assert dv["deDIAR"] == "true"
    assert dv["deFEVER"] == "true"


def test_build_event_payload_omits_unmapped_or_absent_symptoms():
    payload = dhis2_bridge.build_event_payload(
        program_uid="p", stage_uid="s", org_unit_uid="o",
        case_de_uid="c", onset_de_uid="n",
        symptom_de_by_key={"diarrhoea": "deDIAR", "vomiting": None},
        case_count=1, symptoms=["diarrhoea", "vomiting"],
        onset_iso="2026-06-01", occurred_iso="2026-06-01T00:00:00+00:00",
    )
    dv = {d["dataElement"]: d["value"] for d in payload["events"][0]["dataValues"]}
    assert dv.get("deDIAR") == "true"
    assert "vomiting" not in dv and None not in dv  # unmapped symptom dropped
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'dhis2_bridge'`.

- [ ] **Step 3: Implement (config + pure builder)**

Create `App/backend/dhis2_bridge.py`:

```python
"""SMS -> DHIS2 bridge: turn a completed Flask SMS report into a DHIS2
Community Illness Reports event. Stdlib-only (urllib) so it adds no production
dependency. Does NOT run labelling (partner-owned).

Disabled unless DHIS2_BRIDGE_ENABLED is truthy, so existing behaviour is
unchanged by default.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request


def enabled() -> bool:
    return os.environ.get("DHIS2_BRIDGE_ENABLED", "").strip().lower() in ("1", "true", "yes")


def base_url() -> str:
    return os.environ.get("DHIS2_BASE_URL", "http://localhost:8080").rstrip("/")


def _auth_header() -> str:
    user = os.environ.get("DHIS2_USER", "admin")
    pw = os.environ.get("DHIS2_PASSWORD", "district")
    return "Basic " + base64.b64encode(f"{user}:{pw}".encode()).decode()


def build_event_payload(*, program_uid, stage_uid, org_unit_uid, case_de_uid, onset_de_uid,
                        symptom_de_by_key, case_count, symptoms, onset_iso, occurred_iso):
    """Pure: assemble the /api/tracker event payload. A symptom is included only
    if it maps to a real data-element UID."""
    data_values = [
        {"dataElement": case_de_uid, "value": str(case_count)},
        {"dataElement": onset_de_uid, "value": onset_iso},
    ]
    for key in symptoms:
        de_uid = symptom_de_by_key.get(key)
        if de_uid:
            data_values.append({"dataElement": de_uid, "value": "true"})
    return {"events": [{
        "program": program_uid,
        "programStage": stage_uid,
        "orgUnit": org_unit_uid,
        "occurredAt": occurred_iso,
        "status": "COMPLETED",
        "dataValues": data_values,
    }]}
```

- [ ] **Step 4: Run it — expect pass**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py -q`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add App/backend/dhis2_bridge.py App/backend/tests/test_dhis2_bridge.py
git commit -m "Add SMS->DHIS2 bridge config + pure event-payload builder"
```

---

### Task 2: Runtime ref resolution + create_event_from_report (POST)

**Files:**
- Modify: `App/backend/dhis2_bridge.py`
- Test: `App/backend/tests/test_dhis2_bridge.py`

- [ ] **Step 1: Add the integration test (skips if DHIS2 down)**

Append to `App/backend/tests/test_dhis2_bridge.py`:

```python
import urllib.request as _u
import urllib.error as _ue

import dhis2_bridge as _b


def _dhis2_up():
    try:
        req = _u.Request(_b.base_url() + "/api/system/info.json")
        req.add_header("Authorization", _b._auth_header())
        with _u.urlopen(req, timeout=5) as r:
            return r.status == 200
    except (_ue.URLError, OSError):
        return False


import pytest

dhis2 = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")


@dhis2
def test_create_event_round_trip():
    # station 1 == DHIS2 org unit code STATION-1 (Avenues — central clinic)
    event_id = dhis2_bridge.create_event_from_report(
        station_id=1, case_count=3, symptoms=["diarrhoea", "vomiting"], onset="2026-06-03",
    )
    assert event_id, "expected a created event id"
    try:
        # verify it exists and carries our case count
        got = _b._get(f"/api/tracker/events/{event_id}.json?fields=event,dataValues[dataElement,value]")
        assert got["event"] == event_id
        assert any(d["value"] == "3" for d in got["dataValues"])
    finally:
        # clean up the test event so it doesn't pollute the demo data
        _b._post("/api/tracker?async=false&importStrategy=DELETE",
                 {"events": [{"event": event_id}]})
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py::test_create_event_round_trip -q`
Expected: FAIL — `AttributeError: module 'dhis2_bridge' has no attribute 'create_event_from_report'` (or `_get`). (If DHIS2 is down it SKIPS — start it: `cd ../dhis2 && docker compose up -d`.)

- [ ] **Step 3: Implement resolution + POST**

Append to `App/backend/dhis2_bridge.py`:

```python
import urllib.error
from datetime import datetime, timezone

PROGRAM_NAME = "Community Illness Reports"
_REFS = None  # cached per process


def _get(path):
    req = urllib.request.Request(base_url() + path)
    req.add_header("Authorization", _auth_header())
    req.add_header("Accept", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _post(path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(base_url() + path, data=body, method="POST")
    req.add_header("Authorization", _auth_header())
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"DHIS2 POST {path} failed: {e.code} {e.read().decode()[:300]}")


def _resolve_refs(force=False):
    """Resolve + cache program/stage UIDs and a data-element name->uid map."""
    global _REFS
    if _REFS and not force:
        return _REFS
    progs = _get(
        "/api/programs.json?filter=name:eq:Community%20Illness%20Reports"
        "&fields=id,programStages[id]&paging=false"
    )["programs"]
    if not progs:
        raise RuntimeError(f"DHIS2 program not found: {PROGRAM_NAME}")
    stage_uid = progs[0]["programStages"][0]["id"]
    stage = _get(
        f"/api/programStages/{stage_uid}.json"
        "?fields=programStageDataElements[dataElement[id,name]]"
    )
    de_by_name = {p["dataElement"]["name"]: p["dataElement"]["id"]
                  for p in stage["programStageDataElements"]}
    _REFS = {"program": progs[0]["id"], "stage": stage_uid, "de_by_name": de_by_name}
    return _REFS


def _org_unit_uid(station_id):
    ous = _get(
        f"/api/organisationUnits.json?filter=code:eq:STATION-{station_id}"
        "&fields=id&paging=false"
    )["organisationUnits"]
    if not ous:
        raise RuntimeError(f"no DHIS2 org unit with code STATION-{station_id}")
    return ous[0]["id"]


def create_event_from_report(station_id, case_count, symptoms, onset):
    """Create a DHIS2 illness-report event from a completed SMS report.
    `onset` is an ISO date string. Returns the created event UID."""
    refs = _resolve_refs()
    de = refs["de_by_name"]
    symptom_de_by_key = {k: de.get(f"Symptom: {k.capitalize()}") for k in symptoms}
    payload = build_event_payload(
        program_uid=refs["program"], stage_uid=refs["stage"],
        org_unit_uid=_org_unit_uid(station_id),
        case_de_uid=de["Illness - Case Count"], onset_de_uid=de["Illness - Onset Date"],
        symptom_de_by_key=symptom_de_by_key,
        case_count=case_count, symptoms=symptoms,
        onset_iso=str(onset), occurred_iso=datetime.now(timezone.utc).isoformat(),
    )
    resp = _post("/api/tracker?async=false&importStrategy=CREATE", payload)
    if resp.get("status") not in ("OK", "SUCCESS"):
        raise RuntimeError(f"DHIS2 event import not OK: {json.dumps(resp)[:300]}")
    reports = (resp.get("bundleReport", {}).get("typeReportMap", {})
               .get("EVENT", {}).get("objectReports", []))
    return reports[0]["uid"] if reports else None
```

- [ ] **Step 4: Run it — expect pass (against the live instance)**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py -q`
Expected: PASS (4 passed — the round-trip runs since DHIS2 is up). If the import response shape differs and `event_id` is None, inspect `resp` (print it) and adjust the `bundleReport` path; do NOT weaken the assertion.

- [ ] **Step 5: Commit**

```bash
git add App/backend/dhis2_bridge.py App/backend/tests/test_dhis2_bridge.py
git commit -m "Add DHIS2 ref resolution + create_event_from_report (urllib POST)"
```

---

### Task 3: Hook the bridge into the /sms complete transition

**Files:**
- Modify: `App/backend/app.py` (import + the `awaiting_onset` complete branch)
- Test: `App/backend/tests/test_dhis2_bridge.py`

- [ ] **Step 1: Add the hook test (flag on, bridge monkeypatched)**

Append to `App/backend/tests/test_dhis2_bridge.py` (uses the existing `client` fixture from conftest):

```python
import json as _json


def test_sms_completion_calls_bridge(client, monkeypatch):
    calls = []
    monkeypatch.setattr(dhis2_bridge, "enabled", lambda: True)
    monkeypatch.setattr(dhis2_bridge, "create_event_from_report",
                        lambda **kw: calls.append(kw) or "evtTEST")

    def sms(body):
        return client.post("/sms", data={"From": "+15550001111", "Body": body})

    sms("1")          # station -> awaiting_case_count
    sms("5")          # case count -> awaiting_symptoms
    sms("1,3")        # diarrhoea, fever -> awaiting_onset
    r = sms("today")  # onset -> complete (bridge fires)
    assert b"Report complete" in r.data

    assert len(calls) == 1
    kw = calls[0]
    assert kw["station_id"] == 1
    assert kw["case_count"] == 5
    assert set(kw["symptoms"]) == {"diarrhoea", "fever"}
    assert kw["onset"]  # ISO onset string present


def test_sms_completion_no_bridge_when_disabled(client, monkeypatch):
    calls = []
    monkeypatch.setattr(dhis2_bridge, "enabled", lambda: False)
    monkeypatch.setattr(dhis2_bridge, "create_event_from_report",
                        lambda **kw: calls.append(kw))

    def sms(body):
        return client.post("/sms", data={"From": "+15550002222", "Body": body})

    sms("1"); sms("5"); sms("1,3"); sms("today")
    assert calls == []  # disabled -> bridge never called
```

- [ ] **Step 2: Run it — expect failure**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py::test_sms_completion_calls_bridge -q`
Expected: FAIL — `calls` is empty because the hook doesn't exist yet (or `dhis2_bridge` not imported in app.py).

- [ ] **Step 3: Add the import to `App/backend/app.py`**

In the import block near the other local imports (e.g. just after `from labels import label_readings_for_report`), add:

```python
import dhis2_bridge
```

- [ ] **Step 4: Add the guarded hook in the `awaiting_onset` complete branch**

In `App/backend/app.py`, find (in the `if state == "awaiting_onset":` branch):

```python
                reply.message("Report complete. Stay safe. Reply STOP to opt out.")
                return str(reply)
```

Replace with:

```python
                reply.message("Report complete. Stay safe. Reply STOP to opt out.")
                if dhis2_bridge.enabled():
                    rpt = conn.execute(
                        text("SELECT station_id, case_count, symptoms, onset_date "
                             "FROM illness_reports WHERE report_id = :rid"),
                        {"rid": report_id},
                    ).mappings().first()
                    try:
                        dhis2_bridge.create_event_from_report(
                            station_id=rpt["station_id"],
                            case_count=rpt["case_count"],
                            symptoms=json.loads(rpt["symptoms"] or "[]"),
                            onset=rpt["onset_date"],
                        )
                    except Exception as exc:  # bridge must never break the SMS reply
                        app.logger.warning("DHIS2 bridge failed for report %s: %s", report_id, exc)
                return str(reply)
```

(There is exactly one occurrence of that two-line block — it's the SMS onset-completion path. `json` and `text` are already imported in app.py.)

- [ ] **Step 5: Run the new tests + the existing SMS suite (no regressions)**

Run: `cd App/backend && python -m pytest tests/test_dhis2_bridge.py tests/test_sms_dialog.py -q`
Expected: PASS — the two hook tests pass, and all existing `test_sms_dialog.py` tests still pass (they run with the flag off by default, so behaviour is unchanged).

- [ ] **Step 6: Commit**

```bash
git add App/backend/app.py App/backend/tests/test_dhis2_bridge.py
git commit -m "Hook SMS completion to the DHIS2 bridge (guarded by DHIS2_BRIDGE_ENABLED)"
```

---

### Task 4: Config + demo run docs

**Files:**
- Modify: `App/backend/.env.example`
- Modify: `App/backend/README.md` (create if absent)

- [ ] **Step 1: Add bridge config to `.env.example`**

Append to `App/backend/.env.example`:

```
# --- SMS -> DHIS2 bridge (optional) ---
# When true, a completed SMS report also creates a DHIS2 event.
DHIS2_BRIDGE_ENABLED=false
# DHIS2 instance the bridge posts events to.
DHIS2_BASE_URL=http://localhost:8080
DHIS2_USER=admin
DHIS2_PASSWORD=district
```

- [ ] **Step 2: Document the SMS demo flow**

Append to `App/backend/README.md` (create the file with this content if it doesn't exist):

```markdown
## SMS → DHIS2 demo

A completed SMS illness report can also be pushed into the DHIS2 demo as an event.

1. Start DHIS2 locally: `cd ../dhis2 && docker compose up -d` (wait for it).
2. In `App/backend/.env` set `DHIS2_BRIDGE_ENABLED=true` (and `DHIS2_BASE_URL`/creds if not the defaults).
3. Run Flask and expose it to Twilio: `ngrok http 5000`, set the Twilio number's
   SMS webhook to `<ngrok-url>/sms`.
4. Text the Twilio number a station number (e.g. `1`), then follow the prompts
   (how many sick → symptoms `1,3` → onset `today`). On "Report complete" the
   bridge creates a DHIS2 event at that borehole; it appears in the DHIS2
   dashboard/line list after the next analytics run.

The bridge never runs labelling (that is the partner's logic) and never blocks
the SMS reply — if DHIS2 is unreachable, the text conversation still completes
and a warning is logged.
```

- [ ] **Step 3: Commit**

```bash
git add App/backend/.env.example App/backend/README.md
git commit -m "Document SMS->DHIS2 bridge config + demo run"
```

---

## Self-Review

**Spec coverage (against 2026-06-07 spec §5):**
- New module `dhis2_bridge.py` with `create_event_from_report(station_id, case_count, symptoms, onset)` → Tasks 1–2. ✅
- Resolve borehole by `STATION-<id>`, build event (case count, onset, symptom checkboxes), POST `/api/tracker` → Task 2. ✅
- UIDs resolved by name/code, not hardcoded → Task 2 (`_resolve_refs`, `_org_unit_uid`). ✅
- Guarded hook in `/sms` behind `DHIS2_BRIDGE_ENABLED`, additive, no labelling → Task 3. ✅
- Symptom mapping (4 SMS keys → `Symptom: <Cap>`; others absent) → Task 2 + builder. ✅
- Env config + demo path (ngrok/Twilio) → Task 4. ✅
- Testing: pure unit (Task 1), skip-aware integration (Task 2), flag-on/off hook tests + existing-suite regression (Task 3). ✅

**Placeholder scan:** none — all steps have runnable code/commands. The `bundleReport` extraction path is concrete; Task 2 Step 4 says to inspect+adjust only if the live response shape differs (not a hand-wave).

**Type/name consistency:** `build_event_payload(**kwargs)` keyword names match between Task 1's definition, its tests, and `create_event_from_report` in Task 2. `enabled()`, `base_url()`, `_auth_header()`, `_get()`, `_post()`, `_resolve_refs()`, `_org_unit_uid()`, `create_event_from_report()` are defined once and referenced consistently in tests and the app.py hook. The hook passes `station_id/case_count/symptoms/onset` exactly as `create_event_from_report` and the monkeypatched test expect.
