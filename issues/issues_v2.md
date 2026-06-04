# issues_v2.md — Dataset-Level Technical Issues

A briefing document of **dataset-only** issues for the GM2 TinyML water-quality project. Implementation difficulties are outlined in "issues_v3.md". The issues described here refer to the four datasets in the "Data" folder. 

## 0. Inventory

| File | Rows × Cols | Target column | Target type | Origin |
|---|---|---|---|---|
| `Data/full_dataset.csv` | 25,625 × 15 | `risk_drinking_no_treatment` (also `_limited_treatment`, `_contact`, `_irrigation_raw`) + raw `ecoli_per_100ml`, `faecal_coliforms_per_100ml` | Ordinal {low, Med, HIGH} + raw microbial counts | DWS South Africa (WMA monitoring) |
| `Data/water_potability (1).csv` | ~3,276 × 10 | `Potability` | Binary {0, 1} | Kaggle (Aditya Kadiwal) |
| `Data/Combined_dataset.csv` | very large (~320 MB) × 14 | `CCME_WQI`, `CCME_Values` | Continuous + ordinal {Excellent, …, Poor} | Figshare 1940–2023 scrape |
| `Data/WQD.csv` | small (~kB) × 15 | `Water Quality` | Ordinal | Mendeley (fish-pond aquaculture) |

## 1. Cross-dataset issues

### 1.1 Only one dataset has a microbial label
- `full_dataset.csv` is the **only** file with E. coli or faecal-coliform counts. None of the four files measure *Vibrio cholerae*.
- As such, only one of our datasets is useful for detecting bacterial quantities. However, even then, we cannot predict the cholera quantity as it is not included in any datasets we could find. 

### 1.2 The four datasets share almost no features
- **pH is the only column present in all four.** Turbidity & Temperature appear in three of four. 
- DO / BOD / Ammonia appear in two of four (`WQD.csv`, `Combined_dataset.csv`).
- Combining the tables would result in many missing rows. Additionally, the datasets are of different sizes, weighting some measurements more heavily than others. 

### 1.3 The four labels are not the same quantity
Even if features lined up, the labels do not:
- `full_dataset.csv` → risk band derived from E. coli counts (faecal contamination).
- `water_potability (1).csv` → binary "potable" against an unspecified composite rule.
- `Combined_dataset.csv` → CCME WQI, a Canadian regulatory composite of ten parameters scored vs jurisdiction-specific thresholds (same standards do not apply to other countries).
- `WQD.csv` → fish-pond suitability classes. Fish-ponds do not have the same contamination mechanisms as boreholes. 
We could combine these, but they measure fundamentally different things. If we choose one label, we limit our training data significantly. 

## 2. `full_dataset.csv` — DWS South Africa

The **only viable pathogen-label source**, but with three structural problems:

### 2.1 Extreme target skew
- Distribution of `risk_drinking_no_treatment`: **HIGH 24,283 / Med 943 / low 399** (≈ 95% / 4% / 1%).
- A constant-predict-HIGH classifier scores ~91% accuracy. This is useless as it would result in the unnecessary closure of a borehole. 
- E. coli counts span **0 – 50,000,000 per 100 mL**, eight orders of magnitude, median 678. 

### 2.2 Heavy missingness in the only useful predictor besides pH
- `temperature_c`: **45% missing** (11,531 / 25,625 rows).
- `faecal_coliforms_per_100ml`: largely empty.
- 17.7% of `ecoli_per_100ml` rows are blank — those rows cannot be label-imputed without fabricating the target.
- Our model actually states that missing temperature data is a strong indicator of water quality, but we do not know why a temperature reading might have been missed. This also has no physical interpretation. 

### 2.3 Repeated readings per site over time
- 188 sites, dates 1990-01-02 to 2024-12-19.
- Multiple observations per site over decades → a random train/test split correlates rows across the split (data leakage). The split must be both **grouped by `site_id` AND temporally ordered**.
- On an annual scale, it was however found that incorporating the month/season provides a useful additional parameter for contamination prediction due to increased sewage propagation under rain. 

## 3. `WQD.csv` — Mendeley fish-pond dataset

Smallest file; largest number of file-level defects.

### 3.1 Encoding and header corruption
- File begins with a **UTF-8 BOM** (`EF BB BF`). Naive `pd.read_csv` reads the first column name as `﻿Temp` instead of `Temp`.
- The pH column header is `pH\`` — a literal stray **backtick** in the name. Any code that looks up `df['pH']` or `df['ph']` silently fails or returns the wrong series.
- Column headers contain inconsistent unit suffixes and trailing spaces: `Alkalinity (mg L-1 )`, `Hardness (mg L-1 )` (note trailing space before `)` ).

### 3.2 Turbidity is in **cm**, not NTU
- Header: `Turbidity (cm)`.
- This is a **Secchi/transparency reading**, not a nephelometric measurement. NTU and cm are **not linearly convertible** — the relationship depends on suspended-solid composition, lighting, and viewing geometry.
- Implication: you cannot stack `WQD.Turbidity (cm)` with `full_dataset.turbidity_ntu`. Do not invent a conversion. Drop the column when merging, or model the two as separate features.

### 3.3 Implausible physical values
- First data row: `Temp = 67.45 °C` — outside the liquid-water range for an open pond.
- Other rows show pH values around 3–5 (extremely acidic) inconsistent with aquaculture water.
- These look like either synthetic / simulated data or sensor failure rows. **Cannot tell from the file alone.** Treat with suspicion; do not train an OOD-bounds estimator on these ranges or the field detector will accept anything.

## 4. `Combined_dataset.csv` — Figshare 1940–2023 scrape

### 4.1 Heterogeneous provenance hidden behind a single table
- A `Country` column exists and effectively *is* the provenance flag (Canada, US, EU member states, etc.).
- Different national programs use **different sampling cadences, different lab methods, and different parameter definitions**. CCME WQI is a Canadian regulatory composite — applying it across countries with non-CCME methodologies makes the label inconsistent.
- Window grain differs per source: some rows are point-in-time samples, some are monthly aggregates, some are annual.
- **Action:** treat `Country` (and source-program where derivable) as a `provenance` flag from load, never drop it.

### 4.2 Date column is ambiguously formatted
- Sample row 1: `12-01-1974`. Is this 12-Jan-1974 (DD-MM-YYYY) or 1-Dec-1974 (MM-DD-YYYY)? The file does not declare the format and rows from different country-of-origin systems may use different conventions.
- Implication: any temporal split or time-series feature is wrong until format-by-country is established and parsed explicitly.

### 4.3 Mass
- The file is **~320 MB**. Loading naively will exhaust memory on lightweight environments. Repeated full reads in notebooks cause silent slowdowns that get blamed on the model.

### 4.4 Mismatched parameter list vs the project
- `Combined_dataset.csv` does **not** carry turbidity. The project's minimum-sensor tier is `pH + turbidity + temperature`. Combined is therefore irrelevant to the shipped TinyML feature set — useful only for pre-training a richer auxiliary model.

## 5. `water_potability (1).csv` — Kaggle

### 5.1 Composite label without a published rubric
- `Potability ∈ {0, 1}` is provided without the threshold rules used to compute it. Different rules across rows cannot be ruled out.
- Implication: the label is not the same physical quantity as `risk_drinking_no_treatment` in `full_dataset.csv`. Cannot be treated as additional pathogen labels.

### 5.2 Missingness in the key shared feature
- `pH` is **blank in row 1** of the file, and missing across thousands of rows.
- pH is the *only* feature this dataset shares with the pathogen-track dataset. Missingness on the shared feature destroys the case for using this file as auxiliary pretraining for the field model.

### 5.3 Implausible feature magnitudes
- `Solids` values in the **tens of thousands of ppm**. These are well above potable-water norms (typical drinking water ≤ 1,000 ppm TDS). Either the units are something other than ppm, or many rows are non-potable industrial-influent samples.
- Unit not declared in the column header.

## 6. Cross-cutting issues *that v2 of the model just confirmed*

These are reported here because the v2 notebook (`ML/FirstGradBooster_v2.ipynb`, commit `9a6ed8c`) made them visible — but the **root cause is in the data**, not the model.

### 6.1 Missingness leaks site/era identity
- v2 added a `temperature_missing` indicator to handle the 45% NaN rate in `full_dataset.csv`.
- That indicator became the **top feature by XGBoost gain (9.44)**.
- Interpretation: the model's most decisive splits are on *whether the temperature sensor recorded a value*, not on water chemistry. Missingness is correlated with site / monitoring-era — a provenance feature in disguise. This is a `full_dataset.csv` artefact, surfaced by but not caused by the modelling choice.

### 6.2 Predictive ceiling from three sensors is at the dummy baseline
- With a clean grouped + temporal split (61 train sites, 127 held-out test sites, pre-2015 vs post-2015), XGBoost macro-F1 = **0.324**; always-predict-HIGH dummy = **0.317**.
- A 0.007 gap on macro-F1 is within resampling noise.
- This is a **data-information ceiling**, not a model-tuning failure. pH + turbidity + temperature alone, on the labels that exist in `full_dataset.csv`, do not separate the risk bands. Any next step needs **more or different features**, or a different label definition (e.g. binary HIGH-vs-not, ordinal log-bands).

## 7. What this means for the project

- The "minimum viable tier" (pH + turbidity + temperature) is supportable from `full_dataset.csv` alone — **but it appears to be at or near a predictive ceiling on the current label.** Adding sensors (DO / BOD / ammonia) requires importing the *features only* from `WQD.csv` or `Combined_dataset.csv` while keeping the pathogen label from `full_dataset.csv`. There is no row-level overlap to do a supervised join, so this must be cast as transfer learning / multi-task learning, not naive concatenation.
- `WQD.csv` and `water_potability (1).csv` should be treated as **suspect** until §3.3 and §5.3 are resolved. Both contain values that may be synthetic, mislabelled, or industrial.
- Before any further modelling: add a `provenance` column at load time on **every** dataset, run physical-plausibility checks per column, and document unit conventions in a unit registry. Without these three steps, every downstream result is contaminated by the issues above.

## Appendix: quick reproductions

```bash
# Confirm the BOM and stray backtick in WQD.csv:
head -1 Data/WQD.csv | xxd | head -1
# → 00000000: efbb bf54 656d 702c 5475 7262 6964 6974   ...Temp,Turbidit
head -1 Data/WQD.csv
# → ...pH`,Alkalinity (mg L-1 ),...

# Confirm full_dataset class imbalance:
python -c "import pandas as pd; print(pd.read_csv('Data/full_dataset.csv')['risk_drinking_no_treatment'].value_counts())"

# Confirm Combined date ambiguity:
head -2 Data/Combined_dataset.csv

# Confirm potability missing pH and large solids:
head -2 'Data/water_potability (1).csv'
```
