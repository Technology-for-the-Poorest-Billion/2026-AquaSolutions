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
    stages = progs[0].get("programStages", [])
    if not stages:
        raise RuntimeError(f"DHIS2 program '{PROGRAM_NAME}' has no stages")
    stage_uid = stages[0]["id"]
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
    for required in ("Illness - Case Count", "Illness - Onset Date"):
        if required not in de:
            raise RuntimeError(f"DHIS2 data element not found: {required!r}")
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
