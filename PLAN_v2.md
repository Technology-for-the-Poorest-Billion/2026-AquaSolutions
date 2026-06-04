# PLAN.md — v2: Data-Collection Apparatus + Server-Side ML (deferred)

> v1 (the 10-day on-device TinyML plan) is archived in [`PLAN_v1.md`](PLAN_v1.md). The pivot rationale lives in [`App/cholera_sensor_ml_approach.md`](App/cholera_sensor_ml_approach.md). Read those two if any decision below seems to come out of nowhere.

## 0. Where we are and what we're building

The project is no longer "ship an on-device classifier trained on the existing datasets." After grouped + temporal evaluation, three-sensor classification on `full_dataset.csv` was indistinguishable from a majority-class dummy (macro-F1 ≈ 0.32, `issues_v2.md` §6.2). That ceiling is in the *labels*, not the *model* — none of the four phase-1 datasets pair sensor measurements with health outcomes.

The current build is a **two-leg data-collection system**:

- **Sensor leg.** A low-cost field node POSTs readings (pH, turbidity, temperature, rainfall) to a Flask `/ingest` endpoint, authenticated by a shared `DEVICE_SECRET`. Inference does not run on the node.
- **Reporting leg.** Community members text a station number to a Twilio phone number when illness is suspected. The Flask `/sms` webhook validates the Twilio signature, parses the station ID, retro-labels the trailing window of readings at that station as *unsafe*, writes an `illness_reports` row, and replies acknowledging receipt.

The server-side ML pipeline is **specified** (see "ML pipeline discipline" in `CLAUDE.md` and `App/cholera_sensor_ml_approach.md` §6) but **deferred** — it trains once labelled windows have accumulated. Until then, the pipeline is validated against a *proxy* dataset to demonstrate the imbalance-handling and leakage-avoidance discipline.

## 1. Deliverables

By 2026-06-11 the repo must contain:

1. **Working Gen-1 backend** — Flask + SQLite + Twilio + sensor `/ingest`, runnable locally with `ngrok` and (stretch) deployable to Railway.
2. **Sensor simulator** — a script that POSTs plausible readings on a cadence so the demo and the labelling pipeline have data to operate on.
3. **Debug dashboard** — recent sensor readings + recent SMS reports, side by side, auto-refreshing. Not user-facing; for supervisors and developers.
4. **Labelling logic** with a defensible trailing-window definition; full audit trail (which reading was labelled, by which report, with what window).
5. **ML pipeline validation on a proxy dataset** (e.g. `full_dataset.csv` or open California FIB) — windowed feature construction, matched case–control sampling, ADASYN-inside-CV resampling, model ladder (NB → XGBoost+SHAP → LSTM), imbalance-aware metrics. Demonstrates the eventual real pipeline works without claiming results on our (yet-uncollected) data.
6. **Model card / project write-up** that prominently states the cholera-proxy limitation, the ML-deferral framing, and the open linkage question.
7. **Risk register** — `issues_v3.md`, kept current.

## 2. Calendar

The project has fifteen days from today to submission. Two hard milestones drive the cadence: the **interim presentation on 2026-06-01** and the **final submission on 2026-06-11**.

### 2026-05-27 (today) — docs pivot + Gen-1 scaffold
- Update `CLAUDE.md` to reflect the pivot. **Done.**
- Archive `ISSUES.md` and `PLAN.md` as `ISSUES_v1.md` and `PLAN_v1.md`. **Done.**
- Write `issues_v3.md` covering phase-2 risks (Twilio abuse, linkage, label noise, etc.). **Done.**
- Scaffold `App/backend/`: `app.py`, `database.py`, `labels.py`, `sensor_ingest.py`, `requirements.txt`, `Procfile`, `.env.example`, `templates/dashboard.html`.
- Write `scripts/simulate_sensor.py` so the demo has live readings.
- Write `App/DEMO.md` walking through Twilio + ngrok setup for tomorrow.
- Gate: backend runs locally end-to-end on a stubbed `/sms` POST (no real Twilio yet).

### 2026-05-28 — live demo
- Provision Twilio trial account + phone number; install ngrok; configure webhook.
- Live walk-through: text the Twilio number with a station ID from a real phone, watch the dashboard update with the labelled readings + the new illness report.
- Capture a recorded screencast as a fallback in case the live demo breaks.

### 2026-05-29 to 2026-05-31 — harden the Gen-1 pipeline
- **Security.** Twilio request-signature validation (enabled, with the demo Auth Token); reject unsigned requests with 403. Sensor secret rotation procedure documented.
- **Abuse-resistance.** Per-phone-number SMS rate limit (default: 1 report per phone per 10 minutes). Twilio account spending cap set.
- **Consent.** STOP keyword honoured; auto-reply includes the minimal data-use statement.
- **Label audit trail.** When a report retro-labels readings, the labelling rule + window length are stored on the row, not implicit.
- **Provenance.** Every reading gets a `provenance` column (device-id, firmware version, network path placeholder); every report gets the parsed-station + raw-message + parser-version.
- **Multi-station parser.** Lenient parser logs rejections for human review.
- **Persistence sanity.** Decide whether SQLite file lives in repo (`App/backend/data/`) or external; back it up before any session that writes to it.

### 2026-06-01 — interim presentation
- Story: phase-1 ceiling → pivot → Gen-1 system → ML pipeline on proxy data → linkage question.
- Demo: as 2026-05-28, but with the hardening from the previous three days visible (rate-limiting, signature validation, audit trail).
- Open question for supervisors: linkage partner. Surface `icddr,b` as the lead candidate.

### 2026-06-02 to 2026-06-08 — ML pipeline + linkage outreach + user-facing UI sketch
- **ML pipeline on proxy data.** Implement the §6 pipeline against `full_dataset.csv` (or a public FIB dataset). Show: matched case–control sampling, ADASYN inside CV folds only, NB → XGBoost+SHAP → LSTM ladder, balanced/macro-F1/PR-AUC reporting. The point is *the pipeline is honest and reproducible*, not "we beat the literature."
- **Linkage outreach.** Draft and send a partner-inquiry note (icddr,b, possibly DWS-SA, possibly local Cambridge Global Health contacts). Outcome expected: a soft yes/no, not a signed agreement.
- **User-facing app sketch.** A separate page from the dev dashboard, modelled loosely on `App/Ideation.md`: shows the status of a station ("water at Station 4: contaminated reports in last 48h — boil before drinking"), in English first, with the multi-language hook stubbed. Explicitly *not* the production UI.
- **Federated-learning note.** Write a short design doc on how the pipeline becomes federated when a linkage partner is confirmed; do not implement.

### 2026-06-09 to 2026-06-10 — write-up + polish
- Model card. Prominent cholera-proxy limitation, intended use, known failure modes (label noise on time + source axes, under-reporting bias, predictor missingness, station-ID parsing errors), out-of-distribution behaviour, deferred-ML framing.
- README at repo root: 30-second pitch + how to run.
- Demo screencast re-recorded with the final UI.
- Final risk-register sweep (`issues_v3.md`).

### 2026-06-11 — submission
- Tag a release commit. Push. Submit.

## 3. Decisions still open

These need answers but are not blocking *today's* build. Recorded so they don't get lost.

1. **Pilot / deployment site framing.** The pivot doc recommends Bengal Delta (`icddr,b`) for data density and predictability. CLAUDE.md is currently *site-agnostic*. To be locked when a linkage partner responds.
2. **Database location.** `App/backend/data/water_safety.db` is the obvious default for local dev. Production needs either Postgres on Railway or persistent SQLite with a backup story. Decide when Gen-1 leaves local-only.
3. **User-facing language strategy.** Per `App/Ideation.md`, eventually multi-language. For Gen-1, English-only. Defer the language-detection / language-preference work.
4. **Treatment recommendations in the auto-reply?** Recommendation: **no** (legal exposure, see `issues_v3.md` §C6). Auto-reply is acknowledgement only; recommendations move to the user-facing app screen.
5. **Reporter phone-number hashing.** Recommendation: hash at rest, de-dup via the hash. Implement before any deployment outside the demo laptop.

## 4. Definition of done (per deliverable)

- **Backend:** `pytest` (if added) green; `/health` returns OK; `/sms` retro-labels readings and replies with a valid TwiML response; `/ingest` rejects unauthenticated and accepts authenticated payloads; `/dashboard` renders.
- **Sensor simulator:** runs for ≥1 hour without crashing, populates ≥720 readings across ≥4 simulated stations.
- **Dashboard:** auto-refreshes; shows both panes; renders correctly with zero rows, with mid-volume data, and with the demo's expected ~100 rows.
- **Labelling logic:** the chosen window definition is documented in `App/backend/labels.py`'s docstring, on the row's `label_source` field, and in this PLAN. An audit query reproduces "which readings were labelled by which report."
- **ML pipeline on proxy:** runs end-to-end against a checked-in proxy dataset, produces balanced-accuracy/macro-F1/PR-AUC for each rung of the ladder, and the README explains *why these numbers are not predictions about our real deployment*.
- **Risk register:** every item in `issues_v3.md` has at least an acknowledged mitigation, even if not implemented.

## 5. What we are explicitly NOT doing in Gen-1

To prevent scope creep and to keep `App/Ideation.md` aspirational:

- **No live inference.** No trained model running against incoming sensor data.
- **No multi-language UI.** English-only, with the hook stubbed.
- **No clinical-record linkage.** We do not touch patient data; we collect community-reported symptoms only.
- **No production deployment.** Railway is the stretch; the demo target is local + ngrok.
- **No treatment recommendations via SMS.** Acknowledgement only.
- **No on-device firmware or hardware build.** The sensor is simulated for Gen-1.
- **No federated-learning implementation.** Designed for; not built.

## 6. Pointers

- `CLAUDE.md` — top-level framing, non-negotiable rules, ML pipeline discipline.
- `App/cholera_sensor_ml_approach.md` — pivot rationale and ML pipeline reference.
- `App/sms_to_sqlite_plan.pdf` — backend implementation spec (Gen-1).
- `App/Ideation.md` — user-facing app vision (not Gen-1).
- `issues_v3.md` — current risk register.
- `issues_v2.md` — dataset-level critique from phase 1.
- `PLAN_v1.md`, `ISSUES_v1.md` — archived phase-1 docs, historical only.
