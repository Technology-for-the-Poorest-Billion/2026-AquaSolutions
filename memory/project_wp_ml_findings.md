---
name: project-wp-ml-findings
description: Key ML findings from water_potability_eda_V1.ipynb — model choice, dominant feature, proof-of-concept result
metadata:
  type: project
---

XGBoost is the best-performing model on the water potability dataset (macro-F1 = 0.598 vs 0.495 LogReg vs 0.379 Dummy). pH is the dominant feature by both gain and weight importance. The result is treated as proof-of-concept that sensor-based chemical proxies can classify water safety above a meaningful baseline.

**Why:** Δ macro-F1 = +0.149 over the 3-feature grouped+temporal baseline (0.449), clearing the 0.10 "STRONG" threshold even accounting for the more optimistic random split used here.

**How to apply:** When discussing model selection or sensor BOM with Allen Chafa, lead with XGBoost + pH primacy. The 0.598 figure is an *optimistic upper bound* (random split, no site/date grouping) — frame it as proof-of-concept, not field-deployment performance. The honest field estimate is likely lower once grouped+temporal validation is applied to real collected data.
