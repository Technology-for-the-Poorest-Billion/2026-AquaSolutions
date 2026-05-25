# CCME WQI Proof-of-Concept — Design Spec

**Date:** 2026-05-25
**Status:** Draft, awaiting user review
**Scope:** Single proof-of-concept ML pipeline. Not the project's TinyML pathogen-classifier deliverable.

## 1. Goal

Train an ML regression model that predicts the **CCME Water Quality Index (numeric 0–100 score)** from the chemistry features in `Data/Combined_dataset.csv`. The purpose is to verify that a sensible ML pipeline can be built and trained on this data — the pipeline is the deliverable, not the model itself.

A near-perfect R² is the *expected* outcome (the CCME WQI is a deterministic formula of these inputs) and is therefore not the success criterion on its own. Honest stratified metrics are.

## 2. Non-goals (explicit)

- Not the pathogen / E. coli risk-band model (that is the main project track, scoped in `PLAN.md`).
- Not a TinyML deployment artifact — no quantisation, no MCU export.
- Not a model that uses geography, area, or date. Chemistry only.
- Not a hyperparameter-tuning study. Sklearn defaults are deliberate.
- No new heavy dependencies. Pandas + scikit-learn + matplotlib only.

## 3. Data

### Source
- `Data/Combined_dataset.csv` — 2,827,977 rows, 15 columns (Country, Area, Waterbody Type, Date, 7 chemistry features, Nitrogen, Nitrate, `CCME_Values`, `CCME_WQI`).

### Target
- **Primary (regression):** `CCME_Values` — numeric 0–100 CCME WQI score.
- **Secondary (banded view):** `CCME_WQI` — categorical label (Excellent ≥95, Good 80–94, Fair 65–79, Marginal 45–64, Poor <45). Derived from `CCME_Values` at the standard CCME thresholds.

### Features
The 8 numeric chemistry columns:
1. Ammonia (mg/l)
2. Biochemical Oxygen Demand (mg/l)
3. Dissolved Oxygen (mg/l)
4. Orthophosphate (mg/l)
5. pH (ph units)
6. Temperature (cel)
7. Nitrogen (mg/l)
8. Nitrate (mg/l)

(Earlier conversation framed this as "7 chemistry features" — that was an undercount. All eight columns are used.)

### Sampling
- **50,000 rows, stratified by `Country × Waterbody Type`**, proportional to each stratum's share of the full file. Goal: preserve the natural distribution while avoiding the "first-200k-rows-is-98%-England" artifact.
- Implementation: `pandas.read_csv` with `usecols=[Country, Waterbody Type, CCME_Values, CCME_WQI, <chemistry>]`, then `df.groupby(['Country','Waterbody Type'], group_keys=False).apply(lambda g: g.sample(frac=50_000/len(df), random_state=42))`.
- Fixed `random_state=42`. Sample state (row count per stratum) recorded in the notebook.

## 4. Architecture

```
GM2_Aqua_Solutions/
├── ML/
│   ├── 01_ccme_wqi_poc.ipynb         ← the POC notebook
│   └── specs/
│       └── 2026-05-25-ccme-wqi-poc-design.md   ← this file
└── Data/
    └── Combined_dataset.csv          ← unchanged
```

Single notebook, no separate `src/` package. If the pathogen model later reuses any of this code, refactor at that point — not now.

## 5. Notebook structure

Sections in order:

1. **Setup** — imports, fixed seed, paths.
2. **Load & stratified sample** — produces the 50k DataFrame; prints stratum counts.
3. **EDA** —
   - Summary stats for the 8 chemistry features and `CCME_Values`.
   - Class balance for `CCME_WQI` (after sampling).
   - Pearson correlation matrix of the 8 features (redundancy view).
   - Mutual information and Spearman correlation of each feature vs `CCME_Values` (predictive-relevance view).
   - PCA scree plot of standardised features — **labelled "for visualisation only; not used for input projection."**
4. **Train/test split** — 80/20 random, **stratified by `CCME_WQI` band** so all five bands appear in both halves.
5. **Models** — fit in order:
   - `LinearRegression` (floor baseline).
   - `RandomForestRegressor(n_estimators=200, max_depth=12, n_jobs=-1, random_state=42)`.
   - `HistGradientBoostingRegressor(max_iter=300, random_state=42)`.
   For each: 5-fold CV on the training half → mean ± std of MAE / RMSE / R².
6. **Evaluation** on the held-out 20%:
   - MAE, RMSE, R² overall per model.
   - **MAE stratified by true `CCME_WQI` band** (the honest view — aggregate MAE is dominated by the ~75% of rows that score 80–100).
   - **Banded confusion matrix**: bucket predictions at CCME thresholds (95/80/65/45), report 5×5 matrix + macro-F1.
   - **Permutation feature importance** (`sklearn.inspection.permutation_importance`) for the winning model.
7. **Summary & next steps** — markdown cell summarising what the experiment showed, with explicit acknowledgement that high R² is expected because the WQI is a learnable formula.

## 6. Success criteria

The POC is "green" if **all** of:

1. The notebook runs end-to-end on the 50k sample in under 60 s on a developer laptop.
2. Random Forest **and** Histogram Gradient Boosting both beat `LinearRegression` on R² by a meaningful margin. Anticipated values: linear ~0.55–0.70, ensembles >0.90.
3. Stratified MAE is **reported per band** — Poor and Marginal in particular are not hidden inside an aggregate.
4. Banded confusion-matrix **macro-F1 ≥ 0.70** on the held-out set.
5. **Reproducibility:** restart kernel → run all → identical numbers (modulo seed).

If 1–3 pass but 4 fails, the POC is still informative — it would show that the regression recovered the score but the band-bucketing is lossy near the threshold boundaries. Report that honestly; do not retrain to chase the macro-F1 number.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Memory blow-up loading 2.8M rows. | `usecols=` to drop unused columns at read time; falls to ~600 MB. If still too big, switch to chunked read with per-chunk stratified sampling. |
| Stratified groupby produces near-empty strata for rare combinations (e.g., Canada × Coastal). | `frac=` sampling tolerates this gracefully — strata smaller than `1/frac` rows may contribute zero. Acceptable for a POC; documented in the notebook. |
| `CCME_Values` clipping at 100 induces a censored-target artifact (the model can't predict >100). | Out of scope to fix in the POC. Note it in the summary cell. |
| Sklearn's `HistGradientBoostingRegressor` defaults change between versions. | Pin `max_iter=300, random_state=42` explicitly; record `sklearn.__version__` in the notebook. |
| Notebook cell ordering bugs make it look reproducible when it isn't. | Reproducibility check (criterion #5 above) is a literal "restart-and-run-all" step before declaring success. |

## 8. Decisions made (for the record)

| Decision | Choice | Alternative considered |
|---|---|---|
| Target form | Regression on `CCME_Values`, banded view derived from predictions | Direct classification on the band; rejected because it discards distance-to-threshold information |
| Sample size | 50,000, stratified by Country × Waterbody Type | 10k (too small for Poor class); 200k (more than needed for a POC); full 2.83M (wasted compute) |
| Features | 8 chemistry columns only | + Waterbody / + Country / + month — all rejected to keep the test honest about "can chemistry predict the index" |
| Feature analysis | EDA (correlation, MI, Spearman, PCA-for-EDA), train on all 8, post-hoc permutation importance | PCA-then-project; rejected because PCA finds variance, not target relevance |
| Model family | Linear + RF + HistGBM in one notebook | Single GBM script; rejected to preserve the baseline-comparison narrative |
| Validation split | 80/20 random, stratified by band | Temporal split (pre-2015 / post-2015); deferred to follow-up |
| Deliverable | One notebook in `ML/` | `src/` package; rejected as premature for a POC |

## 9. Open questions

None blocking implementation. Items worth revisiting after the POC runs:

- Does the result depend strongly on the stratified-sample seed? (Re-run with two more seeds if results look unstable.)
- Does a temporal split materially change the picture? (Separate follow-up experiment.)
- Would including `Waterbody Type` as a feature meaningfully lift R²? (Ablation — useful only if the chemistry-only ceiling is unexpectedly low.)
