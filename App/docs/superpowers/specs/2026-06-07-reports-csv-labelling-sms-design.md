# Reports CSV + Labelled Water Dataset + SMS→DHIS2 Bridge — Design

**Date:** 2026-06-07
**Status:** Design approved; pending spec review before planning.
**Author:** Brainstormed with Claude.

## 1. Problem and goal

Three connected capabilities on top of the DHIS2 demo (the **final 2026-06-11
submission**):

1. **Reports dataset** — export DHIS2 *Community Illness Reports* events to a
   single, trackable CSV, one row per report, with symptoms (0/1 columns) and a
   timestamp.
2. **Labelled water dataset** — a second CSV of water-quality readings labelled
   by the project partner's decay-scoring logic (`at_risk` / `unlabelled`),
   **linked to the reports CSV by `station_id`**.
3. **SMS functionality** — inbound SMS reports become DHIS2 report events, via the
   existing Flask `/sms` handler acting as a bridge.

### Framing guardrail (non-negotiable)

Outputs describe **contamination / outbreak risk**, never "cholera detection."
The partner's label is `at_risk`; an optional `unsafe` alias column = `(label ==
"at_risk")` may be added for the user's wording. Reports are a *proxy* signal.

## 2. Decisions log

| # | Decision | Rationale |
|---|----------|-----------|
| E1 | Both features target the **DHIS2 instance** (the final demo), not the Flask app | User confirmed the DHIS2 demo is the submission. |
| E2 | **Reports CSV = one row per report, wide symptom 0/1 columns** | Best for tracking/analysis; matches the TRUE_ONLY symptom fields. |
| E3 | SMS via **Flask `/sms` as an SMS→DHIS2 bridge** | Reuses the existing, tested Twilio webhook + `sms_dialog.py` parsing; fastest path. |
| E4 | **Import the partner's `label_readings()`** from `Data/Labelling/Labelling Logic.py` — do not reimplement | Honors D15 (labelling scheme is partner-owned). The filename has a space → load via `importlib`. |
| E5 | **Water readings are simulated** | No real sensor data exists (Flask `sensor_readings` = 1 row; DHIS2 Water Quality = 0 events; phase-1 datasets are unrelated targets). This demonstrates the labelling *pipeline*, clearly marked synthetic. |
| E6 | **Two linked CSVs**, joined on `station_id` (+ 7-day window) | Matches how the partner's logic ties a reading to a station's reports. |
| E7 | New CSV/ETL/simulation code lives in **`App/dhis2/`**; SMS bridge is a **new module + one guarded hook** in shared `App/backend` | Keeps the DHIS2 work isolated and minimizes merge friction on partner-shared Flask code. |

## 3. Partner labelling logic (the contract we consume)

`Data/Labelling/Labelling Logic.py` (and its `.md`): for each reading, sum a
log-decay score over the station's reports within 7 days
(`1 * (1 - log(t+1)/log(8))`, `t` = fractional days), bin the sum into confidence
tiers (`<0.5`→unlabelled, `0.5–1.5`→0.3, `1.5–2.5`→0.6, `2.5+`→0.9), label
`at_risk` if confidence is not None else `unlabelled`. Public entry point:

```python
label_readings(readings: list[dict], reports: list[dict]) -> list[dict]
# readings: [{"id", "station_id", "timestamp"(datetime), ...}]
# reports:  [{"station_id", "timestamp"(datetime)}]
# returns:  [{"reading_id","station_id","timestamp","label","confidence","score"}]
```

We call this **unchanged**.

## 4. Components & data flow (`App/dhis2/`)

```
DHIS2 events ──► export_reports.py ──► reports.csv  (+ reports list in memory)
                                          │  station_id, timestamp, symptoms 0/1
simulate_water_readings.py ──► readings list (synthetic; per station, over window)
                                          │
reports list + readings list ──► label_water.py ──► labeled_water_readings.csv
        (imports partner's label_readings via importlib)   score, confidence, label
                                          │
                              linked by station_id (+ 7-day window)
```

- **`export_reports.py`** — query DHIS2 *Community Illness Reports* events (reuse
  `metadata/import_metadata.py`'s `base_url`/`auth`); map org-unit `code`
  `STATION-<n>` → integer `station_id`; event date → `timestamp`; emit
  `App/dhis2/data/reports.csv` and return the reports list
  (`[{station_id, timestamp}]`).
- **`simulate_water_readings.py`** — generate synthetic readings for the 32
  stations across the reports' date range (turbidity, pH, temperature, rainfall,
  chlorine, plus `id`, `station_id`, `timestamp`); deterministic seed; clearly
  documented as synthetic.
- **`label_water.py`** — `importlib`-load `Data/Labelling/Labelling Logic.py`,
  call `label_readings(readings, reports)`, join the label fields back onto the
  reading measurements, write `App/dhis2/data/labeled_water_readings.csv`
  (optional `unsafe` alias column).
- **`make datasets`** — runs export → simulate → label, producing both CSVs.

### CSV schemas

`reports.csv`: `event_id, timestamp, onset_date, station_id, borehole,
neighbourhood, case_count, diarrhoea, vomiting, fever, dehydration, … (18 symptom
0/1 columns)`.

`labeled_water_readings.csv`: `reading_id, station_id, timestamp, turbidity_ntu,
ph, temperature_c, rainfall_mm, chlorine_mg_l, score, confidence, label[, unsafe]`.

## 5. SMS→DHIS2 bridge (`App/backend/`)

- **New module `App/backend/dhis2_bridge.py`**:
  `create_event_from_report(station_id, case_count, symptoms, onset)` → resolve
  the borehole org unit by `STATION-<station_id>`, build the event (program +
  stage + dataValues: case count, onset date, symptom checkboxes `true` for
  reported), `POST /api/tracker`. Program/stage/data-element UIDs resolved by
  code/name at call time (not hardcoded). DHIS2 connection from env
  (`DHIS2_BASE_URL`, `DHIS2_USER`/`DHIS2_PASSWORD`).
- **Hook in `app.py` `/sms`**: when the dialog completes, if
  `DHIS2_BRIDGE_ENABLED` is set, call the bridge — **in addition to** existing
  behaviour, and **without** invoking `labels.py` (labelling is the partner's
  domain). One guarded call + import; existing flow unchanged when the flag is
  off.
- **Symptom mapping**: `sms_dialog.py` collects the original 4 symptoms
  (diarrhoea/vomiting/fever/dehydration) → set the matching DHIS2 checkboxes; the
  other 14 stay 0.
- **Demo path**: Twilio number → ngrok → Flask `/sms` → DHIS2 event → appears on
  the dashboard.

## 6. Testing

- **export_reports / label_water**: integration tests that skip when DHIS2 is
  unreachable (matching the existing `App/dhis2/tests` pattern). Assert
  `reports.csv` columns + row count == event count; assert
  `labeled_water_readings.csv` has the label/confidence/score columns and that a
  reading near a clustered-report station comes back `at_risk`.
- **label_water** uses the partner's function: a small test mirrors one scenario
  from their `__main__` (e.g. 3 fresh reports → high confidence) to confirm we're
  wired to their logic, not a copy.
- **dhis2_bridge**: unit-test the event-payload construction (UID resolution +
  dataValues) with the API mocked; an optional integration test creates an event
  and verifies it via the API (skips if DHIS2 down).
- **Flask regression**: existing `/sms` tests still pass with the flag off.

## 7. Out of scope / deferred

- Pushing simulated water readings into the DHIS2 *Water Quality Summary* program
  (the gateway — "Plan 3"); here we only produce the CSV.
- The server-side ML model (paused, D14).
- Real sensor hardware / a live ingest pipeline.
- Production Twilio hardening beyond signature validation already in the Flask app.

## 8. Open items for planning

- Simulated-reading cadence (per-day count per station) and value ranges.
- Whether to also emit a dated snapshot (`reports-YYYY-MM-DD.csv`) vs overwrite.
- Whether to include the `unsafe` alias column by default.
- DHIS2 service account vs admin creds for the SMS bridge.
