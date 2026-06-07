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

    ou = ou_by_id.get(event["orgUnit"])
    if ou is None:
        return None  # event at an org unit not in the committed metadata; skip it
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
    """Fetch all illness-report events from DHIS2 (requires a running instance).

    Uses ouMode=ALL because DHIS2 2.42 tracker events API does not honour
    ouMode=DESCENDANTS from a root node when the program is registered only on
    leaf org units.  ouMode=ALL returns events across the full hierarchy for
    superusers, which is the correct behaviour for this ETL.
    """
    r = requests.get(
        f"{im.base_url()}/api/tracker/events.json",
        params={"program": program_uid, "ouMode": "ALL",
                "fields": "event,occurredAt,orgUnit,dataValues[dataElement,value]",
                "pageSize": 10000, "skipPaging": "true"},
        auth=im.auth(), timeout=60,
    )
    r.raise_for_status()
    return r.json().get("events", [])


def write_csv(rows, fieldnames, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
