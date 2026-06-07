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
