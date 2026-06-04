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

### C7. Multi-language reply is unsolved
- Per `App/Ideation.md`, the deployment context needs replies in one of the local languages (e.g. Zimbabwe has 16 official languages. Detecting language from a short SMS is unreliable.
- We could use regional data to inform the language used. We can also provide an option (e.g. "Reply 1 for English. Reply 2 for Shona...). 

### C8. SMS cost and deliverability for the reporter
- **Risk:** Even when receipt is free for the user, the reporter pays per-text in most networks. Some countries block webhook-originated SMS or require registered sender IDs (sender-ID registration in Bangladesh, ZBC in Zimbabwe).
- **Why it matters:** A reporter who pays to send a report and gets no reply, or whose report is dropped at the carrier, will not report again.
- **Mitigation:** Investigate per-country sender-ID rules before any pilot. Provide a fallback channel (USSD, WhatsApp Business, a community health worker phoning in) — flagged as out of scope for Gen-1 but on the roadmap.

---

## D. Linkage and governance risks (new and existential)

### D1. No identified clinical-data linkage partner
- **Risk:** The entire premise of the eventual ML — pairing sensor readings to clinically-confirmed cases — requires a partner with case-level data and the legal/ethical authority to share it.
- **Why it matters:** Without a partner, SMS reports are *self-reported symptoms*, not confirmed cases. The label quality drops a tier; the project remains useful but cannot be presented as outbreak prediction.
- **Mitigation:** Scope this *before* hardware. **icddr,b in Dhaka** is the natural candidate. Reach out early; their letter of intent gates everything downstream. If no partner is secured, reframe the deliverable as a *community-symptom early-warning* system explicitly, not an outbreak predictor.

### D2. IRB / ethics-approval timelines
- **Risk:** Human-subject health-data research typically requires institutional review board approval that takes weeks-to-months. The project submission is 2026-06-11.
- **Why it matters:** No live patient-data work happens before the submission date. The deliverable must be defensible *without* linked clinical data.
- **Mitigation:** Generation 1 deliberately avoids touching patient records — community-reported symptoms via SMS are the user's own data, voluntarily disclosed. Confirm with supervisors whether even this requires consent infrastructure (it likely does, but at a much lower bar than clinical records).

### D3. Cross-border data-transfer constraints
- **Risk:** Bangladesh, Zimbabwe, the EU, and the UK each have data-protection regimes restricting transfer of personally-identifying or health-related data across borders.
- **Why it matters:** A central server outside the country of collection may be illegal under local law.
- **Mitigation:** **Federated learning + differential privacy** (per `App/cholera_sensor_ml_approach.md` §4) is the structural answer: institutions train locally and share only gradient updates. Build the pipeline assuming this from the start, even if the demo runs centrally for now.

### D4. Reporter consent and phone-number storage
- **Risk:** Storing reporter phone numbers without an explicit consent flow may breach data-protection law in the deployment country.
- **Why it matters:** Phone numbers are personally identifying; linking them to illness reports creates a sensitive record.
- **Mitigation:** Hash phone numbers at rest (irreversible mapping for de-duplication only); state the data-use policy in the auto-reply ("By texting in you consent to your station and timestamp being recorded; reply STOP to opt out"); offer a working STOP keyword.

### D5. Case geolocation is heuristic, not precise
- **Risk:** Clinic records say where a patient *lives*, not where they *drank*. The eventual ML's location label will rely on a heuristic ("nearest water source"), which is wrong sometimes.
- **Why it matters:** Source-attribution noise propagates into both training labels and downstream alerts.
- **Mitigation:** Where feasible, the SMS reporting layer *is* the source attribution — the reporter names the station they used. Treat clinic-record geolocation as a fallback / corroborative signal, not the primary source.

---

## E. ML pipeline risks (when ML eventually runs)

These were specified in `App/cholera_sensor_ml_approach.md` §6 and are reproduced here so they live in the risk register too.

### E1. Resampling leakage
- **Risk:** Oversampling (SMOTE / ADASYN) applied before the train/test split lets synthetic copies of test points leak into training, producing inflated accuracy.
- **Why it matters:** Published cholera-prediction papers report suspiciously high scores (e.g. 99.6% CORP accuracy) that are almost certainly this artefact.
- **Mitigation:** Resample on the **training fold only**, inside cross-validation. Outlier removal happens *before* resampling so synthetic samples are not generated around mislabelled points.

### E2. Site / season leakage
- **Risk:** Random train/test splits put correlated rows from the same site across the split, inflating accuracy.
- **Why it matters:** Phase-1 datasets had this problem and it masked the real predictive ceiling for months.
- **Mitigation:** Grouped + temporal split — by `site_id` AND by date. Honest accuracy, even if it's lower.

### E3. Imbalance-blind evaluation
- **Risk:** With ~7% positives, "always predict no outbreak" scores ~93% accuracy and is useless.
- **Mitigation:** Report **balanced accuracy, macro-F1, positive-class recall, and PR-AUC**. Never raw accuracy.

### E4. Quantisation impact on minority recall (carried forward, deferred)
- **Risk:** If a *future* on-device flavour of this system ever runs (Gen-3+), int8 quantisation can disproportionately hurt minority-class recall.
- **Mitigation:** Evaluate the *quantised* model specifically; compare float vs int8 confusion matrices. Not relevant in Gen-1 (no on-device inference).

---

## F. Process risks

### F1. Demo failure under time pressure
- **Risk:** Live demo with Twilio + ngrok + Flask + SQLite has multiple network round-trips; any single one failing (rotated ngrok URL, expired Twilio trial credit, wrong webhook config) breaks the demo.
- **Mitigation:** `App/DEMO.md` documents the failure modes most likely to bite. Have a recorded-screencast fallback ready in case the live demo fails.

### F2. Reproducibility and provenance
- **Risk:** Ad-hoc cleaning and ad-hoc collection metadata make results impossible to reproduce or audit.
- **Mitigation:** Versioned pipeline, fixed seeds, dataset checksums, `provenance` column on every collected reading and every illness report.

### F3. Scope creep into the user-facing app
- **Risk:** `App/Ideation.md` sketches an ambitious multi-language low-literacy UI with treatment recommendations and technician notifications. Most of that is out of scope for Gen-1.
- **Mitigation:** Treat `Ideation.md` as the *vision*, not the *Gen-1 build*. Gen-1 is the pipeline + a debug dashboard, nothing more.

### F4. Stakeholder expectation drift between deadlines
- **Risk:** Between 2026-06-01 (interim) and 2026-06-11 (submission), supervisors may push the system back toward the old "deploy a classifier in Zimbabwe" framing.
- **Mitigation:** The pivot rationale (`App/cholera_sensor_ml_approach.md`) is the rebuttal document. Use it.

---

## Resolved items

- Ephemeral Railway filesystem wiping the demo DB on every redeploy.
  RESOLVED 2026-05-28 by migrating to Railway Postgres. See plan
  docs/superpowers/plans/2026-05-28-sqlite-to-postgres-migration.md.
