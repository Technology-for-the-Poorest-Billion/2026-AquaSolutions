# issues_v3.md — Phase-2 Risk Register

A risk register for the **application + communications + linkage** phase of the project (Generation-1 SMS-to-SQLite pipeline + the eventual server-side ML built on the data it collects).

This document is the *current* risk register. Earlier risk material:
- `issues_v2.md` — dataset-level issues from the four phase-1 datasets. Still valid for the explanation of *why* phase 1 hit a predictive ceiling.
- `ISSUES_v1.md` — archived phase-1 register (on-device TinyML approach). Items A1, A4, A5, B1, B2, C3, C4, D1, D2 from that file are carried forward below in adapted form.

Items are ordered roughly by severity. Each has the **risk**, **why it matters**, and a **mitigation**.

---

## A. Framing risks (carried forward, still load-bearing)

### A1. The device is not a cholera detector — and the system is not a diagnostic
- **Risk:** Reviewers, funders, supervisors, or end-users misread the project as "a cheap sensor that detects cholera."
- **Why it matters:** No part of the system measures *Vibrio cholerae*. The sensor measures faecal-contamination-conducive *conditions* (pH, turbidity, temperature, rainfall, plankton/chlorophyll proxy). The SMS layer collects illness reports, not microbiological diagnoses. Marketing it as cholera detection would mislead public-health users and invites well-deserved reviewer rejection.
- **Mitigation:** Honest framing in every artefact — code comments, commit messages, model card, dashboard, auto-reply text, supervisor-facing presentation. The phrase used should be "faecal-contamination risk and outbreak-conducive conditions" plus "community-reported illness signal." See CLAUDE.md "Non-negotiable framing."

### A2. ML deferral risk
- **Risk:** Generation 1 is plumbing + label generation, *not* live inference. Supervisors expecting "show me the classifier" may interpret the absence of a deployed model as the project under-delivering.
- **Why it matters:** The project has pivoted *because* no existing dataset supported a defensible classifier. The deliverable is now the data-collection apparatus, with the ML pipeline specified but not yet trained. This must be communicated, not concealed.
- **Mitigation:** PLAN.md presents the system + pipeline as the deliverable. Stand up the **ML pipeline against a proxy dataset** (`full_dataset.csv`, the open California FIB data) to demonstrate the imbalance-handling and leakage-avoidance discipline *before* real sensor data exists. See `App/cholera_sensor_ml_approach.md` §9.5.

---

## B. Labelling and data-quality risks (new and structural)

### B1. SMS reports give noisy timing, not exposure timestamps
- **Risk:** A community member texts when they are symptomatic. Cholera incubation is hours to ~5 days. The trailing window labelled "unsafe" therefore conflates *symptom-onset time* with *exposure time* and may be off by several days.
- **Why it matters:** The label is structurally noisy on the time axis. Any model trained on it must tolerate this; tightly-tuned models will over-fit to the noise.
- **Mitigation:** Label a *window*, not a point. The window length is the meaningful design choice (see `App/backend/labels.py`). The model uses **lagged + rolling features** over the window so the model itself spans plausible incubation lags. Document the assumed exposure-vs-onset gap and treat it as a hyperparameter.

### B2. Source attribution from a phone number is ambiguous
- **Risk:** A reporter may drink from multiple sources during the exposure window; the SMS contains only one station number. Other reporters may not know their station number and text a free-form description.
- **Why it matters:** Labelled positives are attributed to a *specific station*, but the actual exposure may have been at a different one. False-positive labels on innocent stations and false-negative labels on the real one.
- **Mitigation:** Treat the station label as *probabilistic*, not certain. In the future, allow multi-station reports (parse "stations 4, 7"); in the meantime, accept the label noise and document it. Do not over-weight individual reports — require multiple corroborating reports before declaring a station unsafe in the user-facing UI.

### B3. Under-reporting makes "negatives" unreliable
- **Risk:** Most illness goes unreported. A window with no SMS does not mean "no illness occurred" — it means "no one texted us."
- **Why it matters:** Naive negative sampling (every non-reported window = negative) trains the model on false negatives.
- **Mitigation:** **Matched case–control sampling** (`App/cholera_sensor_ml_approach.md` §6) — sample negatives from the same sites and seasons as positives, not from every gap.

### B4. Cold start — no positives until reports arrive
- **Risk:** The system has to function for weeks or months before any ML can train; reviewers and stakeholders need to see something working *now*.
- **Why it matters:** A device that must collect for two years before predicting anything is a hard sell.
- **Mitigation:** (a) Demo the *pipeline* and the *labelling logic* rather than the model. (b) Anchor on external environmental-suitability models and refine them with our data, rather than starting from scratch. (c) Use a proxy dataset (DWS / FIB) to validate the model code before real data exists.

### B5. Predictor missingness recurs in the new pipeline
- **Risk:** Sensors drop offline; network is intermittent; some readings will be missing.
- **Why it matters:** Phase 1 found that *missingness itself* leaked site/era identity into the model (issues_v2.md §6.1). The same will happen here unless handled.
- **Mitigation:** Median/KNN-impute *predictors* with explicit **missingness-indicator features**; never impute the *label*; carry a `provenance` column on every reading (which sensor unit, firmware version, network path).

---

## C. Application + communications risks (new and critical)

### C1. Twilio cost and abuse
- **Risk:** Twilio bills per inbound + outbound SMS. Trial credit drains fast; production cost scales with reporter volume. An abuser can drain credits by texting in a loop, or trigger expensive outbound flows.
- **Why it matters:** A demo or pilot can be silently disabled by exhausted credit. Worse, real reports may stop being processed.
- **Mitigation:** (a) Rate-limit inbound SMS per phone number at the Flask layer. (b) Bound outbound auto-reply length and frequency. (c) Set Twilio account-level spending caps. (d) Monitor balance and alert when low.

### C2. Twilio webhook spoofing
- **Risk:** If the `/sms` endpoint is reachable from the internet and signature validation is off, anyone who guesses or scrapes the URL can POST fake SMS payloads, injecting false illness reports.
- **Why it matters:** Fake reports flip stations to "unsafe", erode community trust, and corrupt the training labels.
- **Mitigation:** **Twilio request-signature validation must be enabled** on every internet-reachable deployment. Use `TwilioRequestValidator` (twilio-python) and the Auth Token. The `/sms` route should reject any unsigned or wrongly-signed request with 403.

### C3. ngrok URL instability in development
- **Risk:** The free ngrok tier rotates the public URL each restart. The Twilio webhook URL has to be re-pasted each time.
- **Why it matters:** A forgotten re-paste mid-demo silently kills the SMS leg.
- **Mitigation:** Document the restart procedure in `App/DEMO.md`. For anything beyond demo-day, switch to a stable host (Railway) or a paid ngrok subdomain.

### C4. Sensor endpoint authentication is brittle
- **Risk:** `/ingest` is gated by a shared `DEVICE_SECRET` header. If any field device is captured, the secret leaks; rotating across N devices is operationally expensive.
- **Why it matters:** A leaked secret lets an attacker inject fabricated sensor readings to mask a real outbreak or fake one.
- **Mitigation:** For Gen-1, the shared secret is acceptable. For Gen-2, move to per-device keys (HMAC of payload + nonce + device-id, key rotation via a registration endpoint). Document the secret-rotation procedure.

### C5. Station-ID parsing is a UX/strictness trade-off
- **Risk:** A strict parser ("station ID must be a single integer") rejects messages like "Station 4 needs help" or "stn 4". A lenient parser ("first integer in the message") mislabels jokes ("I drank 2 glasses").
- **Why it matters:** Real users send free-form SMS in the language they're comfortable with. Lossy parsing throws away signal; lossy in the other direction injects noise.
- **Mitigation:** Start strict (single integer, optional whitespace, leading "station" word allowed). Log every rejected message for human review. Loosen iteratively based on what real reporters actually send.

### C6. Auto-reply content carries health-advice legal exposure
- **Risk:** A reply like "drink boiled water" is the wrong advice if the contamination is chemical (e.g. arsenic, fluoride). A reply implying medical diagnosis is regulated speech in many jurisdictions.
- **Why it matters:** Bad advice harms the user; regulated speech exposes the project to liability.
- **Mitigation:** Auto-reply is **acknowledgement only** ("report received, thank you"), not advice. Treatment recommendations (per `App/Ideation.md`) move to a human-mediated channel or a clearly-disclaimed app screen, not to SMS.

### C7. Multi-language reply is unsolved
- **Risk:** Per `App/Ideation.md`, the deployment context needs replies in one of the local languages (e.g. Zimbabwe has 16 official languages; Bangladesh has Bangla as primary). Detecting language from a short SMS is unreliable.
- **Why it matters:** An English-only reply silently excludes the population the system is meant to serve.
- **Mitigation:** Defer real multi-language until language preference is captured on first contact ("Reply 1 for English, 2 for Shona, 3 for Ndebele"). For Gen-1 demo, English-only is acceptable; flag this prominently.

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
