# Recommended Approach: Sensor-Based Data Collection and ML for Cholera Risk Prediction

*Summary of the pivot from "modelling existing data" to "collecting quality data via low-cost sensors, linking it to health records, and predicting outbreak risk."*

---

## 1. The problem we are actually solving

Our three existing datasets each fail for a different reason:

- **WQD.csv** measures aquaculture/fish-pond chemistry (DO, BOD, plankton, ammonia). Its "Water Quality" label is an aquaculture-suitability score, not a human disease outcome — there is no cholera signal in it to find.
- **water_potability.csv** (Kaggle) is widely understood to be synthetic/imputed, with no genuine correlation structure between features and the potability label. The absence of a regression is a property of the data, not a modelling failure on our part.
- **full_dataset.csv** (South African DWS microbiological data) is the most useful — it contains E. coli and faecal coliforms, the correct faecal–oral indicators — but it is monitoring data with **no linked health outcomes**. How can we know whether people were contaminated from this source? It is also flawed by a strong skew to "HIGH" risk water. 

The genuine bottleneck is therefore **data that pairs environmental measurements with disease outcomes**, at a useful spatial and temporal resolution. This challenge has become our new focus and takes priority before any ML algorithm can be implemented. 

## 2. What a cheap sensor can and cannot detect

This shapes the entire design and must be stated honestly up front.

- **A low-cost sensor will not detect *Vibrio cholerae*.** Nor do pH/turbidity/temperature/DO probe measures it.
- **What cheap sensors *can* measure are proxies:**
  - **Faecal-contamination indicators** — E. coli / faecal coliforms are the gold-standard proxy, but in-situ detection needs optical-fluorescence or electrochemical incubation methods that take 3–24 hours and are costly.
  - **Conditions conducive to outbreaks** — temperature, turbidity, and a plankton/chlorophyll proxy are epidemiologically meaningful covariates. *V. cholerae* prevalence falls below ~20 °C; chlorophyll is a known strong predictor in the remote-sensing literature.

**Framing rule:** the device predicts *faecal-contamination risk and conditions conducive to outbreaks*, and the ML links those patterns to outbreak records. It is **not** "a cheap sensor that detects cholera." This must be made clear for the time being. 

## 3. Sensor targets (epidemiologically defensible, buildable)

1. **Rainfall** and seasonal changes were seen to improve prediction of water quality. Rain means faecal contamination is more likely. 
2. **Water temperature** — cheap, reliable, tied to *V. cholerae* survival.
3. **Plankton / turbidity / chlorophyll proxy** — an optical measurement; the most defensible "biological reservoir" signal a low-cost device can plausibly capture.

A faecal-indicator (E. coli) capability is the highest-value addition but the hardest and slowest. For the time being, we will stick to proxies. 

## 4. Two problems

1. **Health-records linkage and governance.** Connecting sensor data to medical records requires data governance, ethics approval, and a functioning reporting system. Key unknowns: who owns the health data, what spatial/temporal resolution case reports have, and whether cases can be geolocated to specific sources.

2. **Cold-start and class imbalance.** Outbreaks are rare relative to routine safe-water readings, so we face severe imbalance and a long collection period before a model is trainable. A device that must collect for two years before predicting anything is a hard sell.
   - *Mitigation:* Rather than learning from scratch, we can develop a simple model based on benchmarks and thresholds to begin with. Then, we can push new models to the microcontroller when data is ready.

## 5. Reframing the unit of analysis: the 7-day exposure window

- **Why?** WHO 5 day incubation period for cholera. Add two days for a margin, giving a 7 day window of data that should be labeled for each case. This will likely need to follow an unsupervised learning appraoch as we don't know when exactly the contamination occurs in that period. 
- **Do NOT** keep only the windows that preceded a case and discard the rest. That deletes the low risk class entirely. A model cannot learn a decision boundary with only positives — the imbalance "vanishes" only because the problem vanishes. We would end up with the same issue as in the full_dataset.csv case. 

### The labelling reality this exposes
Labelling a window as positive presumes we can tie "someone was contaminated" back to specific days at a specific source — which *is* the core challenge. In practice a clinic case gives a person and an approximate onset date, but not the source or exact exposure moment. Positive labels will therefore be noisy in **both** source assignment and timing, and under-reporting means some "negative" windows actually contain unobserved positives. The pipeline must be robust to label noise. This is probably the hardest technical challenge going forward and must be really thought through. 

---

## References

- Leo, Luhanga & Michael (2019), *Machine Learning Model for Imbalanced Cholera Dataset in Tanzania* — ADASYN + PCA; imbalance-aware metrics; XGBoost selected.
- Amshi et al. (2024), *How can machine learning predict cholera* (J. Water & Health) — CORP model; DBSCAN + SMOTE + NMF.
- Adewumi (2025 preprint, Research Square), *AI for Cholera Outbreak Prediction … Federated and Privacy-Preserving ML* — model ladder, TinyML edge deployment, federated learning framing. *(Preprint; internal performance figures inconsistent — use for method/structure, not for reported metrics.)*
- *Contrasting Epidemiology of Cholera in Bangladesh and Africa* (J. Infect. Dis., 2021) — the predictability split underpinning site selection.
- WHO / ECDC cholera situation reports (2024–2026) — global burden and seasonality context.

*Document reflects the working conclusions of an ongoing discussion; figures and framing should be revisited as the linkage partner and scope are confirmed.*
