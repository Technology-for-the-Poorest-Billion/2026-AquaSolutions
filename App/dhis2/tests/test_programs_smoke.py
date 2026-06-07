"""Integration smoke test for the event programs + role. Requires a running
DHIS2; skips when unreachable so unit tests still run without Docker.

Imports all committed metadata in dependency order (org units first, since the
programs reference org-unit UIDs and the levels), then verifies structure via
the Web API. Proves the whole config reproduces from the versioned JSON.
"""

from pathlib import Path

import pytest
import requests

from metadata import import_metadata as im

META = Path(__file__).resolve().parent.parent / "metadata"
FILES = ["org_units.json", "program_illness.json", "program_water.json", "users_roles.json"]


def _dhis2_up() -> bool:
    try:
        return requests.get(f"{im.base_url()}/api/system/info.json", auth=im.auth(), timeout=5).ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")


def _get(path, **params):
    r = requests.get(f"{im.base_url()}{path}", params=params, auth=im.auth(), timeout=30)
    r.raise_for_status()
    return r.json()


def _import_all():
    for fname in FILES:
        result = im.import_metadata(str(META / fname))
        assert result.get("status") in ("OK", "SUCCESS"), (fname, result)


def _program(name):
    progs = _get(
        "/api/programs.json",
        filter=f"name:eq:{name}",
        fields="id,programType,organisationUnits~size,"
               "programStages[programStageDataElements[dataElement[name,valueType]]]",
        paging="false",
    )["programs"]
    assert progs, f"program not found: {name}"
    return progs[0]


def _data_elements(program):
    return [
        de["dataElement"]
        for stage in program["programStages"]
        for de in stage["programStageDataElements"]
    ]


def test_import_is_clean():
    _import_all()


def test_org_unit_levels_present():
    _import_all()
    levels = _get("/api/organisationUnitLevels.json", fields="level", paging="false")
    assert len(levels["organisationUnitLevels"]) == 4


def test_illness_program_structure():
    _import_all()
    p = _program("Community Illness Reports")
    assert p["programType"] == "WITHOUT_REGISTRATION"
    assert p["organisationUnits"] >= 32
    names = [d["name"] for d in _data_elements(p)]
    assert any("Case Count" in n for n in names)
    assert any("Onset" in n for n in names)
    symptom_checkboxes = [
        d for d in _data_elements(p)
        if d["name"].startswith("Symptom: ") and d["valueType"] == "TRUE_ONLY"
    ]
    assert len(symptom_checkboxes) >= 18


def test_water_program_structure():
    _import_all()
    p = _program("Water Quality Summary")
    assert p["programType"] == "WITHOUT_REGISTRATION"
    assert p["organisationUnits"] >= 32
    assert len(_data_elements(p)) >= 8


def test_vhw_role_present():
    _import_all()
    roles = _get("/api/userRoles.json", filter="name:eq:Village Health Worker",
                 fields="id", paging="false")["userRoles"]
    assert roles
