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
