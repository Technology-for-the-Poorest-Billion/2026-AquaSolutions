# CLAUDE.md

Guidance for future Claude sessions working in this repo. Read this first.

## What this project is

A 10-day GM2 ("Technology for the Poorest Billion") undergraduate sprint with industry partner Allen Chafa (Africa Prize 2023). The deliverable is a **TinyML classifier that runs on a low-cost microcontroller and predicts an E. coli risk band from cheap field-measurable water-quality sensors** (pH, temperature, turbidity, optionally DO/BOD/ammonia). Intended use: community-borehole monitoring in Zimbabwe.

## Source of truth

- `PLAN.md` — the 10-day plan and all locked decisions. Reference it by section; do not re-derive strategy from scratch.
- `ISSUES.md` — risk register. Most failure modes are already enumerated; check before claiming a concern is novel.
- `Data/Data.md` — dataset provenance and source URLs.
- `Meetings/` — stakeholder context from Chafa, Allen, Bashford.
- `Research/Notes.md` — literature digest including Chafa's prior fuzzy-logic architecture.

## Non-negotiable framing

**This is an E. coli / faecal-contamination risk classifier used as a cholera-*risk* proxy. It is NOT a cholera detector.** No dataset in this repo measures *V. cholerae*. Never describe outputs as "cholera detection" in code, comments, the model card, or commit messages. If the user phrases a request as "cholera detection," correct the framing rather than going along with it. See ISSUES.md §A1.

## Key data facts (do not re-discover)

- **`full_dataset.csv` is the only dataset with a microbial label.** The other three (`Combined_dataset.csv`, `WQD.csv`, `water_potability (1).csv`) measure unrelated targets (CCME index, fish-pond class, binary potability). Never silently use them as pathogen labels.
- **Common feature across all four datasets: pH only.** Turbidity + temperature appear in three of four. DO/BOD/ammonia in two.
- **`WQD.csv` turbidity is in cm (Secchi/transparency), not NTU.** These are NOT linearly convertible. Keep separate or drop — do not invent a conversion.
- E. coli counts span 0–50,000,000 /100 mL; ~95% of `risk_drinking_no_treatment` labels are "HIGH". Always report **per-class recall and macro-F1**; raw accuracy is misleading here.
- Validation protocol: **grouped + temporal split by `site_id` and date.** A random split leaks repeated readings from the same site and massively inflates accuracy.

## Conventions

- Canonical units: temperature °C, concentrations with the per-100 mL vs per-L convention stated explicitly. Per-100 mL → per-L conversion is ×10, applied only at the labelled boundary.
- Carry a `provenance` column on any combined table so dataset-identity artefacts are detectable.
- Drop rows missing the *label*; median/KNN-impute *predictors* with explicit missingness-indicator features. Never impute the target.

## Deployment guardrails

- **Prefer feature selection over PCA for the shipped model.** PCA components still require sensing every raw input → no BOM saving on the device. PCA is for EDA/visualisation only.
- Hardware budget: Cortex-M0+ / ESP32 class, ≤32 KB model flash, ≤8 KB RAM. Lock concrete numbers before model selection, not after.
- Defer the TinyML toolchain choice (TFLite-Micro vs `emlearn` / `m2cgen`) until the winning model family is known — see PLAN.md Day 7.
- Evaluate the **quantised** model specifically; int8 quantisation can disproportionately hurt minority-class recall. Compare float vs int8 confusion matrices and re-tune thresholds post-quantisation.
- Required output state: **abstain / "send sample to lab"** when input is out of training range. No silent extrapolation.

## Stakeholders and deadlines

- **Allen Chafa** — industry partner, Zimbabwe boreholes.
- **Dr Bashford, Dr Lara Allen** — academic supervisors (see `Meetings/`).
- Interim presentation: **2026-06-01**. Submission: **2026-06-11**.

## Working notes

- The repo uses Git LFS for large datasets (`.gitattributes`). Do not commit large CSVs without confirming LFS handling.
- `WNTR/` is a vendored copy of EPA's Water Network Tool for Resilience, earmarked as a pre-hardware simulator. Not yet integrated; treat as a library, not project code.
- `.venv/` is the local Python environment. Do not commit changes to it.
