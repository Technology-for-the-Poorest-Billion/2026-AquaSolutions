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
