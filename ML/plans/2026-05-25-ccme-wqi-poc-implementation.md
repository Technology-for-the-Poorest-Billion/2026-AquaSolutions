# CCME WQI POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python notebook that trains and evaluates three regression models (Linear, RandomForest, HistGradientBoosting) predicting `CCME_Values` from 8 chemistry features in `Data/Combined_dataset.csv`, with EDA, stratified test metrics, and a banded-confusion-matrix view.

**Architecture:** Single file `ML/01_ccme_wqi_poc.py` in jupytext "percent" cell format (`# %%` and `# %% [markdown]` markers). The file is a notebook in VS Code's Python extension and is convertible to `.ipynb` via one jupytext command. Figures are saved to `ML/figures/` as PNGs so the file is also runnable end-to-end as a plain script (`python ML/01_ccme_wqi_poc.py`). No `src/` package — all logic lives in cells.

**Tech Stack:** Python 3, pandas, numpy, scikit-learn, scipy, matplotlib. No new heavy dependencies.

**Source spec:** `ML/specs/2026-05-25-ccme-wqi-poc-design.md`

---

## Pre-flight (do once before Task 1)

- [ ] **Step 1: Verify Python environment**

Run from repo root:

```bash
cd /Users/tristanmartin/Desktop/GM2/GM2_Aqua_Solutions
source .venv/bin/activate 2>/dev/null || true
python -c "import pandas, numpy, sklearn, scipy, matplotlib; print('pandas', pandas.__version__); print('numpy', numpy.__version__); print('sklearn', sklearn.__version__); print('scipy', scipy.__version__); print('matplotlib', matplotlib.__version__)"
```

Expected: five version lines, no `ImportError`. If any import fails, install with:

```bash
python -m pip install pandas numpy scikit-learn scipy matplotlib
```

- [ ] **Step 2: Verify the dataset is on disk**

```bash
ls -lh Data/Combined_dataset.csv
```

Expected: file exists, ~200–400 MB. If it's an LFS pointer (a few hundred bytes), run `git lfs pull`.

---

## Task 1: Create the scaffold file

**Files:**
- Create: `ML/01_ccme_wqi_poc.py`
- Create: `ML/figures/` (directory, will hold PNGs)

- [ ] **Step 1: Create the figures directory**

```bash
mkdir -p ML/figures
```

- [ ] **Step 2: Write the scaffold file with section headings**

Create `ML/01_ccme_wqi_poc.py` with this content:

```python
# %% [markdown]
# # CCME WQI Proof-of-Concept
#
# Trains regression models that predict the CCME Water Quality Index
# (`CCME_Values`, 0-100) from chemistry features in
# `Data/Combined_dataset.csv`.
#
# Design spec: `ML/specs/2026-05-25-ccme-wqi-poc-design.md`.
# Near-perfect R² is **expected** here because the CCME WQI is a
# deterministic formula of the input parameters. The goal of this
# notebook is to verify the pipeline works end-to-end on this data.

# %% [markdown]
# ## 0. Setup

# %% [markdown]
# ## 1. Load and stratified sample

# %% [markdown]
# ## 2. EDA

# %% [markdown]
# ## 3. Train/test split

# %% [markdown]
# ## 4. Models — Linear, Random Forest, HistGradientBoosting

# %% [markdown]
# ## 5. Evaluation

# %% [markdown]
# ## 6. Summary
```

- [ ] **Step 3: Run the file end-to-end to verify it parses**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: exits with code 0 and no output (file contains only comments).

- [ ] **Step 4: Commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: scaffold notebook with section markers"
```

---

## Task 2: Setup cell — imports, seed, paths

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 0. Setup")

- [ ] **Step 1: Add the setup cell**

Find the `# %% [markdown]\n# ## 0. Setup` block in `ML/01_ccme_wqi_poc.py` and **append** the following two cells immediately after it (before `# %% [markdown]\n# ## 1. Load and stratified sample`):

```python
# %%
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # non-blocking; we save PNGs instead of showing
import matplotlib.pyplot as plt
import sklearn
import scipy
from scipy.stats import spearmanr

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

# Resolve repo root whether we run from repo root or from ML/
_here = Path(__file__).resolve().parent if "__file__" in globals() else Path.cwd().resolve()
REPO_ROOT = _here.parent if _here.name == "ML" else _here
DATA_PATH = REPO_ROOT / "Data" / "Combined_dataset.csv"
FIGURES_DIR = REPO_ROOT / "ML" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

print(f"pandas      {pd.__version__}")
print(f"numpy       {np.__version__}")
print(f"sklearn     {sklearn.__version__}")
print(f"scipy       {scipy.__version__}")
print(f"matplotlib  {matplotlib.__version__}")
print(f"data path:  {DATA_PATH}")
print(f"figures:    {FIGURES_DIR}")

# %%
# Verification
assert DATA_PATH.exists(), f"Combined_dataset.csv not found at {DATA_PATH}"
assert FIGURES_DIR.exists()
print("Setup OK")
```

- [ ] **Step 2: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: prints five version lines, two path lines, and `Setup OK`. No assertion errors.

- [ ] **Step 3: Commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: setup cell (imports, seed, paths)"
```

---

## Task 3: Load and stratified 50k sample

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 1. Load and stratified sample")

- [ ] **Step 1: Add the load + sample cells**

Append immediately after the `# %% [markdown]\n# ## 1. Load and stratified sample` markdown cell:

```python
# %%
CHEM_COLS = [
    "Ammonia (mg/l)",
    "Biochemical Oxygen Demand (mg/l)",
    "Dissolved Oxygen (mg/l)",
    "Orthophosphate (mg/l)",
    "pH (ph units)",
    "Temperature (cel)",
    "Nitrogen (mg/l)",
    "Nitrate (mg/l)",
]
STRATA_COLS = ["Country", "Waterbody Type"]
TARGET_NUM = "CCME_Values"
TARGET_BAND = "CCME_WQI"
SAMPLE_SIZE = 50_000

usecols = STRATA_COLS + CHEM_COLS + [TARGET_NUM, TARGET_BAND]
print(f"Reading {DATA_PATH.name} (this takes ~10-30s)...")
df_full = pd.read_csv(DATA_PATH, usecols=usecols)
print(f"Full dataset: {len(df_full):,} rows")

frac = SAMPLE_SIZE / len(df_full)
# Explicit per-stratum sampling avoids pandas FutureWarning on groupby.apply
df = pd.concat(
    [g.sample(frac=frac, random_state=RANDOM_STATE) for _, g in df_full.groupby(STRATA_COLS)],
    ignore_index=True,
)
del df_full  # free ~600 MB
print(f"Stratified sample: {len(df):,} rows")
print(f"\nBand counts after sampling:\n{df[TARGET_BAND].value_counts()}")
print(f"\nTop 5 strata by row count:")
print(df.groupby(STRATA_COLS).size().sort_values(ascending=False).head())

# %%
# Verification
assert 40_000 <= len(df) <= 60_000, f"Sample size out of tolerance: {len(df)}"
assert df.isna().sum().sum() == 0, f"Unexpected NaNs: {df.isna().sum().to_dict()}"
present_bands = set(df[TARGET_BAND].unique())
required_bands = {"Excellent", "Good", "Fair", "Marginal"}
assert required_bands.issubset(present_bands), \
    f"Missing major bands: have {present_bands}, need {required_bands}"
print("Load + sample OK")
```

- [ ] **Step 2: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: prints `Full dataset: 2,827,977 rows`, `Stratified sample: ~50,000 rows`, band counts (Good > Excellent > Fair > Marginal > Poor), top 5 strata, and finally `Load + sample OK`.

- [ ] **Step 3: Commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: stratified 50k sample of Combined_dataset"
```

---

## Task 4: EDA — stats, correlation, MI/Spearman, PCA scree

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 2. EDA")
- Create (as side effect): `ML/figures/01_band_counts.png`, `ML/figures/02_correlation_heatmap.png`, `ML/figures/03_mi_spearman.png`, `ML/figures/04_pca_scree.png`

- [ ] **Step 1: Add the EDA cells**

Append immediately after the `# %% [markdown]\n# ## 2. EDA` markdown cell:

```python
# %% [markdown]
# ### 2a. Summary stats

# %%
print(df[CHEM_COLS + [TARGET_NUM]].describe().round(3))

# %% [markdown]
# ### 2b. Band distribution

# %%
band_counts = df[TARGET_BAND].value_counts()
fig, ax = plt.subplots(figsize=(6, 4))
band_counts.plot.bar(ax=ax)
ax.set_title("CCME_WQI band counts in 50k stratified sample")
ax.set_ylabel("rows")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "01_band_counts.png", dpi=120)
plt.close(fig)
print(band_counts)

# %% [markdown]
# ### 2c. Pearson correlation matrix — feature redundancy view
# This answers: "are any chemistry features redundant with each other?"

# %%
corr = df[CHEM_COLS].corr()
fig, ax = plt.subplots(figsize=(9, 7))
im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
ax.set_xticks(range(len(CHEM_COLS)))
ax.set_xticklabels(CHEM_COLS, rotation=45, ha="right")
ax.set_yticks(range(len(CHEM_COLS)))
ax.set_yticklabels(CHEM_COLS)
for i in range(len(CHEM_COLS)):
    for j in range(len(CHEM_COLS)):
        ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center",
                color="black", fontsize=8)
fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
ax.set_title("Pearson correlation of chemistry features")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "02_correlation_heatmap.png", dpi=120)
plt.close(fig)

# %% [markdown]
# ### 2d. Mutual information and Spearman vs CCME_Values — target relevance view
# This answers: "which features actually predict the WQI score?"
# This is the question PCA does *not* answer.

# %%
from sklearn.feature_selection import mutual_info_regression

X_eda = df[CHEM_COLS].values
y_eda = df[TARGET_NUM].values

mi = mutual_info_regression(X_eda, y_eda, random_state=RANDOM_STATE)
spearman = np.array([spearmanr(df[c], df[TARGET_NUM]).statistic for c in CHEM_COLS])

eda_df = (
    pd.DataFrame({"feature": CHEM_COLS, "mutual_information": mi, "spearman": spearman})
    .sort_values("mutual_information", ascending=False)
    .reset_index(drop=True)
)
print(eda_df.round(3))

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
axes[0].barh(eda_df["feature"], eda_df["mutual_information"])
axes[0].invert_yaxis()
axes[0].set_title("Mutual information vs CCME_Values")
axes[1].barh(eda_df["feature"], eda_df["spearman"])
axes[1].invert_yaxis()
axes[1].set_title("Spearman correlation vs CCME_Values")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "03_mi_spearman.png", dpi=120)
plt.close(fig)

# %% [markdown]
# ### 2e. PCA scree plot — VISUALISATION ONLY
# Not used to project inputs into the model. Components are shown to
# inspect how variance is distributed across the chemistry features.

# %%
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

X_std = StandardScaler().fit_transform(df[CHEM_COLS])
pca = PCA().fit(X_std)
fig, ax = plt.subplots(figsize=(7, 4))
xs = np.arange(1, len(pca.explained_variance_ratio_) + 1)
ax.bar(xs, pca.explained_variance_ratio_, label="per-component variance")
ax.plot(xs, np.cumsum(pca.explained_variance_ratio_), "-o", color="orange",
        label="cumulative")
ax.set_xlabel("principal component")
ax.set_ylabel("explained variance ratio")
ax.set_title("PCA scree — EDA only, NOT used for input projection")
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES_DIR / "04_pca_scree.png", dpi=120)
plt.close(fig)
print("Cumulative explained variance:", np.cumsum(pca.explained_variance_ratio_).round(3))

# %%
# Verification
assert mi.shape == (len(CHEM_COLS),)
assert np.all(np.isfinite(mi)), "mutual_information has non-finite values"
assert np.all(np.isfinite(spearman)), "spearman has non-finite values"
for name in ["01_band_counts.png", "02_correlation_heatmap.png",
             "03_mi_spearman.png", "04_pca_scree.png"]:
    assert (FIGURES_DIR / name).exists(), f"Missing figure: {name}"
print("EDA OK")
```

- [ ] **Step 2: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: prints summary stats table, band counts, MI/Spearman table sorted by MI, cumulative explained variance, and `EDA OK`. Four PNGs appear in `ML/figures/`.

- [ ] **Step 3: Inspect the figures**

Open the four PNGs and confirm:
- `01_band_counts.png`: bar chart with five bands, Good largest.
- `02_correlation_heatmap.png`: 8×8 matrix, diagonal is 1.00.
- `03_mi_spearman.png`: two horizontal bar charts, top feature roughly matches between the two panels.
- `04_pca_scree.png`: bars descending, cumulative line approaches 1.0 by PC8.

- [ ] **Step 4: Commit**

```bash
git add ML/01_ccme_wqi_poc.py ML/figures/
git commit -m "ML POC: EDA (correlation, MI/Spearman, PCA scree)"
```

---

## Task 5: Train/test split (80/20, stratified by band)

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 3. Train/test split")

- [ ] **Step 1: Add the split cells**

Append immediately after the `# %% [markdown]\n# ## 3. Train/test split` markdown cell:

```python
# %%
from sklearn.model_selection import train_test_split

X = df[CHEM_COLS].values
y = df[TARGET_NUM].values
y_band = df[TARGET_BAND].values

X_train, X_test, y_train, y_test, y_band_train, y_band_test = train_test_split(
    X, y, y_band,
    test_size=0.20,
    stratify=y_band,
    random_state=RANDOM_STATE,
)
print(f"train: {len(X_train):,}  test: {len(X_test):,}")
print(f"\nTrain band balance:\n{pd.Series(y_band_train).value_counts()}")
print(f"\nTest band balance:\n{pd.Series(y_band_test).value_counts()}")

# %%
# Verification
assert len(X_train) + len(X_test) == len(df)
assert abs(len(X_test) / len(df) - 0.20) < 0.01, \
    f"Test fraction off: {len(X_test) / len(df):.4f}"
assert set(np.unique(y_band_train)) == set(np.unique(y_band_test)), \
    "Train and test should contain the same bands"
print("Split OK")
```

- [ ] **Step 2: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: prints train/test counts (≈40k / 10k), band balance for each, and `Split OK`.

- [ ] **Step 3: Commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: 80/20 train/test split stratified by band"
```

---

## Task 6: Train three models with 5-fold CV

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 4. Models")

- [ ] **Step 1: Add the model + CV cells**

Append immediately after the `# %% [markdown]\n# ## 4. Models — Linear, Random Forest, HistGradientBoosting` markdown cell:

```python
# %%
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import cross_validate

models = {
    "Linear": LinearRegression(),
    "RandomForest": RandomForestRegressor(
        n_estimators=200, max_depth=12, n_jobs=-1, random_state=RANDOM_STATE
    ),
    "HistGBM": HistGradientBoostingRegressor(
        max_iter=300, random_state=RANDOM_STATE
    ),
}

cv_scoring = {
    "mae": "neg_mean_absolute_error",
    "rmse": "neg_root_mean_squared_error",
    "r2": "r2",
}

cv_summary = {}
for name, model in models.items():
    print(f"5-fold CV: {name} ...")
    scores = cross_validate(
        model, X_train, y_train, cv=5, scoring=cv_scoring, n_jobs=-1
    )
    cv_summary[name] = {
        "MAE_mean": -scores["test_mae"].mean(),
        "MAE_std":  scores["test_mae"].std(),
        "RMSE_mean": -scores["test_rmse"].mean(),
        "RMSE_std":  scores["test_rmse"].std(),
        "R2_mean":  scores["test_r2"].mean(),
        "R2_std":   scores["test_r2"].std(),
    }

print("\nCV results (mean ± std over 5 folds):")
print(pd.DataFrame(cv_summary).T.round(3))

# %%
# Fit each model on the full training set for downstream evaluation
for name, model in models.items():
    print(f"Fitting {name} on full training set ...")
    model.fit(X_train, y_train)
print("Models fitted")

# %%
# Verification
for name, row in cv_summary.items():
    for key, val in row.items():
        assert np.isfinite(val), f"{name}.{key} = {val} (non-finite)"
# Sanity: the ensemble models should beat linear on CV R²
linear_r2 = cv_summary["Linear"]["R2_mean"]
rf_r2 = cv_summary["RandomForest"]["R2_mean"]
gbm_r2 = cv_summary["HistGBM"]["R2_mean"]
assert rf_r2 > linear_r2, f"RF ({rf_r2:.3f}) should beat Linear ({linear_r2:.3f})"
assert gbm_r2 > linear_r2, f"GBM ({gbm_r2:.3f}) should beat Linear ({linear_r2:.3f})"
print("Models OK")
```

- [ ] **Step 2: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: prints three "5-fold CV: ..." lines, a CV summary table (Linear R² ≈ 0.55–0.75, RF/GBM R² > 0.9), three "Fitting ..." lines, and `Models OK`. Total runtime to here: roughly 30–90 s on a modern laptop.

- [ ] **Step 3: Commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: train Linear/RF/HistGBM with 5-fold CV"
```

---

## Task 7: Test-set evaluation — metrics, stratified MAE, banded CM, importance

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (insert under "## 5. Evaluation")
- Create (as side effect): `ML/figures/05_permutation_importance.png`

- [ ] **Step 1: Add the overall-metrics cells**

Append immediately after the `# %% [markdown]\n# ## 5. Evaluation` markdown cell:

```python
# %% [markdown]
# ### 5a. Overall MAE / RMSE / R² on the held-out 20%

# %%
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

def evaluate(model, X_te, y_te):
    yhat = model.predict(X_te)
    metrics = {
        "MAE": mean_absolute_error(y_te, yhat),
        "RMSE": float(np.sqrt(mean_squared_error(y_te, yhat))),
        "R2": r2_score(y_te, yhat),
    }
    return metrics, yhat

test_metrics = {}
preds = {}
for name, model in models.items():
    metrics, yhat = evaluate(model, X_test, y_test)
    test_metrics[name] = metrics
    preds[name] = yhat
print("Test-set metrics:")
print(pd.DataFrame(test_metrics).T.round(3))
```

- [ ] **Step 2: Add the stratified-MAE cells**

Append next:

```python
# %% [markdown]
# ### 5b. MAE stratified by true band
# Aggregate MAE is dominated by Excellent/Good (~80% of rows). This view
# exposes how the model performs on the rarer, more important bands.

# %%
def stratified_mae(y_true, y_pred, bands):
    out = {}
    for b in ["Excellent", "Good", "Fair", "Marginal", "Poor"]:
        mask = bands == b
        if mask.sum() == 0:
            out[b] = float("nan")
        else:
            out[b] = mean_absolute_error(y_true[mask], y_pred[mask])
    return out

strat_table = pd.DataFrame(
    {name: stratified_mae(y_test, preds[name], y_band_test) for name in models}
)
print("Stratified MAE by true band:")
print(strat_table.round(3))
```

- [ ] **Step 3: Add the banded confusion matrix cells**

Append next:

```python
# %% [markdown]
# ### 5c. Banded confusion matrix
# Bucket predictions at standard CCME thresholds and report a 5×5 matrix.
# Thresholds: Excellent ≥95, Good 80–94, Fair 65–79, Marginal 45–64, Poor <45.

# %%
def to_band(values):
    out = np.full(len(values), "Poor", dtype=object)
    out[values >= 45] = "Marginal"
    out[values >= 65] = "Fair"
    out[values >= 80] = "Good"
    out[values >= 95] = "Excellent"
    return out

LABELS = ["Poor", "Marginal", "Fair", "Good", "Excellent"]
band_preds = {name: to_band(preds[name]) for name in models}

macro_f1s = {}
for name in models:
    cm = confusion_matrix(y_band_test, band_preds[name], labels=LABELS)
    macro_f1 = f1_score(
        y_band_test, band_preds[name], labels=LABELS, average="macro", zero_division=0
    )
    macro_f1s[name] = macro_f1
    cm_df = pd.DataFrame(
        cm,
        index=[f"true_{l}" for l in LABELS],
        columns=[f"pred_{l}" for l in LABELS],
    )
    print(f"\n=== {name}: macro-F1 = {macro_f1:.3f} ===")
    print(cm_df)
print("\nMacro-F1 summary:", {k: round(v, 3) for k, v in macro_f1s.items()})
```

- [ ] **Step 4: Add the permutation-importance cells**

Append next:

```python
# %% [markdown]
# ### 5d. Permutation feature importance — best model

# %%
from sklearn.inspection import permutation_importance

best_name = max(test_metrics, key=lambda n: test_metrics[n]["R2"])
print(f"Best model by test R²: {best_name}")

perm = permutation_importance(
    models[best_name],
    X_test,
    y_test,
    n_repeats=10,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)
perm_df = (
    pd.DataFrame({
        "feature": CHEM_COLS,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    })
    .sort_values("importance_mean", ascending=False)
    .reset_index(drop=True)
)
print(perm_df.round(4))

fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(perm_df["feature"], perm_df["importance_mean"],
        xerr=perm_df["importance_std"])
ax.invert_yaxis()
ax.set_xlabel("permutation importance (drop in R²)")
ax.set_title(f"Permutation importance — {best_name}")
fig.tight_layout()
fig.savefig(FIGURES_DIR / "05_permutation_importance.png", dpi=120)
plt.close(fig)
```

- [ ] **Step 5: Add the evaluation verification cell**

Append next:

```python
# %%
# Verification
for name in models:
    cm = confusion_matrix(y_band_test, band_preds[name], labels=LABELS)
    assert cm.sum() == len(y_test), \
        f"{name} confusion matrix sums to {cm.sum()}, expected {len(y_test)}"
    f1 = macro_f1s[name]
    assert 0.0 <= f1 <= 1.0, f"{name} macro_f1 out of range: {f1}"
for name in models:
    assert np.all(np.isfinite(preds[name])), f"{name} produced non-finite predictions"
assert perm.importances_mean.shape == (len(CHEM_COLS),)
assert (FIGURES_DIR / "05_permutation_importance.png").exists()
print("Evaluation OK")
```

- [ ] **Step 6: Run the file end-to-end**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected:
- Test-set metrics table (Linear R² ≈ 0.55–0.75, RF/GBM R² > 0.9).
- Stratified MAE table (errors should be roughly smallest for Excellent, largest for Poor / Marginal).
- Three confusion matrices and a macro-F1 summary (best model's macro-F1 should be ≥ 0.70 per the spec; if lower, that's still a valid result — see Task 8).
- Permutation-importance table sorted descending; the same feature(s) should rank high here and in §2d's MI table.
- `Evaluation OK`.

- [ ] **Step 7: Inspect the new figure**

Open `ML/figures/05_permutation_importance.png`. Expect a horizontal bar chart with the most-important chemistry feature at top and error bars from the 10 repeats.

- [ ] **Step 8: Commit**

```bash
git add ML/01_ccme_wqi_poc.py ML/figures/
git commit -m "ML POC: test-set evaluation, stratified MAE, banded CM, permutation importance"
```

---

## Task 8: Summary markdown cell + reproducibility check

**Files:**
- Modify: `ML/01_ccme_wqi_poc.py` (replace the empty `## 6. Summary` block with a populated one)

- [ ] **Step 1: Populate the summary markdown cell**

Read the actual numbers printed by Task 7 from the most recent run (CV table, test-metrics table, stratified MAE table, macro-F1 summary, top-3 permutation importances). Then replace the `# %% [markdown]\n# ## 6. Summary` block at the end of `ML/01_ccme_wqi_poc.py` with:

```python
# %% [markdown]
# ## 6. Summary
#
# **Cross-validated R² on the training half (5-fold):**
# - Linear:       <Linear  R²_mean> ± <Linear  R²_std>
# - RandomForest: <RF      R²_mean> ± <RF      R²_std>
# - HistGBM:      <HistGBM R²_mean> ± <HistGBM R²_std>
#
# **Held-out 20% test set:**
# - Linear:       R² = <Linear  test R²>, MAE = <Linear  test MAE>
# - RandomForest: R² = <RF      test R²>, MAE = <RF      test MAE>
# - HistGBM:      R² = <HistGBM test R²>, MAE = <HistGBM test MAE>
#
# **Banded-confusion macro-F1:**
# - Linear:       <Linear  macro-F1>
# - RandomForest: <RF      macro-F1>
# - HistGBM:      <HistGBM macro-F1>
#
# **Top 3 features by permutation importance (best model = <best_name>):**
# 1. <feature_1> — <importance ± std>
# 2. <feature_2> — <importance ± std>
# 3. <feature_3> — <importance ± std>
#
# **Reading these numbers.** The CCME WQI is a deterministic formula of
# these inputs, so ensembles fitting R² > 0.9 is the *expected* outcome
# and tells us only that the pipeline works. The interesting parts are:
# (a) how far the linear baseline trails the ensembles (the floor the
# fancy model has to beat), (b) the stratified-MAE spread across bands
# (large gaps mean the model relies on the high-score majority and
# struggles on Poor/Marginal), and (c) whether the same chemistry
# features rank high in MI (§2d) and permutation importance (§5d) —
# agreement strengthens the "which features matter" finding.
#
# **Next steps (out of scope for this POC, candidates only):** temporal
# train/test split (pre-2015 vs post-2015) to test generalisation across
# time; ablation adding Waterbody Type as a feature; comparison against
# the project's TinyML target on the pathogen-label dataset
# (`full_dataset.csv`).
```

Replace each `<...>` placeholder with the actual value from the most recent run output. Do **not** leave any angle brackets in the committed file.

- [ ] **Step 2: Run the file end-to-end one final time**

```bash
python ML/01_ccme_wqi_poc.py
```

Expected: same numbers as the previous run, ending in `Evaluation OK`. The summary cell is markdown-only, so it does not change output.

- [ ] **Step 3: Reproducibility check**

Note the test-set R² for HistGBM from this run.

Run the file again from a clean state:

```bash
python ML/01_ccme_wqi_poc.py
```

Confirm the HistGBM test R² is **identical** to the previous run (same `RANDOM_STATE` everywhere). If it differs, the reproducibility criterion (spec §6.5) has failed — find the source of non-determinism before claiming the POC is green.

- [ ] **Step 4: Final commit**

```bash
git add ML/01_ccme_wqi_poc.py
git commit -m "ML POC: populated summary cell with actual results"
```

---

## Optional Task 9: Convert to .ipynb

Only do this if you specifically need a `.ipynb` file for sharing or for a Jupyter-only workflow.

- [ ] **Step 1: Install jupytext**

```bash
python -m pip install jupytext
```

- [ ] **Step 2: Convert**

```bash
jupytext --to ipynb ML/01_ccme_wqi_poc.py -o ML/01_ccme_wqi_poc.ipynb
```

- [ ] **Step 3: Verify**

```bash
ls -lh ML/01_ccme_wqi_poc.ipynb
jupyter nbconvert --to script ML/01_ccme_wqi_poc.ipynb --stdout | head -20
```

Expected: file exists; the head of the converted-back script matches the top of the `.py` file (minus jupytext markers).

- [ ] **Step 4: Commit (only if keeping the .ipynb)**

```bash
git add ML/01_ccme_wqi_poc.ipynb
git commit -m "ML POC: add .ipynb export"
```

---

## Success criteria recap (from spec §6)

The POC is green if **all** of:

1. The script runs end-to-end on the 50k sample in **under 60 s** on a developer laptop (measure with `time python ML/01_ccme_wqi_poc.py`).
2. Random Forest **and** HistGradientBoosting both beat `LinearRegression` on R² by a meaningful margin (Task 6 verification asserts this).
3. Stratified MAE is **reported per band** in Task 7 §5b (not buried in aggregates).
4. Banded-CM **macro-F1 ≥ 0.70** for the best model on the held-out set (Task 7 §5c).
5. Reproducibility: two consecutive runs produce identical numbers (Task 8 §3).

If 1–3 pass but criterion 4 fails, report the result honestly in the summary cell — do **not** retrain or hand-tune to chase the number. See spec §6 for the rationale.
