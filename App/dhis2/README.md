# DHIS2 VHW + Water Surveillance (parallel track)

Lives at `App/dhis2/`, separate from the frozen `App/backend` Railway demo.
See `docs/superpowers/specs/2026-06-03-dhis2-vhw-water-surveillance-design.md`.

## Pinned versions
- DHIS2 image: `dhis2/core:42.5.0`  (set in docker-compose.yml; see Task 2)
- Forked Android Capture App upstream tag: _TBD in Plan 4_

## Provenance of copied data
- `metadata/seed_data.py` is COPIED from `App/backend/database.py`
  (SEED_NEIGHBORHOODS / SEED_STATIONS). The two projects are deliberately
  separate; this copy is intentional, not shared code.

## Local dev
    cd App/dhis2
    docker compose up -d            # boots DHIS2 (slow first run; see Task 2)
    python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
    make orgunits                   # generate + import org units
    make test                       # unit + API smoke tests
