# PLAN_v1.md — Archived (phase 1)

> **Week 1, Archived 2026-05-27.** This is the original 10-day plan for an on-device TinyML classifier trained on the four pre-existing datasets. It was archived after the team documented the shortcomings of the datasets described in "issues/issues_v2.md". 
>
> The current plan lives in "PLAN.md_v1". The pivot rationale lives in "App/cholera_sensor_ml_approach.md"
>

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

### Day 2 — Baseline models and the validation harness
- **Tasks:** Build the grouped/temporal CV harness (split by `site_id` + time). Train baselines: majority-class floor, logistic/ordinal regression, single decision tree. Establish honest baseline metrics (per-class recall, macro-F1, confusion matrix, **not** accuracy alone). Train an XGBoost model on "full_dataset.csv" and evaluate its performance. 
- **Output:** `baselines/` with reproducible metrics; the metric dashboard. A trained XGBoost classifier and its resulting performance on the "full_dataset.csv" test split. 
- **Gate:** Confirm models beat the majority-class floor on minority (unsafe-band) recall — if not, revisit features/targets.

## Pivot: From ML prediction to data collection

It is a good thing we frontloaded the data evaluation and model performance. After these initial steps, we realised that there were no publicly available datasets of sufficient quality and parametric measurement to train an appropriate algorithm for our objective. As such, we now seek to deploy a product which will compile water sensor data and illness reports to enable future ML approaches. See "Plan_v2" for our next steps. 
