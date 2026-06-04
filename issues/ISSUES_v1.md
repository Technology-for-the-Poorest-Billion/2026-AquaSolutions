# ISSUES_v1.md — Archived (phase 1)

> **Week 1: 2026-05-15-2026-05-22, Archived: 2026-05-27.** This document describes the issues with the first attempt at improving Mr.Chafa's project (on-device TinyML classifier trained public datasets). It is preserved for historical context.
>
> This "Week 1" approach was abandoned after the trained models performed poorly. These models are under the ML folder where various experiments were run to explore the capabilities of the XGBoost model. The `App/cholera_sensor_ml_approach.md` file rationalises the pivot made during "Week 2". 
>
> - **Dataset-level issues** are consolidated in [`issues_v2.md`](issues_v2.md).
> - **Phase-2 risks** (application layer, SMS communications, linkage, governance) live in [`issues_v3.md`](issues_v3.md).
>
> Items A1, A4, A5, B1, B2, C3, C4, D1, D2 below are still relevant to the new approach and are carried forward into `issues_v3.md`. The rest are specific to the on-device TinyML approach and no longer constrain the project.

---

# ISSUES.md — Forecast of Potential Issues (based on dataset observation)

Issues are ordered roughly by severity. Many of these were project-defining, forcing us to direct our efforts towards data collection.

## A. Data and labelling issues (most severe)

### A1. No dataset measures cholera — and only one measures *any* pathogen
- Only `full_dataset.csv` (25,625 rows) contains a microbial measurement at all (E. coli + faecal coliforms). The other three provide WQI or proxy values. A model cannot learn to detect cholera quantity without data for it. We could change the output quantity to E. coli volume, but we want to detect cholera as it is the most prevalent waterborne disease in Zimbabwe. 

### A2. The four datasets share almost no predictors
- The only feature common to all four is **pH**. Turbidity and temperature appear in three of four. As such, it is hard to train a model on all the parameters we desire to incorporate (additionally including ORP, UV absorption, etc.). Combining the datasets would result in many missing values. We could train off the most prominent variables (pH, turbidity, and temperature), but more granularity is required for a successful classifier. 

### A3. Extreme target skew and class imbalance
- E. coli spans the range 0–50,000,000 /100 mL (median 678); ~95% of `risk_drinking_no_treatment` labels are "HIGH" (24,283 HIGH vs 943 Med vs 399 low). A model could predict "HIGH" for every input and achieve a 95% accuracy. A nonlinear approach to the risk bands might be required, for example by using CCME values.

### A4. Missing data
- 17.7% of E. coli rows are blank in `full_dataset.csv`; faecal coliforms are largely empty; potability has missing pH/sulfate/trihalomethanes. Deleting the rows with missing values would greatly shrink the dataset. Subsituting in synthetic data points is tricky. 

### A5. Unit and convention mismatches
- Turbidity in **cm (transparency)** in WQD vs **NTU** in others; concentrations per 100 mL vs per L; WQD's `pH`` column has a stray backtick; a BOM prefix on WQD's header. These values must be standardised. Many of these are standard conversions, but some of them must be investigated further.

### A6. Implausible / out-of-range values
- WQD shows Temp values like 67°C, pH ~3–5, or potability solids in the tens of thousands that look synthetic or physically infeasible. These values will mislead the model. Before training, we need to implement a feasibility-checker to remove suspicious datapoints.

## B. Modelling issues

### B1. Repeated site measurements
- 'full_dataset.csv` has many repeated readings per `site_id` over time. A random split puts correlated rows in both train and test. A model can achieve a high performance just by having "seen" the inputs in the test set before in the "training" set. Split the test and train data by time so that values are not repeated.

### B2. Weak predictive ceiling from physico-chemical features alone
- pH/temperature/turbidity are only loosely coupled to bacterial counts; the achievable accuracy may be modest. We saw that Mr.Chafa's trial for his initial design was insuccessful. While  these features are important, we know they don't tell the whole picture. More sensors will be needed, most of which measure variables that are not included in these datasets. We also might want to consider the weather on water contamination, in which case we should use temporal/seasonal data. 

### B3. Overfitting on the small, imbalanced label set
- Effective labelled rows after cleaning may be well under 25k and dominated by one class. More advanced ML techniques will be required to avoid overfitting (highly probable with these datasets).

## C. TinyML / deployment issues

### C1. Footprint and latency budget
- Chosen model exceeds flash/RAM or latency on a Cortex-M0+/ESP32-class device. Need to train a smaller model. How do we compress it?

### C2. Sensor noise and drift in the field
- Cheap pH/turbidity sensors are noisy and drift; lab-quality training data won't reflect this. Train/evaluate with injected sensor noise; add input smoothing; document recalibration cadence. The XGBoost algorithm might be able to handle some drift, while a background check on the mean sensor values over time could be useful in quantifying the drift. 

### C3. Out-of-distribution inputs in the field
- Field water parameter values outside training ranges might trigger model failures. We can send a team to collect a sample or label the point as out of the ordinary. 

## D. Process and safety issues

### D1. Misuse / over-trust of a proxy model
- A "safe" prediction is acted on as a guarantee of potable water, risking real harm to people if the prediction is wrong. The thresholds should be conservative and the proxy-based prediction nature of this product must be disclosed. 

### D2. Timeline risk in a 3-week sprint
- We cannot responsibly develop this product for deployment in three weeks. However, we can try to develop a demo or proof of concept for feedback and feasibly assessment. 

### D3. Licensing and source heterogeneity
- The four sources (DWS South Africa, Kaggle, Figshare, Mendeley) carry different licences and citation requirements. For now, we will keep them all linked in Data/Data.md for reference.  
