# PLAN_v1.md — Archived (phase 1)

> **Week 1, Archived 2026-05-27.** This is the original 10-day plan for an on-device TinyML classifier trained on the four pre-existing datasets. It was archived after the team documented the shortcomings of the datasets described in "issues/issues_v2.md". 
>
> The current plan lives in "PLAN.md_v1". The pivot rationale lives in "App/cholera_sensor_ml_approach.md"
>
> Material still load-bearing from this document:
> - The four-dataset audit (§0 table) and the honest-framing block — both folded into "Claude.md" - "Key facts" and "Non-negotiable framing."
> - The validation protocol (grouped + temporal split by `site_id` and date) — carried into "issues_v3.md".
> - The ML pipeline discipline (imbalance-aware metrics, no PCA for the shipped model, abstain state on OOD inputs) — carried into "Claude.md" - "ML pipeline discipline."
>
> Everything specifically about on-device TinyML deployment (Day 7 toolchain choice, int8 quantisation, Cortex-M0+ budgets) no longer applies — the sensor is now a data-collection node, not an inference node. However, this document could still prove to be very useful if Aqua Solutions returns to an ML approach after appropriate data collection. 

---

# PLAN.md — TinyML Classifier for Waterborne Pathogen Risk (E. coli / Cholera) — ARCHIVED phase-1 plan

## 0. Goal and honest framing

**Objective:** Train a TinyML classification model that predicts the *presence and quantity (per litre)* of *E. coli* or *Cholera* (*Vibrio cholerae*) from low-cost, sensor-measurable water-quality parameters, such that it can run on a microcontroller in the field.

**What the data actually supports.** Before committing to the objective above, the plan must reckon with what the four datasets contain. A quick audit returns the forecasted challenges outlined under "issues/issues_v1.md".

**Revised, defensible objective for the 10 days:** a TinyML model that ingests the field-measurable parameters available on cheap sensors (pH, temperature, turbidity, and where a richer sensor stack exists, DO/BOD/ammonia) and predicts an **E. coli risk band** (a WHO-aligned ordinal scale, e.g. <1, 1–10, 11–100, 101–1000, >1000 per 100 mL) as a proxy for faecal contamination and waterborne-disease risk. Per-litre quantity is reported as the band midpoint (×10 to convert /100 mL → /L) with an explicit uncertainty caveat. A second, optional output head provides a coarse "general water quality" classification trained on the other datasets.

---

## 1. Decisions to be made

These are flagged here because they should be settled *early*. Documenting such decisions also allows future contributors to this project to revise potential shortcomings in the product's deployment and propose improvements. 

1. **Target definition.** Per-litre regression vs. ordinal risk bands vs. binary safe/unsafe.
   *Decision:* ordinal risk bands aligned to WHO E. coli categories (the dataset's own `risk_*` columns are derived from these), with per-litre quantity reported as a banded estimate. Rationale: the eight-order-of-magnitude spread and heavy right-skew make point regression unreliable on an MCU, and bands map directly to public-health action.
2. **Which datasets supply labels.** Pathogen classifier can *only* be supervised by `full_dataset.csv`. *Decision:* train the pathogen head on `full_dataset.csv`; use the other three to learn more about the relationships between proxies, to predict other water quality parameters (e.g. CCME_WQI), and to validate the obtained results. 
3. **Common feature set.** The intersection across *all* datasets is essentially **pH only** (turbidity and temperature appear in three of four). *Decision:* define **two feature tiers** — a *minimal tier* (pH, temperature, turbidity) that every cheap sensor node can supply and that `full_dataset.csv` supports directly, and a *rich tier* (adds DO, BOD, ammonia/nitrogen, nitrate) for nodes with a fuller sensor stack. While these parameters are part of some of the datasets, we still need to determine whether they can be cheaply measured. 
4. **Unit and schema standardisation.** Differing column names, units (Turbidity in cm vs NTU; concentrations /100 mL vs /L), and conventions. *Decision:* a single canonical schema, with all loaders mapping into it. Turbidity-in-cm (Secchi-style) is **not** linearly convertible to NTU and must be handled as a separate feature. 
5. **Model family for TinyML.** Decision tree / gradient-boosted trees vs. tiny MLP vs. logistic/linear. *Decision:* start with a small gradient-boosted tree or a depth-limited decision tree (interpretable, quantises well, tiny footprint), benchmark a 1–2 hidden-layer MLP. Keep logistic regression as the floor baseline. Need to test a variety of algorithms to define the most per
6. **Imbalance handling.** ~95% HIGH risk. *Decision:* class weights and/or focal loss, threshold tuning, and report per-class recall. These are more advanced ML techniques for dealing with the dataset's skewness. However, we need to research them further to understand how they work. 
7. **Deployment toolchain.** TensorFlow Lite for Microcontrollers vs. micromlgen/emlearn (for trees) vs. Edge Impulse. *Decision:* if a tree model wins, `emlearn`/`m2cgen` produce trivial C; if the MLP wins, TFLite-Micro with int8 quantisation. Decide which library to go with only after having tested various approaches. 
8. **Target hardware budget.** Flash/RAM/latency ceiling. *Decision:* fix a concrete budget after having validated the ML approach. If it turns out a bigger model is needed, the device can be configured to this task. However, it would affect the cost of the device and how it is deployed. 
9. **Validation protocol.** Random split vs. grouped/temporal split. *Decision:* **grouped split by `site_id` and time** in `full_dataset.csv` to avoid leakage from repeated measurements at the same monitoring station. A random row split here would overstate accuracy due to correlation between data points.

---

## 2. Ten-day plan

The plan front-loads data reconciliation, because if the "issues/issues_v1.md" dilemmas are real, a decision needs to be made quickly on the future of this approach. Each day lists **objective → tasks → output → decision/gate** (if there are any).

### Day 1 — Audit, scoping, and the honest-target decision
- **Tasks:** Profile every dataset (row counts, missing values, ranges, target distributions). Only "full_dataset.csv" carries a microbial quantity. Quantify E. coli skew and risk-class imbalance.
- **Output:** "data_audit.md" + the explicit revised objective (E. coli risk-band proxy, not literal cholera detection).

### Day 2 — Canonical schema and unit standardisation
- **Tasks:** Define one canonical schema (snake_case names, SI-ish units, explicit per-100 mL vs per-L convention). Build a unit registry. Write per-dataset loaders that map raw → canonical, flagging un-mappable columns (e.g. turbidity-cm vs NTU) rather than coercing them. Record provenance (source dataset) as a column.
- **Output:** `schema.yaml`, `loaders.py`, a reconciled `canonical_*.parquet` per dataset.
- **Decision:** Final common-feature tiers (minimal vs rich) locked.

### Day 3 — Cleaning, imputation, and label engineering
- **Tasks:** Handle missingness (17.7% of E. coli rows are blank; potability pH has gaps). Decide drop-vs-impute per column (recommend: drop rows missing the *label*; median/KNN-impute predictors with missingness flags). Engineer the ordinal E. coli risk-band target from `ecoli_per_100ml` using WHO-aligned cut points; derive the auxiliary general-quality target from the other datasets. Log-transform skewed predictors and the count.
- **Output:** `clean.py`, labelled modelling table for the pathogen head, separate table for the auxiliary head.
- **Gate:** Final target encoding agreed and frozen.

### Day 4 — EDA and dimensionality reduction
- **Tasks:** Correlation matrix, mutual information and ANOVA F-scores between predictors and the risk band, tree-based importances, and PCA *for visualisation only*. Identify the 3–6 most informative field-measurable parameters. Cross-check against domain literature (pH, temperature, turbidity, DO, BOD, ammonia are the physically plausible indicators of conditions favouring faecal bacteria).
- **Output:** `feature_analysis.md` with ranked features and the agreed shipped feature set.
- **Decision:** Final feature set for the minimal-tier (TinyML) model.

### Day 5 — Baseline models and the validation harness
- **Tasks:** Build the grouped/temporal CV harness (split by `site_id` + time). Train baselines: majority-class floor, logistic/ordinal regression, single decision tree. Establish honest baseline metrics (per-class recall, macro-F1, confusion matrix, **not** accuracy alone).
- **Output:** `baselines/` with reproducible metrics; the metric dashboard.
- **Gate:** Confirm models beat the majority-class floor on minority (unsafe-band) recall — if not, revisit features/targets.

### Day 6 — Primary model development
- **Tasks:** Train and tune the candidate TinyML models on the minimal feature tier: depth-limited tree, gradient-boosted trees, tiny MLP. Apply imbalance handling (class weights / focal loss), tune decision thresholds toward high recall on unsafe bands. Optionally train the rich-tier stretch model.
- **Output:** Trained candidate models + comparison table (accuracy is reported but ranking is by macro-F1 and unsafe-band recall under the budget).
- **Decision:** Select the winning model family.

### Day 7 — Compression and TinyML conversion
- **Tasks:** Apply the matching toolchain — int8 post-training quantisation (TFLite-Micro) for the MLP, or `emlearn`/`m2cgen` C export for the tree. Prune/limit depth to fit the flash/RAM budget. Measure footprint and inference latency on the target MCU class (or an emulator).
- **Output:** Quantised model artifact + generated C, plus a footprint/latency report.
- **Gate:** Model fits the Day-1 hardware budget. If not, iterate on depth/width or feature count.

### Day 8 — On-device validation and accuracy-vs-size trade-off
- **Tasks:** Evaluate the *quantised* model (quantisation can shift minority-class recall). Compare float vs int8 confusion matrices. Run on the actual board if available; otherwise a faithful emulator. Profile worst-case latency and memory.
- **Output:** `deployment_eval.md` documenting the accuracy lost to quantisation and the final operating thresholds.
- **Decision:** Accept the trade-off or roll back to a larger-but-still-feasible config.

### Day 9 — Robustness, calibration, and field-condition stress tests
- **Tasks:** Sensor-noise injection (simulate cheap-sensor error on pH/turbidity/temp), out-of-distribution checks (inputs outside training ranges → must abstain/flag, not silently extrapolate), probability calibration, and a clear "uncertain / send sample to lab" output state. Sanity-check the per-litre quantity estimates (band midpoint × 10) against physical plausibility.
- **Output:** robustness report; abstention/uncertainty logic specified.
- **Gate:** Model degrades gracefully under realistic sensor noise.

### Day 10 — Packaging, documentation, and handover
- **Tasks:** Freeze the model, write the model card (intended use, the cholera-proxy limitation stated prominently, performance per class, known failure modes), reproducible training pipeline, and the firmware integration notes. Final demo.
- **Output:** `model_card.md`, packaged artifact, reproducible pipeline, README, and a short "what we'd do with more time / more data" section.
- **Gate:** Handover review.

---

## 3. Standardisation strategy (the specific concern raised)

The team correctly identified three reconciliation problems. The plan handles each as follows:

- **Different columns.** Map all sources into one canonical schema (Day 2). Where a predictor exists in only some datasets, it stays available for the rich-tier model but is excluded from the minimal TinyML feature set. Provenance is tracked so multi-dataset training never hides which rows could carry a real label.
- **Different units.** A unit registry performs explicit, documented conversions (e.g. temperature already in °C everywhere; concentrations normalised to a stated per-100 mL or per-L convention). **Non-convertible** quantities — notably Turbidity in cm (transparency/Secchi-style) vs NTU (nephelometric) — are *not* force-converted; they are kept as distinct features or dropped, with the decision logged. This avoids manufacturing a false equivalence.
- **Different quality measures (the target mismatch).** This is the deepest issue and is handled by the **multi-target / multi-head framing**: the *pathogen* target comes only from `full_dataset.csv`'s E. coli counts (banded); the other datasets' targets (potability, fish-pond class, CCME_WQI) are *not* harmonised into one number — instead they feed a separate auxiliary "general quality" task and unsupervised pre-training. We explicitly **do not** invent a single synthetic "water quality" label spanning all four datasets, because their definitions are physically different and merging them would inject label noise.

## 4. Dimensionality reduction strategy (the specific concern raised)

Use a *consensus of methods* (Day 4) rather than one technique: correlation pruning, mutual information / ANOVA F-test, tree-based importance, and PCA. **For the shipped model, prefer feature *selection* over feature *projection* (PCA):** on a microcontroller, a PCA component still requires every raw input to be sensed, so it does not reduce the sensor cost or the on-device compute the way dropping a feature does. PCA is therefore used for understanding structure and visualising redundancy, while the final 3–6 features are chosen by selection so the deployed node only has to carry the cheapest, most informative sensors.

## 5. Definition of done

- A quantised TinyML model running within the agreed flash/RAM/latency budget, predicting E. coli risk bands (with banded per-litre estimates) from minimal field-measurable inputs.
- Honest, per-class metrics (macro-F1 and unsafe-band recall foregrounded; raw accuracy de-emphasised), reported on a leakage-free grouped/temporal split.
- A model card stating the cholera-proxy limitation and out-of-distribution behaviour prominently.
- A fully reproducible pipeline from raw CSVs to deployed C/TFLite artifact.
