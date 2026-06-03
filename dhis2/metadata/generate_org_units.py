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
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(payload['organisationUnits'])} org units to {OUT_PATH}")


if __name__ == "__main__":
    main()
