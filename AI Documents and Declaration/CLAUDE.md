# CLAUDE.md

Guidance for future Claude sessions working in this repo. Read this first.

## What this project is

A GM2 ("Technology for the Poorest Billion") undergraduate sprint with industry partner Allen Chafa (Africa Prize 2023). The project **pivoted in late May 2026** away from "ship a TinyML classifier trained on existing datasets" toward a **two-leg data-collection system** whose ML lives on a server and trains *once labelled data accrues*:

- **Sensor leg** — a low-cost field node measures rainfall, water temperature, and a turbidity/plankton/chlorophyll proxy, and POSTs readings to a central Flask server. The node does **not** run inference; it is a data-collection endpoint, not a TinyML node.
- **Reporting leg** — community members text a station number to a Twilio phone number when illness is suspected. The Flask server parses the SMS, labels the trailing window of sensor readings at that station as *unsafe*, and auto-replies. This is how the system generates training labels for the model that will be trained later.

Generation 1 is therefore **plumbing + label generation, not live inference.** The ML pipeline (server-side, not on-device) only runs once labelled windows have accumulated.

## Source of truth

Read these in this order. Each supersedes the older docs it points back to.

- `PLAN.md` — the current v2 plan for the application-layer + comms build, against the 2026-06-01 interim presentation and 2026-06-11 submission. Reference by section; do not re-derive strategy.
- `App/cholera_sensor_ml_approach.md` — the pivot rationale. Read this if the user's request seems to assume the old TinyML approach.
- `App/sms_to_sqlite_plan.pdf` — backend implementation spec for the Generation-1 SMS-to-SQLite pipeline.
- `App/Ideation.md` — early sketch of the user-facing application layer (multi-language, low-literacy UI, treatment recommendations, technician notification). Aspirational; not yet implemented.
- `issues_v3.md` — **current** risk register for the application + communications + linkage phase.
- `issues_v2.md` — *dataset-level* issues from phase 1. Still valid as the explanation of why the original approach hit a predictive ceiling.
- `ISSUES_v1.md` — archived risk register from phase 1. Read only for historical context.
- `PLAN_v1.md` — archived 10-day TinyML plan. Read only for historical context.
- `Meetings/` — stakeholder context from Chafa, Allen, Bashford.
- `Research/Notes.md` — literature digest including Chafa's prior fuzzy-logic architecture.

## Non-negotiable framing

**This system measures faecal-contamination indicators and outbreak-conducive conditions, plus collects community illness reports. It is NOT a cholera detector and the sensor cannot identify *Vibrio cholerae*.** *V. cholerae* requires culture and serotyping; no cheap probe measures it. Never describe outputs as "cholera detection" in code, comments, model cards, or commit messages. If the user phrases a request as "cholera detection," correct the framing rather than going along with it.

This was the single biggest risk under phase 1 and remains so — see `App/cholera_sensor_ml_approach.md` §2 and `issues_v3.md`.

## Key facts (do not re-discover)

- **Phase-1 datasets are proxy/pre-training resources only.** `full_dataset.csv` (DWS South Africa) has E. coli labels but no linked health outcomes. The other three (`Combined_dataset.csv`, `WQD.csv`, `water_potability (1).csv`) measure unrelated targets (CCME index, fish-pond class, binary potability) and **cannot** supply pathogen labels. See `issues_v2.md` for the full dataset critique.
- **Phase-1 predictive ceiling:** pH + turbidity + temperature on `full_dataset.csv` gave macro-F1 ≈ 0.32 vs a 0.32 dummy baseline under a proper grouped + temporal split. This is a data-information ceiling, not a tuning problem — see `issues_v2.md` §6.2. It is the empirical reason the project pivoted to collecting its own purpose-built data.
- **The new labelling unit is the trailing 7-day window** per (station, date), not per-row. Aggregate sensor readings over the window into features: means, peaks, rate-of-change, days-above-threshold. Cholera has an incubation period of hours to ~5 days; contamination is a process, not an instant.
- **Keep both classes when sampling.** Do NOT discard non-event windows — that deletes the negative class and the imbalance "vanishes" only because the problem vanishes.
- **Validation protocol:** grouped + temporal split (by site and date). A random split leaks correlated repeated readings.

## ML pipeline discipline (when ML eventually runs)

These rules come from `App/cholera_sensor_ml_approach.md` §6 and `Research/Notes.md`. They apply to the server-side model that will be trained on collected data.

- **Outlier removal first**, *before* any resampling, so synthetic points are not generated around mis-labelled or anomalous observations.
- **Resample (ADASYN / class-weighting) on the training fold only**, inside cross-validation. Never on the test set. Suspiciously high published scores (e.g. 99.6% accuracy in the CORP paper) are usually resampling-leakage artefacts — guard against this from day one.
- **Matched case–control sampling** for negatives — same sites and same seasons as positives — so the model doesn't learn "rainy season = case" instead of water-chemistry signal.
- **Model ladder:** Negative Binomial regression (interpretable baseline) → Random Forest / XGBoost with SHAP → LSTM for 7–14 day temporal forecasting.
- **Imbalance-aware metrics:** balanced accuracy, macro-F1, positive-class sensitivity/recall, PR-AUC. **Never** raw accuracy.
- **Label noise is structural**, not a bug to fix: SMS reports give a person and an approximate onset, not a guaranteed source or exposure moment, and unreported illness means some "negative" windows contain unobserved positives. The pipeline must be robust to this.

## Conventions

- Canonical units: temperature °C; concentrations with the per-100 mL vs per-L convention stated explicitly. Per-100 mL → per-L conversion is ×10, applied only at the labelled boundary.
- Carry a `provenance` column on any combined table so dataset-identity artefacts are detectable.
- Drop rows missing the *label*; median/KNN-impute *predictors* with explicit missingness-indicator features. Never impute the target.
- `WQD.csv` turbidity is in cm (Secchi/transparency), not NTU — NOT linearly convertible. Keep separate or drop; do not invent a conversion.

## Application-layer guardrails

- The current build target is in `App/backend/` — a Flask + SQLite + Twilio stack. Local dev uses ngrok for the Twilio webhook; Railway is the eventual deploy target.
- **Twilio webhook signature validation must be on** for any internet-exposed deployment. Without it the `/sms` endpoint can be spoofed by anyone who knows the URL.
- The `/ingest` sensor endpoint authenticates with a shared `DEVICE_SECRET` header. Treat the secret as production-equivalent: never commit it, rotate if exposed.
- Required output state on any future inference: **abstain / "send sample to lab"** when input is out of training range. No silent extrapolation. The user-facing app must also surface this state honestly (see `App/Ideation.md`).
- Federated learning + differential privacy is the structural answer to cross-border patient-data governance (see `App/cholera_sensor_ml_approach.md` §4). Don't design the pipeline as if all raw data will live in one place.
- The Railway deploy uses Postgres (provisioned as a Railway service). Local
  dev and the pytest suite use SQLite via the engine module's DATABASE_URL
  fallback. All DB code goes through SQLAlchemy Core text() with named
  parameters so the same SQL runs on both backends. Do not reintroduce raw
  sqlite3 calls in request-path code; feature_engineering.py is the only
  remaining sqlite3-only consumer and is offline-only.

## Site framing

The pilot site is **deliberately not locked** in this document. The Bengal Delta (with icddr,b as the surveillance partner) is the strongest candidate on data-density and predictability grounds; Sub-Saharan settings including Chafa's Zimbabwe boreholes remain the eventual deployment ambition, reached via transfer learning. The decision waits on confirmation of the linkage partner.

## Stakeholders and deadlines

- **Allen Chafa** — industry partner (Africa Prize 2023), originator of the Zimbabwe-borehole deployment ambition.
- **Dr Bashford, Dr Lara Allen** — academic supervisors (see `Meetings/`).
- Interim presentation: **2026-06-01**. Submission: **2026-06-11**.

## Working notes

- The repo uses Git LFS for specific large datasets (see `.gitattributes`). The currently-tracked LFS files are `Data/Datasets/Combined_dataset.csv` and `Data/Datasets/GFQA_v3.zip`. Do not commit large CSVs without confirming LFS handling.
- `WNTR/` is a vendored copy of EPA's Water Network Tool for Resilience, earmarked as a pre-hardware network simulator. Not yet integrated; treat as a library, not project code.
- `.venv/` is the local Python environment. Do not commit changes to it.
- Phase-1 ML notebooks live in `ML/`. They are evidence for the predictive-ceiling finding, not the deliverable.
- The Flask app's UI is internationalised (en/sn/nd, framework supports
  all 16). Translation catalogs live in `App/backend/translations/`. If
  you edit a `.po` file, run `make i18n-compile` from `App/backend/`
  before restarting Flask or the change won't take effect. The
  `#, fuzzy` flag means "machine-translated, not yet native-reviewed";
  removing it from a catalog entry promotes that translation to verified.
  Known caveat: `App/scripts/translate_po.py` does not yet protect format
  placeholders (`{role}`, `%(station_id)s` etc.) — they get translated
  along with surrounding words and break `.format()` / `%`-substitution
  if not manually restored after a re-translation. See
  `docs/superpowers/specs/2026-05-30-i18n-design.md` for the full design.
