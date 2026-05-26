# Water Potability EDA + Classifier — Design Spec

**Date:** 2026-05-26
**Status:** Approved 2026-05-26
**Scope:** Single notebook combining EDA and a binary classifier on `Data/water_potability (1).csv`. Not the TinyML deliverable.

## 1. Goal

Characterise the Kaggle water-potability dataset and train a binary classifier (potable / not potable) using its full 9-feature set. The **strategic purpose** is to test whether more features break through the macro-F1 ≈ 0.45 plateau observed on `FirstGradBooster_v2.ipynb` with only three sensors (pH, turbidity, temperature). The notebook is the deliverable; the model's per-class metrics, compared cross-notebook against v2, are the experimental output.

## 2. Non-goals (explicit)

- Not the pathogen / E. coli model (that is the main project track on `full_dataset.csv`).
- Not a TinyML deployment artifact — no quantisation, no MCU export, no abstain state. The dataset has no field-deployment context.
- Not a hyperparameter-tuning study. Hyperparameters mirror v2 exactly to make the cross-notebook comparison apples-to-apples.
- Not a generalisation study — `water_potability (1).csv` has no `site_id` or `date`, so grouped / temporal splits are impossible. Reported metrics are upper bounds, not field-deployment estimates.

## 3. Data

### Source
- `Data/water_potability (1).csv` — ~3,276 rows, 10 columns (9 features + 1 binary label). Origin: Kaggle (`adityakadiwal/water-potability`). See `Data/Data.md`.

### Target
- `Potability` ∈ {0, 1}. 1 = potable, 0 = not potable. Expected ~61/39 class balance (much milder than `full_dataset.csv`'s 95/5).

### Features (9)
1. `ph`
2. `Hardness`
3. `Solids`
4. `Chloramines`
5. `Sulfate`
6. `Conductivity`
7. `Organic_carbon`
8. `Trihalomethanes`
9. `Turbidity`

`ph` and `Turbidity` overlap with the sensors Aidan's notebook uses on `full_dataset.csv` — this overlap is the basis for the cross-notebook comparison.

### Known data-quality issues
- ~30–40% missing values are expected in `Sulfate` and `Trihalomethanes` (documented Kaggle artefact). Confirm in Section 2 of the notebook before deciding on imputation.
- Some Kaggle copies of this dataset have unphysical values (e.g. pH < 0). Section 4 should flag these.

## 4. Architecture

```
GM2_Aqua_Solutions/
├── ML/
│   ├── water_potability_eda.ipynb         ← the new notebook
│   └── specs/
│       └── 2026-05-26-water-potability-eda-design.md   ← this file
└── Data/
    └── water_potability (1).csv           ← unchanged
```

Single notebook, no `src/` package. Matches the convention set by `FirstGradBooster_v2.ipynb` and the CCME WQI POC plan.

## 5. Notebook structure

| § | Cell type | Purpose |
|---|---|---|
| 1 | Setup | Imports, fixed seed (42), load `Data/water_potability (1).csv`. |
| 2 | Schema + missingness | Shape, dtypes, per-column null counts. Confirm or refute the ~30–40% Sulfate/Trihalomethanes missingness. |
| 3 | Class balance | `value_counts(normalize=True)` on `Potability`. Compare to `full_dataset.csv`'s 95/5 in a one-line print. |
| 4 | Distributions + outliers | Histograms (or violin plots) of all 9 features. Flag rows with unphysical values (`ph` outside [0, 14], negatives in concentrations). Report count of flagged rows. |
| 5 | Correlation matrix | Pearson and Spearman on the 9 features + label. Identify redundant pairs and any feature meaningfully correlated with `Potability`. |
| 6 | Feature prep | Median-impute each feature; add a `<feature>_missing` indicator column for any feature with >5% missingness. Same protocol Aidan used on `temperature_c`. |
| 7 | Random 80/20 stratified split | `train_test_split` with `stratify=y`, `random_state=42`. **Markdown cell explicitly states**: dataset lacks `site_id` / `date`, so v2's grouped + temporal protocol cannot apply; reported metrics are an *optimistic upper bound*. |
| 8 | Baselines: DummyClassifier | `strategy='most_frequent'`. Establishes the macro-F1 floor (~0.38 expected). |
| 9 | LogisticRegression | `StandardScaler` + `LogisticRegression(class_weight='balanced', max_iter=1000)`. Same config as v2. |
| 10 | XGBoost | `XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42)`. Sample weights via `compute_sample_weight('balanced', ...)`. Same config as v2. |
| 11 | Comparison table | 3-model DataFrame with columns `macro_F1`, `recall_0`, `recall_1`, `accuracy`. Same shape as v2 Step 7. |
| 12 | Feature importance | XGBoost gain/weight/cover. Three-panel bar chart + auto-print top feature per metric (same pattern as v2 Step 8). |
| 13 | **Cross-notebook comparison** | Side-by-side comparison: this 9-feature problem's best macro-F1 vs the 3-feature problem's macro-F1 from the pathogen-track notebooks. Numbers are hard-coded constants pulled from the most recent run of `FirstGradBooster_v2.ipynb` if it has been executed; otherwise fall back to `FirstGradBooster.ipynb` (Aidan's expanded v1, commit 923a34f: macro-F1 0.449 with temporal features). The markdown above the cell records which source was used. |
| 14 | Summary + open questions | What we learned about the dataset, caveats (Kaggle quality, no grouping, no abstain), and a recommendation for whether to invest more time in `water_potability` as a project asset. |

## 6. Success criteria

The notebook is "green" if **all** of:

1. Runs end-to-end on a developer laptop in under 30 s (≈3,276 rows × 9 features is tiny).
2. The leakage caveat in Section 7 is explicit, not buried.
3. Both XGBoost and LogReg beat the DummyClassifier on macro-F1.
4. The cross-notebook comparison (§13) produces a single concrete claim of the form: *"on a 9-feature classifier the best macro-F1 is X, vs Y for the 3-feature v2 classifier. The Δ = X − Y is/is not strong evidence that adding sensors lifts performance."*
5. Reproducibility: restart kernel → run all → identical numbers.

If 3 fails (i.e. neither model beats the dummy), the notebook is still informative — it would show the Kaggle dataset's 9 features don't carry enough signal even on an optimistic random split. Report that honestly; do not retrain to chase the F1 number.

## 7. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Cross-notebook macro-F1 comparison is unfair because splits differ (random here, grouped+temporal in v2). | Section 13 calls this out in a markdown cell. The comparison is framed as "best-case potability classifier vs honest-case pathogen classifier." A favourable comparison would have to clear that gap to be credible. |
| Median imputation on the heavily missing Sulfate/Trihalomethanes columns produces a degenerate feature. | The `<feature>_missing` indicator column captures the information that the value was missing. If the indicator dominates feature importance (as `temperature_missing` does in Aidan's notebook), Section 14 flags it as a known leakage-via-metadata risk. |
| The Kaggle dataset has documented data-quality issues (unphysical values, synthetic-feeling distributions). | Section 4 surfaces them; Section 14 acknowledges in the recommendation. |
| Hardcoded v2 numbers in §13 go stale when v2 is re-run. | The notebook reads the numbers from a small dict at the top of §13 with a markdown note pointing at the v2 cell that produced them. If v2 is re-run, the dict is updated by hand. Not automated. |

## 8. Decisions made (for the record)

| Decision | Choice | Alternative considered |
|---|---|---|
| Notebook scope | EDA + binary classifier in one notebook | Separate EDA notebook + modeling notebook. Rejected: too much ceremony for ~3k rows. |
| Comparison framing | Comparison-first — cross-notebook comparison is the strategic hook | Self-contained, no cross-reference. Rejected: loses the project-strategic question. |
| Split | Random 80/20 stratified by label | Grouped + temporal (impossible — no `site_id` / `date`); plain random (rejected — loses minority class in test set on small data). |
| Imputation | Median + missingness indicator per heavily-missing column | KNN imputation (rejected for a ~3k-row Kaggle dataset — overkill); drop-missing (rejected — loses ~40% of rows in worst case). |
| Model family | Dummy + LogReg + XGBoost | Just XGBoost (rejected: kills the baseline-comparison narrative); add RandomForest (rejected: not in v2, breaks apples-to-apples comparison). |
| Hyperparameters | Identical to v2 | Tune per dataset (rejected: tuning makes the cross-notebook comparison meaningless). |
| Abstain state | Omitted | Included (rejected: no field-deployment context here, would be ceremonial). |

## 9. Open questions

None blocking implementation. Worth revisiting after the notebook runs:

- If §13's cross-notebook comparison shows a meaningful Δ in macro-F1, what is the *minimum subset* of the 9 features needed to recover most of the lift? A small feature-selection experiment would inform the BOM-vs-utility conversation with Allen Chafa.
- If §13 shows no lift (i.e. the 9-feature classifier is no better than the 3-feature one), is the bottleneck dataset character (Kaggle artefact) or chemistry physics (3 vs 9 features don't actually carry materially different information for binary potability)? A follow-up notebook running v2's classifier on water_potability's pH+Turbidity columns would isolate this.
- Should the `Potability` binary label be treated as a noisy proxy for an underlying continuous quality score? Out of scope for this notebook.
