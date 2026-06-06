# DHIS2 Event Programs (Illness + Water) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure two DHIS2 event programs — *Community Illness Report* (VHW-entered via the Capture App) and *Water Quality Summary* (gateway-pushed) — plus a VHW user role, captured as version-controlled metadata under `App/dhis2/metadata/` and verified by an import smoke test against a live instance.

**Architecture:** Build each program in the DHIS2 Maintenance app per an exact field spec, then export it (with all its dependencies) via the metadata dependency-export API to a committed JSON file. Reproducibility is proven by importing those files (after `org_units.json`) into the running instance and asserting structure through the Web API. This mirrors Plan 1's config-as-code + import-smoke-test discipline, but for the harder-to-hand-author program objects we author in the UI and export rather than write JSON by hand.

**Tech Stack:** DHIS2 2.42 (Maintenance app + Web API), `curl`, Python 3 (`requests`, `pytest`), reusing `App/dhis2/metadata/import_metadata.py` from Plan 1.

## Scope

**In scope:** *Community Illness Report* event program (option set + data elements + program + org-unit assignment + sharing); *Water Quality Summary* event program (data elements + program + assignment + sharing); a VHW user role; an import smoke test + Makefile target.

**Explicitly DEFERRED (do NOT build — see spec D14/D15):**
- The **label program** and any labelling logic — owned by a project partner.
- The **Risk/Decision** output element and the server-side XGBoost step — ML is paused.

**Prerequisites:** Plan 1 merged; DHIS2 running at `http://localhost:8080` (`admin`/`district`) with `org_units.json` imported (38 org units). Verify before starting:
`curl -fsu admin:district http://localhost:8080/api/organisationUnits.json?paging=false | python3 -c "import sys,json;print(len(json.load(sys.stdin)['organisationUnits']),'org units')"` → expect `38 org units`.

## File Structure

| File | Responsibility |
|------|----------------|
| `App/dhis2/metadata/program_illness.json` | Exported *Community Illness Report* program + its stage, data elements, Symptoms option set (created in Task 1) |
| `App/dhis2/metadata/program_water.json` | Exported *Water Quality Summary* program + its stage and data elements (Task 2) |
| `App/dhis2/metadata/users_roles.json` | Exported VHW user role (Task 3) |
| `App/dhis2/tests/test_programs_smoke.py` | Import-and-verify smoke test (Task 4) |
| `App/dhis2/Makefile` | Add a `metadata` target importing all metadata files in order (Task 4) |

**Convention note:** Programs are created in the UI, so DHIS2 assigns their UIDs (unlike Plan 1's deterministic org-unit UIDs). That is fine — the exported files freeze those UIDs, and the org-unit references inside them point at Plan 1's deterministic UIDs, so a fresh import (org units first, then programs) stays valid.

---

### Task 1: Community Illness Report event program

Mirrors the existing SMS dialog grain: case count + symptoms + onset date, captured at a borehole org unit.

**Files:**
- Create (by export): `App/dhis2/metadata/program_illness.json`

- [ ] **Step 1: Create the Symptoms option set**

In the Maintenance app (`http://localhost:8080`, login `admin`/`district`) → **Option set** → **New**:
- Name: `Symptoms`
- Code: `SYMPTOMS`
- Value type: `Text`
- Add four options (Name / Code), in this order:
  1. `Diarrhoea` / `diarrhoea`
  2. `Vomiting` / `vomiting`
  3. `Fever` / `fever`
  4. `Dehydration` / `dehydration`

Save.

- [ ] **Step 2: Create the three data elements**

Maintenance app → **Data element** → **New**, once per element. For ALL three set **Domain type = Tracker** and **Aggregation type = None**:

1. Name `Illness — case count`, Short name `Case count`, Value type **Positive Integer**.
2. Name `Illness — symptoms`, Short name `Symptoms`, Value type **Multi-text**, Option set **Symptoms**.
   - *Fallback if your DHIS2 build lacks the `Multi-text` value type:* set Value type **Text** with Option set **Symptoms** (single-select). Note which you used in the commit message; the smoke test in Task 4 accepts either.
3. Name `Illness — onset date`, Short name `Onset date`, Value type **Date**.

- [ ] **Step 3: Create the event program**

Maintenance app → **Program** → **New** → **Event program**:
- Name: `Community Illness Report`
- Short name: `Illness Report`
- Program type: **Event program** (without registration)
- Category combination: `None` (i.e. the default)

On the **Program stage** (a single stage is created for event programs), add the three data elements in this order, each marked **Compulsory**:
1. `Illness — case count`
2. `Illness — symptoms`
3. `Illness — onset date`

- [ ] **Step 4: Assign the program to the borehole org units**

In the program's **Access → Organisation units** (or "Organisation units" tab), select **all 32 boreholes** (the level-4 units under each neighbourhood). Tip: expand `Zimbabwe → Harare`, then for each of the 4 neighbourhoods tick its child boreholes (use "select sub-units" if offered). Save.

- [ ] **Step 5: Set sharing so it can be captured and viewed**

Open the program's **Sharing settings**:
- Public access: **Metadata: can view**, **Data: can capture and view** (so any logged-in user — including the demo VHW — can enter reports during the demo).

Save.

- [ ] **Step 6: Export the program with dependencies**

Find the program UID, then export it and its dependencies to the metadata file:

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
UID=$(curl -fsu admin:district "http://localhost:8080/api/programs.json?filter=name:eq:Community%20Illness%20Report&fields=id" | python3 -c "import sys,json;print(json.load(sys.stdin)['programs'][0]['id'])")
echo "illness program UID=$UID"
curl -fsu admin:district "http://localhost:8080/api/programs/$UID/metadata.json" -o App/dhis2/metadata/program_illness.json
python3 -c "import json;d=json.load(open('App/dhis2/metadata/program_illness.json'));print('top-level keys:',sorted(d));print('programs:',len(d.get('programs',[])),'dataElements:',len(d.get('dataElements',[])),'optionSets:',len(d.get('optionSets',[])))"
```
Expected: a JSON file containing at least `programs` (1), `programStages`, `dataElements` (>=3), `optionSets` (>=1 Symptoms), `options` (>=4).

- [ ] **Step 7: Commit**

```bash
git add App/dhis2/metadata/program_illness.json
git commit -m "Add Community Illness Report event program (exported metadata)"
```

---

### Task 2: Water Quality Summary event program

Gateway-pushed, one event per (borehole, day). Never hand-entered, so no option sets — just numeric/text data elements.

**Files:**
- Create (by export): `App/dhis2/metadata/program_water.json`

- [ ] **Step 1: Create the data elements**

Maintenance app → **Data element** → **New**, once per element. For ALL set **Domain type = Tracker** and **Aggregation type = Average** (except `reading count` → **Sum**, and `provenance` → **None**):

| Name | Short name | Value type |
|------|-----------|-----------|
| `Water — turbidity mean (NTU)` | `Turbidity mean` | Number |
| `Water — turbidity peak (NTU)` | `Turbidity peak` | Number |
| `Water — temperature mean (°C)` | `Temp mean` | Number |
| `Water — rainfall total (mm)` | `Rainfall total` | Number |
| `Water — pH mean` | `pH mean` | Number |
| `Water — chlorine mean (mg/L)` | `Chlorine mean` | Number |
| `Water — reading count` | `Reading count` | Positive Integer |
| `Water — provenance` | `Provenance` | Text |

- [ ] **Step 2: Create the event program**

Maintenance app → **Program** → **New** → **Event program**:
- Name: `Water Quality Summary`
- Short name: `Water Summary`
- Program type: **Event program** (without registration)
- Category combination: `None`

On the program stage, add all eight data elements (order: turbidity mean, turbidity peak, temperature mean, rainfall total, pH mean, chlorine mean, reading count, provenance). Leave them **not compulsory** (sensors may omit fields).

- [ ] **Step 3: Assign to the same 32 boreholes** (as Task 1 Step 4). Save.

- [ ] **Step 4: Set sharing**

Sharing settings → Public access: **Metadata: can view**, **Data: can capture and view** (the gateway writes via the admin/service account; viewers see it on dashboards). Save.

- [ ] **Step 5: Export with dependencies**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
UID=$(curl -fsu admin:district "http://localhost:8080/api/programs.json?filter=name:eq:Water%20Quality%20Summary&fields=id" | python3 -c "import sys,json;print(json.load(sys.stdin)['programs'][0]['id'])")
echo "water program UID=$UID"
curl -fsu admin:district "http://localhost:8080/api/programs/$UID/metadata.json" -o App/dhis2/metadata/program_water.json
python3 -c "import json;d=json.load(open('App/dhis2/metadata/program_water.json'));print('programs:',len(d.get('programs',[])),'dataElements:',len(d.get('dataElements',[])))"
```
Expected: `programs: 1`, `dataElements: 8` (or more if shared defaults are pulled in).

- [ ] **Step 6: Commit**

```bash
git add App/dhis2/metadata/program_water.json
git commit -m "Add Water Quality Summary event program (exported metadata)"
```

---

### Task 3: VHW user role

A role that can capture the illness program in the Capture App. (A demo *user* is created manually with a password kept OUT of git; only the role metadata is committed.)

**Files:**
- Create (by export): `App/dhis2/metadata/users_roles.json`

- [ ] **Step 1: Create the user role**

Users app (`http://localhost:8080` → apps → **Users**) → **User roles** → **New**:
- Name: `Village Health Worker`
- Description: `VHW — captures community illness reports on the Capture App`
- Add authorities: search for and enable at minimum: **"See Event Analytics"** is NOT needed; enable **data capture**-relevant authorities — specifically tick the metadata/data authorities that let the role open and submit tracker/event data (e.g. the Tracker capture authorities). Also tick the *Community Illness Report* program under the role's program access if the role editor exposes it.
  - If unsure which authorities, the minimal reliable set for event capture is: `Tracker Capture app` access plus the program's data sharing (set in Task 1 Step 5). Public data-capture sharing already lets any logged-in user capture, so the role can stay lightweight.

Save.

- [ ] **Step 2: (Manual, NOT committed) create a demo VHW user**

Users app → **Users** → **New**: username `vhw.demo`, assign role **Village Health Worker**, set its **data capture org units** to a handful of boreholes (e.g. all 8 in Central Harare), set a demo password. **Do not commit this password.** Record it in your own notes / a local `.env`, not in git. (For a pure-laptop demo you may instead just log in as `admin`; the dedicated user is for a more realistic "VHW logs in" moment.)

- [ ] **Step 3: Export the role only**

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
UID=$(curl -fsu admin:district "http://localhost:8080/api/userRoles.json?filter=name:eq:Village%20Health%20Worker&fields=id" | python3 -c "import sys,json;print(json.load(sys.stdin)['userRoles'][0]['id'])")
curl -fsu admin:district "http://localhost:8080/api/userRoles/$UID.json?fields=:owner" | python3 -c "import sys,json; r=json.load(sys.stdin); json.dump({'userRoles':[r]}, open('App/dhis2/metadata/users_roles.json','w'), indent=2)"
python3 -c "import json;d=json.load(open('App/dhis2/metadata/users_roles.json'));print('userRoles:',len(d['userRoles']),'name:',d['userRoles'][0]['name'])"
```
Expected: `userRoles: 1 name: Village Health Worker`. Confirm the file contains **no user passwords** (it shouldn't — it's a role, not a user).

- [ ] **Step 4: Commit**

```bash
git add App/dhis2/metadata/users_roles.json
git commit -m "Add Village Health Worker user role (exported metadata)"
```

---

### Task 4: Import smoke test + Makefile target

Proves the exported metadata re-imports cleanly (after org units) and that the programs exist with the right structure and org-unit assignment.

**Files:**
- Create: `App/dhis2/tests/test_programs_smoke.py`
- Modify: `App/dhis2/Makefile`

- [ ] **Step 1: Write the smoke test**

Create `App/dhis2/tests/test_programs_smoke.py`:

```python
"""Integration smoke test for the event programs. Requires a running DHIS2.
Skips when unreachable so unit tests still run without Docker.
Imports org_units first (programs reference org-unit UIDs), then the programs
and role, then verifies structure via the Web API.
"""

from pathlib import Path

import pytest
import requests

from metadata import import_metadata as im

META = Path(__file__).resolve().parent.parent / "metadata"


def _dhis2_up() -> bool:
    try:
        r = requests.get(f"{im.base_url()}/api/system/info.json", auth=im.auth(), timeout=5)
        return r.ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(not _dhis2_up(), reason="DHIS2 not reachable")


def _get(path, **params):
    r = requests.get(f"{im.base_url()}{path}", params=params, auth=im.auth(), timeout=30)
    r.raise_for_status()
    return r.json()


def _import_all():
    # Org units first — programs reference their UIDs.
    for fname in ("org_units.json", "program_illness.json", "program_water.json", "users_roles.json"):
        result = im.import_metadata(str(META / fname))
        assert result.get("status") in ("OK", "SUCCESS"), (fname, result)


def _program(name):
    progs = _get(
        "/api/programs.json",
        filter=f"name:eq:{name}",
        fields="id,programType,organisationUnits~size,programStages[programStageDataElements[dataElement[name,valueType]]]",
        paging="false",
    )["programs"]
    assert progs, f"program not found: {name}"
    return progs[0]


def test_import_is_clean():
    _import_all()


def test_illness_program_structure():
    _import_all()
    p = _program("Community Illness Report")
    assert p["programType"] == "WITHOUT_REGISTRATION"
    des = [
        de["dataElement"]["name"]
        for stage in p["programStages"]
        for de in stage["programStageDataElements"]
    ]
    assert any("case count" in n for n in des)
    assert any("symptoms" in n.lower() for n in des)
    assert any("onset" in n.lower() for n in des)
    # assigned to at least the 32 boreholes
    assert p["organisationUnits"] >= 32


def test_symptoms_option_set_has_four_options():
    _import_all()
    os_ = _get("/api/optionSets.json", filter="name:eq:Symptoms",
               fields="options~size", paging="false")["optionSets"]
    assert os_ and os_[0]["options"] == 4


def test_water_program_structure():
    _import_all()
    p = _program("Water Quality Summary")
    assert p["programType"] == "WITHOUT_REGISTRATION"
    des = [
        de["dataElement"]["name"]
        for stage in p["programStages"]
        for de in stage["programStageDataElements"]
    ]
    assert len(des) >= 8
    assert p["organisationUnits"] >= 32


def test_vhw_role_present():
    _import_all()
    roles = _get("/api/userRoles.json", filter="name:eq:Village Health Worker",
                 fields="id", paging="false")["userRoles"]
    assert roles
```

- [ ] **Step 2: Run the smoke test against the live instance**

Run: `cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/App/dhis2 && python -m pytest tests/test_programs_smoke.py -v`
Expected: 5 passed (DHIS2 reachable). If DHIS2 is down they SKIP. If the symptoms test fails with `options == 1` you likely created options under the wrong set; re-check Task 1 Step 1.

- [ ] **Step 3: Run the WHOLE suite to confirm no regressions**

Run: `cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/App/dhis2 && python -m pytest -v`
Expected: all Plan 1 tests still pass plus the 5 new ones (smoke tests run, not skipped, since DHIS2 is up).

- [ ] **Step 4: Add a Makefile `metadata` target**

In `App/dhis2/Makefile`, add this target (TAB-indented recipe lines). Keep existing targets:

```makefile
metadata:
	PYTHONPATH=. python -m metadata.generate_org_units
	PYTHONPATH=. python -m metadata.import_metadata metadata/org_units.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/program_illness.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/program_water.json
	PYTHONPATH=. python -m metadata.import_metadata metadata/users_roles.json
```

Also add `metadata` to the `.PHONY` line.

- [ ] **Step 5: Verify the Makefile target works end-to-end**

Run: `cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions/App/dhis2 && make metadata`
Expected: each import prints `import status=OK ...` with no errors.

- [ ] **Step 6: Commit**

```bash
git add App/dhis2/tests/test_programs_smoke.py App/dhis2/Makefile
git commit -m "Add event-programs import smoke test + Makefile metadata target"
```

---

## Self-Review

**Spec coverage (against the 2026-06-03 design spec + 2026-06-05 revision):**
- §4 Program A *Community Illness Report* (case count / symptoms / onset, borehole OU) → Task 1. ✅
- §4 Program B *Water Quality Summary* (8 summary fields, borehole OU) → Task 2. ✅
- §4 VHW role → Task 3. ✅
- §4 config-as-code under `App/dhis2/metadata/` → exports in Tasks 1–3. ✅
- §8 metadata smoke test → Task 4. ✅
- **Deferred per D14/D15 (correctly absent):** label program, Risk/Decision element, labelling logic, XGBoost.

**Placeholder scan:** No "TBD/TODO" implementation hand-waves. The Multi-text fallback (Task 1 Step 2) is a real, specified alternative, not a placeholder. The manual demo-user step (Task 3 Step 2) is intentionally not committed (credential hygiene) and is clearly marked optional.

**Consistency:** Program names (`Community Illness Report`, `Water Quality Summary`), the option set name (`Symptoms`), and the role name (`Village Health Worker`) are used identically in the UI steps, the export `curl` filters, and the smoke-test assertions. The smoke test imports `org_units.json` before the program files, matching the UID-reference dependency. `import_metadata`/`base_url`/`auth` are reused from Plan 1 unchanged.

**Known version-sensitivity:** `programType == "WITHOUT_REGISTRATION"` is the API value for an event program in 2.42; if a future DHIS2 renames it, Task 4's assertions are where to adjust. Event *creation* (vs metadata) is deliberately left to manual UI/Capture-app verification to avoid the `/api/events` vs `/api/tracker` version split.
