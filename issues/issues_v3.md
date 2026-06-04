# issues_v3.md — Phase-2 Risk Register

This is a live document of the risks associated with the implementation of the data collection and management system (Week 2 onward). 

This document is the *current* risk register. Earlier risk material:
- `issues_v2.md` — dataset-level issues from the four Week 1 datasets. 
- `ISSUES_v1.md` — archived Week 1 register (on-device TinyML approach). Items A1, A4, A5, B1, B2, C3, C4, D1, D2 from that file are carried forward below in adapted form.

Items are ordered roughly by severity.

---

## A. Framing risks (carried forward, still load-bearing)

### A1. The device is not a cholera detector — and the system is not a diagnostic
- We cannot present our new product as a detector. Rather, it is an approach for compiling reliable data in order to, hopefully, create a predictor in the future. 
- No part of the system measures *Vibrio cholerae*. The sensor measures faecal-contamination **proxies** (pH, turbidity, temperature, rainfall, ORP, etc.). The SMS and medical layers collect illness reports, not microbiological diagnoses. Marketing it as cholera detection would mislead public-health users and invites well-deserved reviewer rejection.
- We should ensure that the model characteristics are made clear when presenting the product to external entities, particularly due to the pivot in objective. 

### A2. ML deferral risk
- The project has pivoted *because* no existing dataset supported a strong classifier. The deliverable is now the data-collection apparatus, with the ML pipeline designed but not yet trained. This must also be made clear to others. We cannot know how a state-of-the-art model will perform without first providing it with the best data. Only then will we be able to fully assess the feasibility of ML algorithms for water quality inference.

---

## B. Labelling and data-quality risks (new and structural)

### B1. SMS reports give noisy timing, not exposure timestamps
- A community member texts when they are symptomatic. Cholera incubation can take hours to ~5 days. The trailing window labelled "unsafe" therefore confounds *symptom-onset time* with *exposure time* and may be off by several days.
- Tightly-tuned models will struggle. We must make the model aware of the range of possibilites for incubation and use other medical indicators to reinforce our labeling window. 
- The model uses **lagged + rolling features** over the window so the model itself spans plausible incubation lags. Document the assumed exposure-vs-onset gap and treat it as a hyperparameter.

### B2. Source attribution from a phone number is ambiguous
- A reporter may drink from multiple sources during the exposure window. As such, a complete dictionary must be provided in the roll out of the product for SMS communication. We need to be able to understand, in a few words/numbers, where the person has been drinking and what their symptoms are. 
- Treat the station label as *probabilistic*, not certain. Allow multi-station reports (parse "stations 4, 7"). Do not over-weight individual reports. Require multiple corroborating reports before declaring a station unsafe in the user-facing UI. 

### B3. Under-reporting makes "negatives" unreliable
- Most illness goes unreported. A window with no SMS does not mean "no illness occurred" — it means "no one texted us."
- Naive negative sampling (every non-reported window = negative) trains the model on false negatives. This will result in the same skewing issue defined in v1 and v2. 
- Sample negatives from the same sites and seasons as positives, not from every gap.
- We also need to consider how we can incentivise people to always report illness or if this is better done via VHWs and clinics. 

### B4. Cold start — no positives until reports arrive
- The system has to function for weeks or months before any ML can train; reviewers and stakeholders need to see something working *now*.
- A device that must collect for two years before predicting anything is a hard sell.
- During the cold start period, we will implemenet a rudimentary/reliable model using baselines driven by WHO standards. As data is collected, we will be able to test a general model for later implementation. 

### B5. Predictor missingness recurs in the new pipeline
- Sensors drop offline; network is intermittent; some readings will be missing.
- Median/KNN-impute *predictors* with explicit **missingness-indicator features**; never impute the *label*; carry a `provenance` column on every reading (which sensor unit, firmware version, network path).
- XGBoost is intended to be robust against single-sensor failure.

---

## C. Application + communications risks (new and critical)

### C1. Twilio cost and abuse
- Twilio bills per inbound + outbound SMS. As such, costs scale with client volume.
- Additionally, free trial credits can slip away easily. A demo or pilot can be disabled by exhausted credit. Worse, real reports may stop being processed.
- For the time being, we need Twilio spending caps. However, in the long run, we need to look at the cost/revenue structure to determine how to account for this variable cost. 

### C2. Sensor endpoint authentication is brittle
- `/ingest` is gated by a shared `DEVICE_SECRET` header. If any device is stolen, the secret leaks; rotating across N devices is operationally expensive.
- We could move to per-device codes. However, this not an issue into the product is deployed at scale. 

### C3. Station-ID parsing is a UX/strictness trade-off
- A strict parser ("station ID must be a single integer") rejects messages like "Station 4 needs help" or "stn 4". A lenient parser ("first integer in the message") mislabels jokes ("I drank 2 glasses of water").
- Real users send free-form SMS in the language they're comfortable with. In the first case, we could lose the signal. In the second case, we inject inappropriate data into our labeled training set. 
- We need a strict dictionary to begin with that tolerates only compatible messages. In the long run, we may want to use an LLM API for message interpretation, providing more flexibility.

### C4. Auto-reply carries health-advice liability
- A reply like "drink boiled water" is the wrong advice if the contamination is chemical (e.g. arsenic, fluoride). A reply implying medical diagnosis is regulated speech in many jurisdictions. If the advice is wrong and the person gets ill as a result, we could be liable. 
- Auto-reply should be **acknowledgement only** ("report received, thank you"), not advice. They are intended to keep users in the loop, not to provide consultation (as was initially the intention in Week 1). 

### C5. Multi-language reply is unsolved
- Per `App/Ideation.md`, the deployment context needs replies in one of the local languages (e.g. Zimbabwe has 16 official languages. Detecting language from a short SMS is unreliable.
- We could use regional data to inform the language used. We can also provide an option (e.g. "Reply 1 for English. Reply 2 for Shona...). 

### C8. SMS cost and deliverability for the reporter
- Even when receipt is free for the user, the reporter pays per-text in most networks. Some countries block webhook-originated SMS or require registered sender IDs (ZBC in Zimbabwe). This further harms the incentive structure for people to self-report illness. 
- Investigate per-country sender-ID rules before any pilot.
- It is probably easiest to get VHWs registered sender IDs and have them report on illness while they do their rounds. 

---

## D. Linkage and governance risks (new and existential)

### D1. No identified clinical-data linkage partner
- Need a partner to ensure validated healthcare data. 
- Scope this *before* hardware. Reach out early; first letter of intent gates everything downstream.
- A partner (e.g. a government) is key to this product's deployment. 

### D2. IRB / ethics-approval timelines
- Health-data research typically requires institutional review board approval that can take months. 

### D3. Cross-border data-transfer constraints
- Zimbabwe, the EU, and the UK each have data-protection regimes restricting transfer of personally-identifying or health-related data across borders.
- A central server outside the country of collection may be illegal under local law. We would need to set up an HQ in Harare. This has several benefits. 

### D4. Reporter consent and phone-number storage
- Storing reporter phone numbers without an explicit consent flow may breach data-protection law in the deployment country.
- Phone numbers are personally identifying; linking them to illness reports creates a sensitive record.
- How can we obtain consent over SMS? This would allow us to track the health of individual people. 

### D5. Case geolocation is heuristic, not precise
- Clinic records say where a patient *lives*, not where they *drank*. The eventual ML's location label will rely on a heuristic ("nearest water source"), which is wrong sometimes. Part of the product's deployment will be a database of the locations/sources of peoples' drinking water. This must be very accurate for the dataset to be successful. 
- Where feasible, the SMS reporting layer *is* the source attribution — the reporter names the station they used.
- Defaulting to clinical records and estimating water drinking locations is the worst-case scenario. 

---

## E. ML pipeline risks (when ML eventually runs)

These were specified in `App/cholera_sensor_ml_approach.md` §6 and are reproduced here so they live in the risk register too. There are many more, but this is a live document and we will build off these ML challenges when we eventually get to that stage in the build. 

### E1. Site / season leakage
- **Risk:** Random train/test splits put correlated rows from the same site across the split, inflating accuracy.
- **Mitigation:** Grouped + temporal split (by `site_id` AND by date). This results in an honest test accuracy. 

### E2. Imbalance-blind evaluation
- Example: With ~7% positives, "always predict no outbreak" scores ~93% accuracy and is useless.
- We need balanced data and uncertainty values for the outputs. The label structure chosen should favour granularity of output, rather than simplicity of training. 

---
