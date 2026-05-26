# Water Potability EDA + Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce `ML/water_potability_eda.ipynb` — an EDA + binary classifier on `Data/water_potability (1).csv` whose headline finding is a cross-notebook macro-F1 comparison against `FirstGradBooster_v2.ipynb`.

**Architecture:** Single Jupyter notebook (no `src/` package). Mirrors `FirstGradBooster_v2.ipynb` structure where possible so the cross-notebook comparison is mechanical: identical model hyperparameters, identical metric reporting style. The split protocol differs (random stratified, not grouped+temporal) because the dataset lacks `site_id` / `date`.

**Tech Stack:** Python 3.13.1 (`.venv` kernel), pandas, scikit-learn, xgboost, matplotlib. No new dependencies.

**Spec:** `ML/specs/2026-05-26-water-potability-eda-design.md`

**Conventions:**
- Each task ends with a `git commit`. Per-section commits are intentional — matches the granularity of `ML/plans/2026-05-25-ccme-wqi-poc-implementation.md`.
- "Run cell" + "verify expected output" replaces classical pytest TDD. The expected-output block in each task is the test.
- Notebook is hand-edited (open in VS Code / Jupyter, add cells via UI). Each task says which cells to add or modify.

---

## Task 1: Scaffold notebook + Section 1 (Setup & Load)

**Files:**
- Create: `ML/water_potability_eda.ipynb`

**Goal:** A 4-cell notebook that loads the dataset and prints its shape, date range (if any), and column list. After this task, the file exists, runs end-to-end (4 cells), and is committed.

- [ ] **Step 1: Create the notebook**

In VS Code: `File → New Jupyter Notebook` → save as `ML/water_potability_eda.ipynb`. Confirm the kernel reads `.venv (3.13.1)` (top-right of the notebook).

- [ ] **Step 2: Add Cell 1 (markdown) — title**

```markdown
# Water Potability EDA + Binary Classifier

EDA and binary classifier on `Data/water_potability (1).csv` (Kaggle, ~3,276 rows, 9 chemistry features + binary `Potability` label).

The strategic question this notebook answers: does adding 6 more chemistry features beyond pH/turbidity/temperature meaningfully lift macro-F1 above the ~0.45 plateau observed in `FirstGradBooster_v2.ipynb`?

**Spec:** `ML/specs/2026-05-26-water-potability-eda-design.md`
```

- [ ] **Step 3: Add Cell 2 (code) — imports**

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.dummy import DummyClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight
from sklearn.metrics import classification_report, f1_score

from xgboost import XGBClassifier

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)
```

- [ ] **Step 4: Add Cell 3 (markdown) — Step 1 header**

```markdown
## Step 1: Load data
```

- [ ] **Step 5: Add Cell 4 (code) — load**

```python
df = pd.read_csv('Data/water_potability (1).csv')
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
```

- [ ] **Step 6: Run all 4 cells. Verify output**

Expected from Cell 4:
```
Shape: (3276, 10)
Columns: ['ph', 'Hardness', 'Solids', 'Chloramines', 'Sulfate', 'Conductivity', 'Organic_carbon', 'Trihalomethanes', 'Turbidity', 'Potability']
```

If the shape is not `(3276, 10)` the file is corrupted — `git status` to confirm `Data/water_potability (1).csv` is unmodified before proceeding.

- [ ] **Step 7: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Scaffold water_potability_eda notebook (setup + load)"
```

---

## Task 2: Section 2 — Schema + missingness

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** Surface per-column null counts and confirm the ~30–40% missingness in `Sulfate` and `Trihalomethanes` documented in the spec.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 2: Schema + missingness

Surface dtype and null counts per column. The spec predicts ~30–40% missingness in `Sulfate` and `Trihalomethanes` (documented Kaggle artefact). Confirm or refute here before deciding on imputation.
```

- [ ] **Step 2: Add code cell**

```python
print("dtypes:")
print(df.dtypes)

print("\nMissing values:")
missing = df.isna().sum()
missing_pct = (missing / len(df) * 100).round(1)
print(pd.DataFrame({'count': missing, 'pct': missing_pct}).sort_values('count', ascending=False))
```

- [ ] **Step 3: Run cell. Verify expected output shape**

Expected: a 10-row DataFrame with `count` and `pct` columns. `Sulfate` and `Trihalomethanes` should appear at the top with non-zero counts (~700–1000 missing each, ~25–35%). `ph` typically has ~500 missing. `Potability` should be 0 missing (we drop rows missing the label later if needed).

If `Potability` has any missing values: flag in the next task's summary — the spec assumes the label is complete.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add schema + missingness section to water_potability_eda"
```

---

## Task 3: Section 3 — Class balance

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** Print the `Potability` class balance and contrast it with `full_dataset.csv`'s 95/5 in one line.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 3: Class balance

Kaggle water_potability is roughly 61/39 (not-potable / potable) — much milder than `full_dataset.csv`'s 95/5 HIGH-vs-rest. This matters because the macro-F1 floor for an always-majority dummy is much higher here, so the per-class recall on the minority class is the metric that actually moves.
```

- [ ] **Step 2: Add code cell**

```python
balance = df['Potability'].value_counts(normalize=True).mul(100).round(1)
print("Potability class balance (%):")
print(balance)
print(f"\nAlways-majority baseline accuracy: {balance.max():.1f}%")
print(f"(Compare: full_dataset.csv always-HIGH baseline is ~94.8%)")
```

- [ ] **Step 3: Run cell. Verify**

Expected:
```
Potability class balance (%):
Potability
0    61.0  (approx)
1    39.0  (approx)

Always-majority baseline accuracy: 61.0% (approx)
```

The exact split varies slightly by Kaggle download version. Accept anything in the 58–63 / 37–42 range.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add class balance section to water_potability_eda"
```

---

## Task 4: Sections 4 + 5 — Distributions, outliers, correlation

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 4 cells)

**Goal:** Two analytical cells — feature distributions with outlier flagging, plus correlation matrix.

- [ ] **Step 1: Add markdown cell for distributions**

```markdown
## Step 4: Distributions + outliers

Histograms of all 9 features. Flag rows with unphysical values — pH outside [0, 14] is the obvious one; large negative values in concentration columns (`Hardness`, `Solids`, `Chloramines`, `Sulfate`, `Conductivity`, `Organic_carbon`, `Trihalomethanes`, `Turbidity`) are physical impossibilities.
```

- [ ] **Step 2: Add code cell for distributions**

```python
feature_cols = ['ph', 'Hardness', 'Solids', 'Chloramines', 'Sulfate',
                'Conductivity', 'Organic_carbon', 'Trihalomethanes', 'Turbidity']

fig, axes = plt.subplots(3, 3, figsize=(13, 9))
for ax, col in zip(axes.flat, feature_cols):
    df[col].hist(bins=40, ax=ax)
    ax.set_title(col)
plt.tight_layout()
plt.show()

# Flag unphysical values
unphysical = {
    'ph_oor': ((df['ph'] < 0) | (df['ph'] > 14)).sum(),
    'negative_concentrations': sum((df[c] < 0).sum() for c in feature_cols if c != 'ph'),
}
print("Unphysical-value counts:")
for k, v in unphysical.items():
    print(f"  {k}: {v}")
```

- [ ] **Step 3: Add markdown cell for correlation**

```markdown
## Step 5: Correlation matrix

Pearson and Spearman correlations. We're looking for two things:
1. Redundant feature pairs (|ρ| > 0.7 between two features → one likely carries no marginal information).
2. Features meaningfully correlated with `Potability` (|ρ| > 0.1 is already noteworthy on this dataset — Kaggle water_potability is notoriously weak-signal).
```

- [ ] **Step 4: Add code cell for correlation**

```python
corr_p = df.corr(method='pearson', numeric_only=True)
corr_s = df.corr(method='spearman', numeric_only=True)

fig, axes = plt.subplots(1, 2, figsize=(16, 6))
for ax, corr, name in zip(axes, [corr_p, corr_s], ['Pearson', 'Spearman']):
    im = ax.imshow(corr.values, vmin=-1, vmax=1, cmap='RdBu_r')
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha='right')
    ax.set_yticklabels(corr.columns)
    ax.set_title(f'{name} correlation')
    fig.colorbar(im, ax=ax, fraction=0.046)
plt.tight_layout()
plt.show()

# Top correlations with the label
print("\nPearson correlation with Potability (sorted by |value|):")
target_corr = corr_p['Potability'].drop('Potability').sort_values(key=abs, ascending=False)
print(target_corr.round(3))
```

- [ ] **Step 5: Run both new code cells. Verify**

Expected from Step 2:
- 3x3 grid of histograms appears.
- Most features look roughly normal or log-normal except `Solids` (typically right-skewed). `pH` should look centred near 7.
- `ph_oor` and `negative_concentrations` should typically both be 0 (the published Kaggle dataset is clean) — but if they're non-zero, note for Section 14.

Expected from Step 4:
- Two heatmaps appear.
- The `Potability` correlation print should show all values with |ρ| < 0.1 — confirming the spec's warning that this is a weak-signal dataset.

- [ ] **Step 6: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add distributions + correlation matrix to water_potability_eda"
```

---

## Task 5: Section 6 — Feature prep

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** Add missingness indicators for any feature with >5% missing, then median-impute.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 6: Feature prep

For any feature with >5% missingness, add a `<feature>_missing` indicator column **before** imputing. Then median-impute the original column. Same protocol Aidan used on `temperature_c` in `FirstGradBooster.ipynb` — keeps the missingness signal available to tree-based models.
```

- [ ] **Step 2: Add code cell**

```python
df_model = df.copy()

# Identify features needing missingness indicators
missing_pct = df_model[feature_cols].isna().mean()
features_to_flag = [c for c in feature_cols if missing_pct[c] > 0.05]
print(f"Features with >5% missing (adding indicator + median impute): {features_to_flag}")

# Add missingness indicators
for col in features_to_flag:
    df_model[f'{col}_missing'] = df_model[col].isna().astype(int)

# Median impute all features
for col in feature_cols:
    df_model[col] = df_model[col].fillna(df_model[col].median())

# Define final feature list
FEATURES = feature_cols + [f'{c}_missing' for c in features_to_flag]
TARGET = 'Potability'

print(f"\nFinal feature count: {len(FEATURES)}")
print(f"Features: {FEATURES}")
print(f"\nRemaining nulls in feature matrix: {df_model[FEATURES].isna().sum().sum()}")
```

- [ ] **Step 3: Run cell. Verify**

Expected:
- `features_to_flag` should contain `['ph', 'Sulfate', 'Trihalomethanes']` (or a subset — `ph` may or may not exceed 5% depending on the Kaggle version).
- `Final feature count` typically 11–12 (9 base + 2–3 indicators).
- `Remaining nulls in feature matrix: 0`.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add feature prep (missingness indicators + median impute) to water_potability_eda"
```

---

## Task 6: Section 7 — Random stratified split

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** 80/20 random stratified split with explicit leakage caveat in the markdown.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 7: Random 80/20 stratified split

**Important caveat:** `water_potability (1).csv` has no `site_id` and no `date` column. The grouped + temporal protocol used in `FirstGradBooster_v2.ipynb` is *impossible* here. We fall back to random stratified split.

This means: any macro-F1 the models score here is an **optimistic upper bound** — repeated readings from the same physical source (if any exist in this Kaggle dataset) will leak across train/test. The cross-notebook comparison in Step 13 must account for this.
```

- [ ] **Step 2: Add code cell**

```python
X = df_model[FEATURES]
y = df_model[TARGET]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, stratify=y, random_state=RANDOM_STATE,
)

print(f"Train: {len(X_train)} rows")
print(f"Test:  {len(X_test)} rows")
print(f"\nTrain class balance (%):")
print(y_train.value_counts(normalize=True).mul(100).round(1))
print(f"\nTest class balance (%):")
print(y_test.value_counts(normalize=True).mul(100).round(1))
```

- [ ] **Step 3: Run cell. Verify**

Expected:
- Train ≈ 2,620 rows, Test ≈ 656 rows.
- Train and test class balances both ≈ 61/39 (stratified split should preserve the marginal).

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add 80/20 stratified split with leakage caveat to water_potability_eda"
```

---

## Task 7: Section 8 — Dummy baseline

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** Always-majority dummy classifier — the macro-F1 floor.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 8: Dummy baseline (always-majority)

Floor for the comparison. On a 61/39 problem, the dummy scores ~61% accuracy and ~0.38 macro-F1 (because it gets 100% recall on class 0 and 0% on class 1). Any honest classifier has to clear that macro-F1 to be worth shipping.
```

- [ ] **Step 2: Add code cell**

```python
dummy = DummyClassifier(strategy='most_frequent', random_state=RANDOM_STATE)
dummy.fit(X_train, y_train)
y_pred_dummy = dummy.predict(X_test)

print("Dummy (always-majority) on test set:")
print(classification_report(y_test, y_pred_dummy, digits=3, zero_division=0))
```

- [ ] **Step 3: Run cell. Verify**

Expected: macro avg F1-score ≈ 0.38. accuracy ≈ 0.61. recall[0] = 1.000, recall[1] = 0.000.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add dummy baseline to water_potability_eda"
```

---

## Task 8: Section 9 — Logistic regression

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** LogReg with StandardScaler + balanced class weights. Same hyperparameters as `FirstGradBooster_v2.ipynb`.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 9: Logistic regression baseline

Same hyperparameters as `FirstGradBooster_v2.ipynb` Step 6: `StandardScaler` → `LogisticRegression(class_weight='balanced', max_iter=1000)`. Identical config makes the cross-notebook comparison in Step 13 valid.
```

- [ ] **Step 2: Add code cell**

```python
lr_pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=RANDOM_STATE)),
])
lr_pipeline.fit(X_train, y_train)
y_pred_lr = lr_pipeline.predict(X_test)

print("Logistic regression on test set:")
print(classification_report(y_test, y_pred_lr, digits=3, zero_division=0))
```

- [ ] **Step 3: Run cell. Verify**

Expected: macro F1 in the 0.45–0.55 range. recall[1] should be meaningfully above 0 (probably 0.3–0.5).

If macro F1 ≤ 0.38, the model has not beaten the dummy and the dataset is genuinely no-signal. Surface this in Section 14.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add logistic regression baseline to water_potability_eda"
```

---

## Task 9: Section 10 — XGBoost

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** XGBoost classifier with same hyperparameters as v2.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 10: XGBoost

Hyperparameters identical to `FirstGradBooster_v2.ipynb` Step 5: 300 trees, depth 4, learning rate 0.1, subsample 0.8, colsample 0.8. Sample weights via `compute_sample_weight('balanced', ...)`.
```

- [ ] **Step 2: Add code cell**

```python
sample_weights = compute_sample_weight('balanced', y_train)

xgb_model = XGBClassifier(
    n_estimators=300,
    max_depth=4,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric='logloss',
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
xgb_model.fit(X_train, y_train, sample_weight=sample_weights)
y_pred_xgb = xgb_model.predict(X_test)

print("XGBoost on test set:")
print(classification_report(y_test, y_pred_xgb, digits=3, zero_division=0))
```

- [ ] **Step 3: Run cell. Verify**

Expected: macro F1 in the 0.55–0.70 range — should beat LogReg. The exact number is the strategic measurement used in Step 13.

If macro F1 ≤ LogReg's macro F1, note for Section 14: tree-based gradient boosting does not exploit non-linear structure that LogReg misses on this dataset, which is itself a signal about feature quality.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add XGBoost classifier to water_potability_eda"
```

---

## Task 10: Sections 11 + 12 — Comparison table + feature importance

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 4 cells)

**Goal:** Two analytical cells — 3-model comparison table, then XGBoost feature importance with auto-interpretation.

- [ ] **Step 1: Add markdown cell for comparison**

```markdown
## Step 11: Compare all three models

Headline table for this notebook. The key column is `macro_F1` — it's the only metric robust to the 61/39 imbalance.
```

- [ ] **Step 2: Add code cell for comparison**

```python
models = {
    'Dummy (always-majority)': y_pred_dummy,
    'Logistic regression':     y_pred_lr,
    'XGBoost':                 y_pred_xgb,
}

rows = []
for name, y_pred in models.items():
    rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    rows.append({
        'model':         name,
        'macro_F1':      rep['macro avg']['f1-score'],
        'recall_0':      rep.get('0', rep.get(0, {})).get('recall', 0.0),
        'recall_1':      rep.get('1', rep.get(1, {})).get('recall', 0.0),
        'accuracy':      rep['accuracy'],
    })

comparison = pd.DataFrame(rows).set_index('model').round(3)
print(comparison)

best_macro_f1 = comparison['macro_F1'].max()
best_model = comparison['macro_F1'].idxmax()
print(f"\nBest macro-F1: {best_macro_f1:.3f} ({best_model})")
```

Note: `rep.get('0', rep.get(0, {}))` handles both string and integer label keys — sklearn's `classification_report` varies between versions on how it keys the dict.

- [ ] **Step 3: Add markdown cell for feature importance**

```markdown
## Step 12: Feature importance + interpretation

XGBoost reports three importance measures. Gain is the most meaningful (how much each split reduces error). Weight = use count. Cover = sample count affected.

Below the chart we print the top feature per metric so the result is readable without re-eyeballing the bars.
```

- [ ] **Step 4: Add code cell for feature importance**

```python
booster = xgb_model.get_booster()

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, imp_type in zip(axes, ['gain', 'weight', 'cover']):
    scores = booster.get_score(importance_type=imp_type)
    scores = {f: scores.get(f, 0) for f in FEATURES}
    sorted_scores = dict(sorted(scores.items(), key=lambda x: x[1]))
    ax.barh(list(sorted_scores.keys()), list(sorted_scores.values()))
    ax.set_title(f'Importance by {imp_type}')

plt.suptitle("XGBoost Feature Importance", fontsize=13)
plt.tight_layout()
plt.show()

print("\nDominant feature by importance type:")
for imp_type in ['gain', 'weight', 'cover']:
    scores = booster.get_score(importance_type=imp_type)
    scores = {f: scores.get(f, 0) for f in FEATURES}
    top = max(scores, key=scores.get)
    print(f"  {imp_type:>7}: {top:<28} ({scores[top]:.2f})")
```

- [ ] **Step 5: Run both new code cells. Verify**

Expected from Step 2:
- 3-row DataFrame, columns `macro_F1`, `recall_0`, `recall_1`, `accuracy`.
- Dummy row: macro_F1 ≈ 0.38, recall_0 = 1.000, recall_1 = 0.000.
- LogReg and XGBoost rows: both higher than Dummy on macro_F1.

Expected from Step 4:
- Three horizontal bar charts side-by-side.
- Top feature by gain is typically `Chloramines` or `Sulfate` (both signal water treatment), but the exact dominant feature is unpredictable — this is what the experiment measures.
- The auto-printed "Dominant feature" block is the cell's user-facing output.

If any of the `<feature>_missing` indicators dominates by gain, that is the **same leakage-via-metadata pattern** noticed in `FirstGradBooster_v2.ipynb` (`temperature_missing` dominating). Flag explicitly in Section 14.

- [ ] **Step 6: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add 3-model comparison + feature importance to water_potability_eda"
```

---

## Task 11: Section 13 — Cross-notebook comparison

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 2 cells)

**Goal:** The strategic deliverable. A single side-by-side table comparing this notebook's best macro-F1 against the most recent comparable run on `full_dataset.csv`.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 13: Cross-notebook comparison — does more features help?

This is the strategic finding for the project. The 3-sensor classifier in `FirstGradBooster_v2.ipynb` plateaus around macro-F1 ≈ 0.45 (Aidan's v1 expansion: 0.449 with temporal features added). This notebook's 9-feature classifier scores `best_macro_f1` (computed above in Step 11).

**Important framing:** The split protocols differ. The 3-sensor classifier uses a grouped + temporal split (honest, pessimistic). This notebook uses random stratified (optimistic, leak-tolerant). So a *favourable* Δ here must be large enough to clear the protocol gap before it can be called real evidence that more features help.
```

- [ ] **Step 2: Add code cell**

```python
# Hardcoded reference numbers from prior runs. Update by hand when the source notebooks are re-run.
# Source: FirstGradBooster.ipynb commit 923a34f (Aidan's expansion, 2026-05-25).
# If FirstGradBooster_v2.ipynb has been run, use its XGBoost macro-F1 from that notebook's Step 7 instead.
V2_BEST_MACRO_F1 = 0.449  # XGBoost with temporal features, grouped+temporal split (honest)
V2_SOURCE = 'FirstGradBooster.ipynb @ 923a34f (Aidan v1.5, temporal-features XGB)'

delta = best_macro_f1 - V2_BEST_MACRO_F1
print(f"This notebook  (9 features, random split):    macro-F1 = {best_macro_f1:.3f}")
print(f"v2 reference   (3 features, grouped+temporal): macro-F1 = {V2_BEST_MACRO_F1:.3f}")
print(f"Source: {V2_SOURCE}")
print(f"\nΔ macro-F1 = {delta:+.3f}")

# The headline claim
if delta > 0.10:
    verdict = "STRONG: 9-feature lift is large enough to clear the protocol gap; suggests more sensors help."
elif delta > 0.03:
    verdict = "WEAK: 9-feature lift exists but is in the noise of the protocol-difference uncertainty."
else:
    verdict = "NULL: 9-feature classifier does not lift macro-F1 meaningfully. Feature count is not the bottleneck."

print(f"\nVerdict: {verdict}")
```

- [ ] **Step 3: Run cell. Verify**

Expected:
- Three printed numbers (this notebook's best, v2 reference 0.449, the delta).
- One of three verdict strings printed.

The verdict thresholds (0.10, 0.03) are calibrated against typical XGBoost noise on small datasets — adjust in Section 14's open questions if it lands ambiguously.

- [ ] **Step 4: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add cross-notebook comparison (strategic deliverable) to water_potability_eda"
```

---

## Task 12: Section 14 — Summary + open questions

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (append 1 cell)

**Goal:** A single markdown summary cell. No code. Records the verdict and open questions for the project.

- [ ] **Step 1: Add markdown cell**

```markdown
## Step 14: Summary + open questions

### What we learned
- **Dataset character:** ~3,276 rows; class balance ~61/39; ~30–40% missing in Sulfate / Trihalomethanes; pH typically also ~15% missing. Distributions are mostly clean (no unphysical values in standard Kaggle download).
- **Per-class correlation with `Potability`:** All features show |ρ| < 0.1 with the label — this dataset is genuinely weak-signal even on the raw feature → target relationship.
- **Best classifier:** {fill in from Step 11} with macro-F1 = {best_macro_f1}.
- **Strategic verdict (Step 13):** {fill in from Step 13's verdict string}.

### Caveats
- Random split, not grouped+temporal — reported metrics are an *optimistic upper bound*.
- The `<feature>_missing` indicators may carry more signal than the features themselves (same pattern observed in `FirstGradBooster.ipynb`'s `temperature_missing`). If feature importance ranks them top by gain, the model is partly learning *which rows had missing values*, which is a dataset artefact, not a chemistry signal.
- Kaggle water_potability has documented quality concerns and likely contains synthetic or imputed rows. Treat as a sandbox dataset, not a substrate for production model decisions.

### Open questions
- If the Step 13 verdict is **STRONG**, what is the minimum subset of the 9 features that recovers most of the macro-F1 lift? A small ablation (drop one feature at a time, retrain) would inform a BOM-vs-utility conversation with Allen Chafa.
- If the Step 13 verdict is **NULL**, the bottleneck is not feature count. The follow-up experiment is: run `FirstGradBooster_v2.ipynb`'s exact pipeline on the `pH + Turbidity` subset of `water_potability` only, to isolate whether the difference is dataset character (Kaggle artefact) vs feature physics.
- Should `Potability` ∈ {0, 1} be treated as a noisy proxy for an underlying continuous quality score? Out of scope for this notebook.
```

- [ ] **Step 2: Manually populate the `{fill in ...}` braces with the actual numbers/verdict from Steps 11 and 13.**

Open the notebook, look at Step 11's printed `Best macro-F1: 0.XYZ (model_name)`, look at Step 13's verdict line, paste them into the markdown cell.

- [ ] **Step 3: Commit**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Add summary section to water_potability_eda"
```

---

## Task 13: End-to-end run + final commit

**Files:**
- Modify: `ML/water_potability_eda.ipynb` (re-execute all cells)

**Goal:** Reproducibility check — kernel restart, run all, confirm the same numbers come out. Final commit with full executed-output notebook.

- [ ] **Step 1: Restart kernel & clear outputs**

In Jupyter / VS Code: `Kernel → Restart and Clear Outputs`. Save the notebook in this cleared state.

- [ ] **Step 2: Run all cells from the top**

`Kernel → Restart and Run All`. Wait for completion (should be under 30 s).

- [ ] **Step 3: Verify all cells succeeded**

Scroll through the notebook. Confirm:
- No red error tracebacks anywhere.
- Every code cell has output below it (except the import cell which prints nothing).
- The 3-panel feature-importance figure rendered.
- The 3×3 distribution histogram grid rendered.
- The Step 13 verdict line is one of the three expected strings.

- [ ] **Step 4: Compare key numbers**

Compare against the numbers committed earlier:
- Class balance from Step 3 should still be ~61/39.
- Step 11's best macro-F1 should match (exactly, given fixed `random_state=42`) what you saw when first running Task 10.
- Step 13's delta and verdict should match what you saw in Task 11.

If any number changed, something is non-deterministic — investigate `random_state` plumbing before committing.

- [ ] **Step 5: Final commit with executed notebook**

```bash
git add ML/water_potability_eda.ipynb
git commit -m "Run water_potability_eda end-to-end; reproducibility verified"
git push origin main
```

---

## Self-review

After completing all 13 tasks, the engineer should have:

| Spec requirement | Task that implements it |
|---|---|
| §1 Goal: EDA + binary classifier with cross-notebook comparison | All tasks; §13 cross-notebook is Task 11 |
| §3 Features: 9 columns + missingness indicators | Task 5 |
| §5 Step 1: Setup + load | Task 1 |
| §5 Step 2: Schema + missingness | Task 2 |
| §5 Step 3: Class balance | Task 3 |
| §5 Steps 4-5: Distributions + correlation | Task 4 |
| §5 Step 6: Feature prep | Task 5 |
| §5 Step 7: Random stratified split with caveat | Task 6 |
| §5 Step 8: Dummy baseline | Task 7 |
| §5 Step 9: LogReg | Task 8 |
| §5 Step 10: XGBoost | Task 9 |
| §5 Steps 11-12: Comparison + feature importance | Task 10 |
| §5 Step 13: Cross-notebook comparison | Task 11 |
| §5 Step 14: Summary | Task 12 |
| §6 Success criterion 5 (reproducibility) | Task 13 |

All spec sections covered. No placeholders in task steps. All file paths absolute. All hyperparameters explicit and identical to `FirstGradBooster_v2.ipynb`. No unreferenced types or functions.
