# Design — Medical history, government detail + actions, SMS dialog

**Date:** 2026-05-28
**Status:** Approved (brainstorming complete; awaiting implementation plan).
**Scope:** Four related additions to the Gen-1 water-safety app — referred to as Phases C, D, E, F. Single coherent design because they share schema, data flow, and the same illness_reports → labelling pipeline.

## 1. Context

The Gen-1 app currently has:
- SMS leg: community members text a station number → row in `illness_reports` → trailing 7-day window of readings retro-labelled `unsafe` → auto-reply.
- Medical portal leg: signed-in medical staff submit a structured form (case_count, symptoms, onset_date) → row in `illness_reports` (`report_source='medical_portal'`) → same labelling.
- Government dashboard: shows per-station rollup status + recent reports.

This design adds:
- **Phase C:** medical history page with a Harare-centred Leaflet map.
- **Phase D:** government per-report detail page with a risk-tier estimator that runs when the reporter didn't fill in a tier.
- **Phase E:** action buttons on the government side (close/reopen borehole, dispatch sample team, dispatch medical team) backed by an append-only interventions table.
- **Phase F:** multi-turn SMS dialog that progressively enriches the SMS report with structured fields, so it ends up structurally equivalent to a medical-portal report.

## 2. Key design decisions

| Decision | Choice | Rationale |
|---|---|---|
| Diagnosis-output shape | **Risk tier** (LOW / MEDIUM / HIGH / SEVERE) | Defensible against the "not medical advice" framing in `issues_v3.md §C6`; matches the project's existing risk-band terminology end-to-end. |
| Estimator rule | **Cholera-pattern heuristic** | Tier reflects whether the symptom pattern matches the disease we care about, not raw symptom count. Transparent, easy to defend. |
| Action button placement | **Dashboard rows + report detail page** | Supports both proactive ("sensors look bad") and reactive ("this report came in") workflows. Close is reversible. |
| Medical history page | **All medical_portal reports + Harare-centred Leaflet map** | Shared situational awareness across the medical team. OSM tiles, no API key. |
| SMS handling | **Multi-turn dialog** | Progressively populates structured fields so the estimator runs on real data, not defaults. Architecturally clean: SMS and medical-portal reports converge to the same shape. |
| Medical-side detail page | **Parallel `/medical/reports/<id>`** | Lets medical staff review their own and colleagues' reports without granting them government-only privileges. |

## 3. Schema changes

All additions use the idempotent `_migrate(conn)` pattern from `database.py`. Existing rows are preserved.

### `illness_reports` — add columns

| Column | Type | Notes |
|---|---|---|
| `risk_tier` | `TEXT` | `CHECK (risk_tier IN ('low','medium','high','severe'))`. NULL means "reporter didn't assess" (estimator runs on read). |
| `dialog_state` | `TEXT` | `CHECK (dialog_state IN ('awaiting_case_count','awaiting_symptoms','awaiting_onset','complete','abandoned'))`. NULL for `medical_portal` rows and for SMS rows without a parsed station. |

### `stations` — add column

| Column | Type | Notes |
|---|---|---|
| `is_closed` | `INTEGER NOT NULL DEFAULT 0` | Denormalised cache. 1 ⇔ latest non-null intervention on this station was `close_borehole`. |

### New table `interventions` (append-only)

```sql
CREATE TABLE IF NOT EXISTS interventions (
    intervention_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id         INTEGER NOT NULL REFERENCES stations(station_id),
    action_type        TEXT    NOT NULL
        CHECK (action_type IN (
            'close_borehole', 'reopen_borehole',
            'dispatch_sample_team', 'dispatch_medical_team')),
    triggered_by       TEXT    NOT NULL,
    triggered_at       TEXT    NOT NULL DEFAULT (datetime('now')),
    related_report_id  INTEGER REFERENCES illness_reports(report_id),
    notes              TEXT
);

CREATE INDEX IF NOT EXISTS idx_interventions_station_time
    ON interventions(station_id, triggered_at);
CREATE INDEX IF NOT EXISTS idx_interventions_report
    ON interventions(related_report_id);
```

`stations.is_closed` is the cached read-fast view of "the most recent intervention for this station." Close/reopen each insert a *new row* in `interventions`; no UPDATE on existing intervention rows ever.

## 4. Endpoint map

### New routes

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/medical/history` | medical | List of medical_portal reports + Leaflet map |
| GET | `/medical/reports/<report_id>` | medical | Read-only report detail (no actions, no estimator banner) |
| GET | `/dashboard/reports/<report_id>` | government | Full report detail + estimator + action buttons + interventions log |
| POST | `/actions` | government | Single endpoint for all four action types |

### Changed routes

| Method | Path | Change |
|---|---|---|
| GET | `/medical/report` | Adds risk-tier dropdown above symptoms |
| GET | `/dashboard` | Each station row gets action buttons + lock badge; each illness-report row links to `/dashboard/reports/<id>`; reports panel adds risk-tier pill column |
| POST | `/sms` | Becomes a state machine (Phase F state table below) |

### Unchanged

`/`, `/login`, `/logout`, `/health`, `/ingest`.

## 5. Risk-tier estimator

Pure function in `app.py` (or `estimator.py` if it grows). No DB access. Recomputed at render time on the gov detail page.

```python
def estimate_risk_tier(
    symptoms: list[str],         # subset of {diarrhoea, vomiting, fever, dehydration}
    onset_date: date | None,     # None if reporter didn't supply
    case_count: int,             # defaults to 1 if missing
) -> tuple[str, str]:            # (tier, rationale)
    """Cholera-pattern heuristic. See spec §5 for rule order."""
```

### Rules in priority order (first match wins)

1. **SEVERE** — all four must hold:
   - `'diarrhoea' in symptoms`
   - `'dehydration' in symptoms`
   - `onset_date is not None AND (today − onset_date) ≤ 3 days`
   - `case_count ≥ 3`
   - *Rationale string:* `"textbook severe-cholera pattern (diarrhoea + dehydration + recent onset + multiple cases)"`

2. **HIGH** — any one of:
   - `len(symptoms) ≥ 3`
   - `case_count ≥ 5 AND len(symptoms) ≥ 2`
   - `'diarrhoea' in symptoms AND onset_date is not None AND (today − onset_date) ≤ 3 days`
   - *Rationale string:* describes which sub-rule matched, e.g. `"3+ symptoms reported"`, `"outbreak-scale case count (≥5) with multiple symptoms"`, or `"recent-onset diarrhoea"`.

3. **MEDIUM** — `1 ≤ len(symptoms) ≤ 2`. *Rationale string:* `"1–2 non-specific symptoms reported"`.

4. **LOW** — `len(symptoms) == 0`. *Rationale string:* `"no symptoms reported — request clinical assessment regardless"`.

### Defensive handling

- Unparseable or future-dated `onset_date` is treated as `None`.
- Missing or non-positive `case_count` defaults to `1`.
- Function is pure (no I/O), unit-testable, idempotent.

### Where the output is displayed

`dialog_state` only gates estimator output for SMS reports. Medical_portal reports are structurally complete on insert and always have the estimator available.

| Report shape | What renders |
|---|---|
| `risk_tier IS NOT NULL` (any source) | Bright pill, label "Reporter's clinical assessment". **No estimator banner.** |
| `risk_tier IS NULL` and `report_source = 'medical_portal'` | Muted pill (estimated tier), label "Estimated risk tier", **yellow banner** "Estimated by automated heuristic — not medical advice. See rationale below." Rationale rendered verbatim. |
| `risk_tier IS NULL` and `report_source = 'sms'` and `dialog_state = 'complete'` | Same muted-pill + banner as the medical_portal estimated case. |
| `risk_tier IS NULL` and `report_source = 'sms'` and `dialog_state IN ('awaiting_case_count','awaiting_symptoms','awaiting_onset')` | No pill. Text: "**pending** — awaiting reporter follow-up". |
| `risk_tier IS NULL` and `report_source = 'sms'` and `dialog_state IN ('abandoned', NULL)` | No pill. Text: "**incomplete** — no structured data available". (Covers legacy SMS rows from before Phase F as well as abandoned conversations.) |

**Medical detail page** (`/medical/reports/<id>`): same logic for the pill itself, but **no estimator banner** — medical staff see their own and colleagues' filings; estimation is government-side context, not clinical guidance.

## 6. Phase C — medical portal additions

### Top nav

Two links on every medical page: "File a report" → `/medical/report`, "History" → `/medical/history`. Right side shows `Signed in as Dr. Smith · Sign out`.

### Form change on `/medical/report`

One new field above symptoms:

```
Risk tier (your clinical assessment, optional)
  ◉ Not yet assessed — estimate on review (default)
  ○ LOW    — non-specific symptoms
  ○ MEDIUM — possible waterborne illness
  ○ HIGH   — likely waterborne illness, clinical workup recommended
  ○ SEVERE — suspected severe cholera, urgent action
```

Stored as `illness_reports.risk_tier`. NULL when "Not yet assessed".

### New page `/medical/history`

Top to bottom:

1. **Leaflet map**, ~300 px tall, centred on Harare `(-17.8292, 31.0522)`, initial zoom 12.
   - Tile source: OSM (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`), no API key.
   - One circle marker per station with `≥1` medical_portal report. Radius scaled to report count.
   - Stations with zero medical-portal reports get a small grey marker.
   - Popup: station name + report count + most-recent-report timestamp.
   - Leaflet 1.9.4 via CDN (`unpkg.com`): one CSS link + one JS script tag. No build step.
2. **Reports table**: last 50 medical_portal reports across *all* medical staff. Columns: `Submitted`, `Submitter`, `Station`, `Cases`, `Symptoms`, `Risk tier`, `Onset`. The `Risk tier` column follows the §5 logic restricted to medical_portal rows: bright pill if `risk_tier IS NOT NULL`, muted estimated pill otherwise. (No "pending"/"incomplete" states reach this table — those are SMS-only and SMS reports never appear here.)
3. **Row click → `/medical/reports/<id>`** detail page.

### New page `/medical/reports/<report_id>`

Read-only view of one medical_portal report. Includes structured fields + risk-tier block (variants from §5). **No action buttons. No interventions log. No labelled-readings table.** Top nav has a `← History` link.

## 7. Phase E — government portal additions

### Dashboard changes

- **Left panel "Station status":** each row gains a small action area on the right with three buttons. The button shown for close is *Close* if `is_closed=0`, *Reopen* if `is_closed=1`. Each button is a tiny `<form method="POST" action="/actions">` with hidden fields + a JS `confirm("Close station N?")` on submit. Closed stations show a 🔒 prefix on the name and a slightly muted row background.
- **Right panel "Recent illness reports":** rows are clickable links to `/dashboard/reports/<id>`. New column shows the risk-tier display from §5 (LOW=green, MEDIUM=yellow, HIGH=orange, SEVERE=red; *muted* pill if estimated, *bright* pill if reporter-supplied; text "pending" or "incomplete" per the §5 table). The "unparsed" badge for SMS reports with no resolved station stays.

### New page `/dashboard/reports/<report_id>`

Top to bottom:

1. **Breadcrumb:** `← Dashboard › Report #<id> · <station name>`. The "NOT a cholera detector" disclaimer strip.
2. **Report metadata block:** source (`sms` | `medical_portal`), received_at, submitter (username for medical_portal; raw `reporter_phone` for SMS — privacy caveat documented in `issues_v3.md §D4`), parser_version.
3. **Structured fields:** station, case_count, symptoms (pills), onset_date, notes, raw_message (collapsed by default).
4. **Risk-tier block** (two variants from §5).
5. **Labelled readings table:** `reading_labels` rows joined to `sensor_readings` for `report_id = <id>`. Columns: reading_id, recorded_at, pH, turb, temp, rule_description.
6. **Action buttons:** Close/Reopen, Sample team, Medical team. Each posts to `/actions` with `related_report_id=<id>` auto-attached.
7. **Interventions log:** rows from `interventions` where `related_report_id=<id>`, ordered chronologically. Shows action_type, triggered_by, triggered_at, notes.

### Cross-role access

A medical user hitting `/dashboard/reports/<id>` gets a 403 with body: *"This page is for government officials. Medical staff can view this report at `<link to /medical/reports/<id>>`."*

### `POST /actions`

Single endpoint for all four action types.

**Form fields (POST body):**
- `action_type` (required, must be one of the four allowed)
- `station_id` (required, must exist)
- `related_report_id` (optional)
- `notes` (optional, ≤500 chars; truncated server-side)

**Validation:**
- `close_borehole` rejects (400) if station is already closed.
- `reopen_borehole` rejects (400) if station is already open.
- Dispatches always allowed.
- Unknown `station_id` → 400.

**Effect:**
- Inserts a row into `interventions` with `triggered_by = session['username']`.
- For `close_borehole` / `reopen_borehole`, also updates `stations.is_closed` (the cache).

**Response:** 302 redirect to `request.referrer` if it starts with `/`, else `/dashboard`.

## 8. Phase F — SMS multi-turn dialog

### State machine

State lives in `illness_reports.dialog_state`. Conversation identity = `reporter_phone` + the most recent illness_reports row from this phone within the last **30 minutes** whose `dialog_state` is non-terminal. Older in-progress rows are marked `abandoned` lazily on the next interaction.

```
[no recent conversation, station parsed]
        │
        ▼
awaiting_case_count
        │  integer 1..200
        ▼
awaiting_symptoms
        │  '1,3' or 'diarrhoea, fever' (canonical-keys subset)
        ▼
awaiting_onset
        │  'today' | 'yesterday' | DD/MM | DD/MM/YY
        ▼
    complete

Any state + STOP keyword → abandoned
Any state + new SMS containing a station number → previous row → abandoned; new row in awaiting_case_count
Any state + unparseable input → state unchanged; re-prompt
```

### Per-state behaviour

| State on receipt | Inbound | Action | Outbound reply |
|---|---|---|---|
| (no in-progress) | text contains station # | Insert row; **fire labelling** on trailing 7d window; `dialog_state=awaiting_case_count` | "Report received for {station name}. {N} reading(s) flagged. How many people are sick? Reply with a number." |
| (no in-progress) | text contains no station # | Insert row with `station_id=NULL`, `dialog_state=NULL` | "We received your message but could not identify a station number. Reply with the station number (e.g. '4'). Thank you." |
| `awaiting_case_count` | integer 1..200 | Update `case_count`; advance to `awaiting_symptoms` | "Noted, {N} cases. Which symptoms? Reply with numbers, e.g. '1,3'. 1=diarrhoea 2=vomiting 3=fever 4=dehydration." |
| `awaiting_case_count` | other | (re-prompt only) | "I didn't understand. How many people are sick? Reply with a number." |
| `awaiting_symptoms` | comma/space digits or symptom-names subset | Update `symptoms` (JSON list of canonical keys); advance to `awaiting_onset` | "Noted: {symptoms}. When did symptoms start? Reply 'today', 'yesterday', or DD/MM." |
| `awaiting_symptoms` | other | (re-prompt only) | "I didn't understand. Reply with numbers, e.g. '1,3'. 1=diarrhoea 2=vomiting 3=fever 4=dehydration." |
| `awaiting_onset` | `today` | onset = today; advance to `complete` | "Report complete. Stay safe. Reply STOP to opt out." |
| `awaiting_onset` | `yesterday` | onset = today − 1d; advance to `complete` | (same) |
| `awaiting_onset` | `DD/MM` or `DD/MM/YY` | parse (current year default; reject future) → onset; advance to `complete` | (same) |
| `awaiting_onset` | other | (re-prompt only) | "I didn't understand. Reply 'today', 'yesterday', or DD/MM." |
| any with an in-progress conversation | message contains `STOP` (case-insensitive, word-boundary) | Mark `abandoned` | "Opted out. We will no longer reply. Thank you." |
| no in-progress conversation | message contains `STOP` | No DB write; idempotent | "No active conversation to opt out of. Thank you." |
| any | text contains a *new* station # | Mark previous `abandoned`; insert new row in `awaiting_case_count`; fire labelling | (1st-SMS reply for the new station) |
| `complete` / `abandoned` | any text | Treated as "no in-progress" — start new conversation | (as appropriate) |

### Parse rules in detail

- **Station number:** existing `\b\d{1,4}\b` regex (`STATION_PARSER_VERSION = lenient_first_int_v1`).
- **Case count:** first integer 1..200 in the message. Rejected if 0 or > 200.
- **Symptoms:** match each token against canonical keys (`diarrhoea`, `vomiting`, `fever`, `dehydration`) and against the digits 1..4. Build a deduplicated, ordered list. Empty list rejected (re-prompt).
- **Onset:** `today` / `yesterday` (case-insensitive); `DD/MM` interpreted in current UTC year (reject if resulting date is in the future); `DD/MM/YY` interpreted as 2000-2099. Anything else rejected.

### Labelling timing

Labelling fires **only** at the moment the station is first identified (1st SMS or station-switch within a conversation). Subsequent dialog turns enrich the row but do not re-trigger labelling. This matches the SMS reporter's mental model: "I texted, it got flagged."

### Estimator behaviour for SMS

Tied directly to `dialog_state`:

- `dialog_state IN ('awaiting_*', 'abandoned', NULL)` → tier displayed as "pending — awaiting reporter follow-up". Estimator does not run.
- `dialog_state = 'complete'` → estimator runs on the fully-populated `symptoms` + `onset_date` + `case_count`, same as medical_portal reports.

### Cost note

Each completed SMS conversation uses 4 outbound SMS (one per state transition reply) versus 1 today. Twilio trial credit (~$15.50, ~$0.0075/outbound) absorbs this for the demo, but it is a per-report cost worth flagging. Already covered under `issues_v3.md §C1`.

## 9. Out of scope (intentional)

- Real-time push of report notifications. Government has to refresh the dashboard.
- Editing or deleting reports — append-only by design.
- Bulk actions ("close all stations").
- Map clustering / heatmap — 10 stations doesn't justify it.
- Reverse-geocoding / address lookup — pins are lat/long only.
- Map on the government dashboard — stays a list view.
- Search or filter on the history / dashboard pages.
- Per-phone opt-out list — STOP just abandons the current conversation; a re-arriving SMS from the same phone starts a new one.
- Asynchronous nudges in the SMS dialog ("you haven't replied in 5 minutes, is everything OK?").
- Multi-station reports inside one SMS conversation.
- Phone-number hashing or other consent-layer work (still `issues_v3.md §D4`).
- New roles, new authentication mechanisms, language detection, internationalisation.
- Admin UI to manage the symptom list, the seeded stations, or the estimator rules.

## 10. Implementation phasing

Suggested order, each phase committable on its own:

1. **Phase D (gov detail + estimator) first.** Foundational: introduces `risk_tier` column, the estimator function, the gov detail page, and the form dropdown. Most other phases depend on the estimator function existing.
2. **Phase C (medical history + map).** Read-only addition; uses the risk_tier from Phase D for the table.
3. **Phase E (gov actions + interventions).** Independent of C/F; adds the interventions table + `/actions` endpoint + the dashboard button area.
4. **Phase F (SMS multi-turn dialog).** Most contained — touches only `/sms`, the schema (`dialog_state`), and the estimator's "do I run?" gate. Goes last so the gov-side rendering knows how to read `dialog_state`.

Each phase: scratch-DB verification via Flask test client (the same pattern used for Phase A/B), then commit + push, then prompt the user to restart Flask.

## 11. Risks not already in issues_v3.md

- **Multi-turn SMS state collisions** when a phone has more than one active conversation (unlikely on a single Twilio number but possible). Mitigation: latest non-terminal row wins; older rows abandoned on next interaction.
- **Estimator gives confident-looking output on weak input** (e.g. only `fever` ticked → MEDIUM). Mitigation: rationale string is rendered verbatim; banner always says "not medical advice."
- **Closed station still appears in the simulator's POSTs** because the simulator doesn't know the station was closed. Mitigation: this is fine — the field sensor wouldn't know either; the close flag is a metadata signal for humans, not a routing control.
- **Leaflet from CDN** has the usual CDN-availability risk for the demo. Mitigation: if unpkg is down, the map fails to render but the table below it works (graceful degradation).

## 12. Verification plan per phase

For each phase, a Flask test-client script on a scratch DB exercising:

- **Phase D:** estimator unit tests on all four rule rungs and the defensive cases; gov detail page renders for both reporter-tier and estimated-tier variants; medical user gets 403 on `/dashboard/reports/<id>`.
- **Phase C:** `/medical/history` renders with 0 / 1 / 50 reports; map HTML contains the expected `L.map(...)` and station JSON.
- **Phase E:** `/actions` accepts each of the four action types; close-then-close rejects with 400; close-then-reopen succeeds; `stations.is_closed` cache reflects the latest intervention.
- **Phase F:** state machine integration test from awaiting_case_count → complete; STOP terminates; new station number mid-conversation abandons + starts new; garbage input re-prompts without state change.
