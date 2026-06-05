# DHIS2 VHW + Water Surveillance — Design

**Date:** 2026-06-03
**Status:** Design approved. Plan 1 (instance + org units) implemented. Scope
refined 2026-06-05 — see Revision below.
**Author:** Brainstormed with Claude.

## Revision — 2026-06-05 (demo scope, "Path A")

Clarified the immediate goal: **a class demo that uses real DHIS2 software and
can be driven by a simulator**, distinct from the 2026-06-11 submission (the
frozen Railway demo still covers that). We chose **Path A — the centralised
demo**, which refines several earlier decisions:

- **D10 — Stock Capture App for the demo; the fork (D9) is deferred.** Health is
  collected with the unmodified DHIS2 Capture App (or DHIS2 web Capture for
  reliability on stage). The forked app (community-facing status/advice screen)
  remains the post-demo stretch goal, not demo scope. Plan 4 is therefore
  deferred.
- **D11 — Water stays on the centralised side.** Borehole sensors → Flask
  gateway → *Water Quality Summary* events → **DHIS2 dashboards + GIS**. Water is
  NOT surfaced in the mobile app (that would need the fork). The app stays
  health-focused.
- **D12 — ML runs server-side and pushes decisions to DHIS2.** A server-side
  XGBoost step reads water summaries and writes a **Risk/Decision** output back
  into DHIS2 (new data element/event, displayed on dashboards). For the demo this
  is **illustrative** (trained on simulated/old data — no real labelled windows
  exist yet; Gen-1 is still label-generation, not live inference per `CLAUDE.md`).
  Output framing: contamination/outbreak-risk, **never "cholera detection"**, with
  an **abstain → "send a sample to the lab"** state for out-of-range inputs.
- **D13 — A simulator drives the pipeline on stage.** Injects fake sensor
  readings (and optionally a report or two) so the sensor → summary → risk → label
  flow animates on demand, no field hardware or live phones required.

- **D14 — ML algorithm deferred (2026-06-05).** Not developing the ML model for
  now. The server-side XGBoost step and the Risk/Decision output element (D12) are
  **paused** — not built until further notice.
- **D15 — Labelling scheme logic is PARTNER-OWNED (2026-06-05).** A project
  partner is writing the labelling-scheme logic (the rule that decides which
  readings/windows are labelled unsafe). Claude must **NOT** implement labelling:
  no `labelling.py`, no label rule, no label-program wiring. Integrate against the
  partner's logic only once its repo location is provided. Until then, treat
  anything labelling-related as off-limits to avoid colliding with the partner's
  work. (Supersedes the planned port of `labels.py` into the gateway.)

Plan impact (revised): **Plan 2** = DHIS2 event programs for illness + water
summary (+ roles); the label program and Risk/Decision element are DEFERRED.
**Plan 3** = gateway (ingest → aggregate → push water summaries) + simulator;
the labelling job (partner) and XGBoost step are DEFERRED. **Plan 4** (fork)
deferred. Net buildable-now scope: illness + water programs, the gateway, and the
simulator.

## 1. Problem and goal

Build a system for collecting **community health data via Village Health Workers
(VHWs)** and **water-quality data from borehole sensors**, where the health-data
collection runs on the **DHIS2 Android Capture App** (forked) and all
analysis-grade data lands in a **self-hosted DHIS2** instance. The system extends
the project's existing purpose: linking community illness reports to water
readings to generate *unsafe-window* training labels (see `CLAUDE.md`,
`labels.py`).

This is built as a **separate entity** from the existing Flask/Twilio Railway
demo. The demo stays frozen and remains the submission hedge for the
**2026-06-11** deadline; this DHIS2 system is developed in parallel and is **not
on the critical path to submission**.

### Framing guardrail (non-negotiable)

This system measures faecal-contamination indicators and outbreak-conducive
conditions and collects community illness reports. It is **not** a cholera
detector and the sensor cannot identify *Vibrio cholerae*. No code, comment,
data element, or label may describe outputs as "cholera detection."

## 2. Decisions log

Each row is a decision taken during brainstorming, with the rationale.

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Health collection on the **DHIS2 Android Capture App** | Open-source, offline-first, metadata-driven; the supported mobile path for DHIS2. |
| D2 | **Self-host our own DHIS2** instance (Docker for dev) | Full control to define programs; no MoHCC governance needed for a prototype. |
| D3 | Health data uses a DHIS2 **Event program** | Mirrors the existing SMS dialog grain (count + symptoms + onset + location); gives the labeller its `(station, date)`. |
| D4 | **Everything into DHIS2** as system-of-record for analysis-grade data | Single analytics/dashboard/GIS hub; clean future national-HMIS story. |
| D5 | Sensor data enters via a **Flask gateway pushing daily summaries** | Devices can't speak DHIS2; raw telemetry must not bloat DHIS2. Gateway buffers raw, aggregates per-(station,day), pushes summaries. |
| D6 | **Borehole = leaf org unit** in the DHIS2 hierarchy | Native linkage (health + water events share the org unit); per-borehole GIS; matches the existing "name a station" flow. |
| D7 | **DHIS2 now; Impilo parked** | Impilo has no public dev API/SDK and needs MoHCC governance; DHIS2 is the open, self-hostable layer Impilo already feeds. No FHIR/Impilo work in scope now (see §9). |
| D8 | New project lives in a dedicated **`App/dhis2/` directory** (a sub-folder of `App/`, alongside `App/backend`) | Shares docs/research/history; deploys as its own Railway service; low friction. (Originally placed at top-level `dhis2/`; moved under `App/` on 2026-06-05.) |
| D9 | **Fork the full DHIS2 Android Capture App** (not the SDK route, not config-only) | User goals require custom code: user-facing status/advice, low-literacy UI, branding, and demonstrating an app build. Costs (APK bloat, upstream drift) accepted and managed (§7). |

### Impilo vs DHIS2 (research summary, supports D7)

Impilo and DHIS2 are **complementary layers of Zimbabwe's national stack, not
alternatives**. Impilo is the patient-level EHR / HIV case-based surveillance
system (point-of-care clinical registers); DHIS2 is the national **aggregate
HMIS** and analytics end-user database. Impilo already feeds DHIS2 over a
**FHIR-based OpenHIE pipeline** via Python middleware. Impilo exposes **no public
developer API/SDK/app** and requires MoHCC partnership; DHIS2 is fully open
(Android Capture App, Android SDK, Web API, self-hostable). For a community
*surveillance / data-collection* prototype, DHIS2 is both the buildable and the
nature-appropriate choice. Sources: Impilo MoHCC, Zim-TTECH, DHIS2 Community
Impilo–DHIS2 thread, Techzim, Global Fund Zimbabwe Digital Health case study.

## 3. Architecture

```
   VHW (Android phone)                     Borehole node (field hardware)
   FORKED DHIS2 Capture App                POST raw JSON + X-Device-Secret
   offline-first, syncs on signal                     │
   + user-facing status/advice screen                 ▼
            │  health events                    ┌──────────────┐
            │  (count, symptoms, onset,         │ Flask gateway │
            │   borehole org unit)              │  /ingest      │
            ▼                                    │  buffer raw   │
   ┌────────────────────────┐  water summary    │  aggregate    │
   │     DHIS2 server        │  events (daily    │  push to DHIS2│
   │  (own Docker instance)  │◄──per-station─────│              │
   │                         │   means/peaks)    └──────┬───────┘
   │  • org tree …>Borehole  │                          │ keeps raw
   │  • Program: Illness     │                          ▼ readings
   │  • Program: Water        │                  ┌──────────────┐
   │  • Program: Label        │◄──labels──┐      │ Postgres (raw│
   │  • Dashboards / GIS      │           │      │ telemetry +  │
   └────────────┬────────────┘           │      │ ML features) │
                │  Web API                │      └──────────────┘
                ▼                         │
        ┌───────────────────┐  writes label back
        │ Labelling job     │──to DHIS2 ┘
        │ (trailing-window   │  fetches illness + water
        │  rule)             │  events at same borehole / window
        └───────────────────┘
```

**System-of-record split:**

- **DHIS2** owns all analysis-grade data: illness case events, daily water
  summaries, computed labels, and all dashboards/maps.
- **Flask + Postgres** is reduced to (a) an authenticated **sensor gateway** that
  buffers raw readings and pushes daily summaries to DHIS2, and (b) host for the
  **labelling job**. Postgres retains raw high-frequency telemetry (DHIS2 must
  not; the eventual ML model wants raw resolution).
- The forked **Android app** is the VHW collection channel **and** the
  community-facing read channel (status + treatment advice).

The existing `App/backend` Railway demo (SMS + dashboard + `/ingest`) is
**untouched**. Reused logic is **copied/adapted**, not edited in place.

## 4. DHIS2 metadata model

Configuration-as-code: all metadata lives as version-controlled JSON under
`dhis2/metadata/`, importable into a fresh DHIS2 via the metadata API.

### Org-unit hierarchy (D6)

```
Zimbabwe (country)
└── District
    └── Village / community     ← existing `neighborhoods` table
        └── Borehole / Station   ← existing `stations` table (leaf; GPS → GIS)
```

Each borehole org unit carries its `station_id` so Postgres and DHIS2 agree on
identity. DHIS2 org-unit identity is the source of truth for linkage.

### Program A — "Community Illness Report" (event program, VHW-entered)

One non-repeatable stage. Maps 1:1 to the existing SMS dialog so no new clinical
concepts are invented.

| Data element | Type | Mirrors |
|--------------|------|---------|
| Case count | positive integer | `parse_case_count` |
| Symptoms | single-select Text + `Symptoms` option set — **8 options** as built 2026-06-05: diarrhoea, vomiting, fever, dehydration, weight loss, muscle cramps, shock, upset stomach (expanded from the original 4 SMS symptoms) | `SYMPTOMS` / `parse_symptoms` |
| Onset date | date | `parse_onset` |
| (event date = report date; org unit = borehole) | — | the SMS "station number" |

### Program B — "Water Quality Summary" (event program, gateway-pushed)

One event per (borehole, day). Never hand-entered.

- turbidity mean & peak, temperature mean, rainfall total, pH mean,
  chlorine mean (when present)
- derived: days-above-threshold, rate-of-change, raw-reading count, provenance
- event date = the summary day; org unit = borehole

### Program C — "Reading Label" (event program, labelling-job-written)

Preserves the audit trail `labels.py` builds in `rule_description`.

- label (`unsafe`), `rule_version` (`trailing_7d_v1`), window_start, window_end,
  triggering illness-report event UID

### Treatment-recommendation mapping (read path)

A mapping from label/severity to community-facing advice (from
`App/Ideation.md`: boil → chlorine tablets → shut off borehole, by severity).
Consumed by the forked app's status screen. Stored as config (exact home —
constant table in app vs DHIS2 option set — decided at planning).

### Users & roles

- **VHW role** — create Community Illness Report events at assigned org unit(s);
  uses the forked Android app.
- **`sensor-gateway` service account** — API token for the gateway to push
  Program B and for the labelling job to write Program C.
- **Supervisor/government role** — read DHIS2 dashboards + GIS.

## 5. Data flows

**Flow 1 · VHW health capture — pure DHIS2 config, no backend code.**
VHW logs into the (forked) Capture App → metadata syncs once, then works
offline → selects borehole org unit → fills Community Illness Report →
saved on-device → syncs to server when signal returns.

**Flow 2 · sensor → gateway → DHIS2.**
1. Borehole POSTs raw JSON + `X-Device-Secret` to `gateway/ingest` (existing
   contract).
2. Gateway validates, writes raw reading to Postgres.
3. Scheduled aggregation builds the per-(station, day) feature summary.
4. Gateway pushes it as a Water Quality Summary event (DHIS2 events endpoint,
   authenticated as `sensor-gateway`).
5. **Idempotency:** deterministic per-(station, day) key checked before insert.

**Flow 3 · labelling job.**
1. Poll DHIS2 for new Community Illness Report events (`lastUpdated` watermark).
2. For each, compute window `[report_time − 7d, report_time]`; fetch Water
   Quality Summary events at the same borehole in that window.
3. Apply the trailing-window rule → write a Reading Label event referencing the
   triggering report UID.
4. **Idempotency:** check for an existing label event keyed on the triggering
   report UID before inserting — the DHIS2 analogue of
   `UNIQUE(reading_id, report_id)`.

**Flow 4 · community-facing read (forked app).**
App queries DHIS2 for the latest Reading Label event at the user's borehole org
unit → maps label/severity to a treatment recommendation → renders status +
advice in a low-literacy, multilingual screen.

## 6. Project layout

```
App/dhis2/
├── README.md                   # records pinned upstream Capture App tag/commit
├── docker-compose.yml          # local DHIS2 + Postgres + gateway for dev
├── gateway/                    # new Flask service (own Railway deploy)
│   ├── app.py                  #   /ingest (device-auth, unchanged contract)
│   ├── aggregate.py            #   per-(station,day) summary features
│   ├── dhis2_client.py         #   DHIS2 Web API client (auth + event push)
│   ├── labelling.py            #   trailing-window rule adapted from labels.py
│   └── store.py                #   raw telemetry in Postgres
├── metadata/                   # DHIS2 config-as-code (importable JSON)
│   ├── org_units.json
│   ├── program_illness.json
│   ├── program_water.json
│   ├── program_label.json
│   └── users_roles.json
└── tests/
```

The forked Capture App lives in its own repo/checkout (it is a large Gradle
project); `dhis2/README.md` records the upstream tag it was branched from and a
pointer to that checkout.

## 7. Forked Capture App — approach and maintenance

The fork serves all four drivers: branding (resources + Gradle flavor),
low-literacy custom UI (edit/replace screens, reuse `en/sn/nd` catalogs),
learning (real production codebase), and the user-facing status/advice screen
(new, has no stock equivalent).

**Maintenance discipline (manages the accepted costs):**
- Record the exact upstream tag/commit the fork branched from in
  `dhis2/README.md`.
- Keep customisations in clearly-marked files/modules so future upstream merges
  stay localised.
- Treat APK size as a tracked metric (rural low-bandwidth deployment).

## 8. Phased build, testing, risks

### Phases (none gated by 2026-06-11 — the frozen demo is the hedge)

1. **Server** — DHIS2 in Docker; import `metadata/`. Unblocks everything.
2. **Gateway + labelling** — ingest → aggregate → push; labelling writes labels.
   Testable with zero Android work.
3. **Fork baseline** — clone, pin & document upstream version, build unmodified
   APK, point at our instance, confirm sync. Prove the toolchain first.
4. **Brand + status screen** — theme; add the user-facing status/treatment
   screen against real label data.
5. **Low-literacy multilingual polish** — iterate the custom UI.

### Testing

- **Gateway/labelling** — pytest against local Postgres + a disposable DHIS2
  (or mocked Web API client). Assert idempotency explicitly (re-runs create no
  duplicate events).
- **Metadata** — smoke test that `metadata/*.json` imports cleanly into a fresh
  DHIS2.
- **Forked app** — keep the upstream test suite green on the baseline build; add
  focused tests around the new status/treatment screen only.

### Risks

- **Android toolchain time-sink** — Phase 3 (clean baseline build) is the most
  likely place to lose days; do it before any customisation.
- **Upstream drift** — the fork ages; mitigated by documenting the branch point
  and localising changes. Standing maintenance cost, accepted.
- **Two-system identity drift** — `station_id` must stay consistent across
  Postgres ↔ DHIS2 org units; gateway treats DHIS2 org-unit identity as source
  of truth.
- **Reused-but-frozen code** — `labels.py` is *copied* into
  `dhis2/gateway/labelling.py`; a fix to one will not propagate to the other.
  Accepted given the deliberate separation.
- **DHIS2 write-path version dependence** — older instances use
  `POST /api/events`, newer (2.36+) prefer the tracker importer
  `POST /api/tracker`. Pin a DHIS2 version in `docker-compose.yml`; target one
  contract in `dhis2_client.py`. Exact version confirmed at planning.

## 9. Out of scope (explicitly deferred)

- Impilo / national-HIE integration and any FHIR export seam (D7).
- Twilio SMS leg (stays only in the frozen demo; not reimplemented here).
- Server-side ML model training (unchanged from `CLAUDE.md`: runs later, once
  labelled windows accrue).
- Twilio webhook signature validation, federated learning / differential
  privacy — relevant to the broader programme, not this build.

## 10. Open items to resolve at planning

- Exact DHIS2 version to pin.
- Treatment-recommendation mapping home (app constant vs DHIS2 option set).
- Aggregation schedule/trigger (cron vs on-ingest) and the daily-summary feature
  list final form.
- Whether the forked app lives in a sibling directory, a submodule, or a
  separate repo referenced from `dhis2/README.md`.
