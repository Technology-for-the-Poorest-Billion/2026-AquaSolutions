# PLAN.md — v2: Data-Collection Apparatus + Server-Side ML (deferred)

> v1 (the 10-day on-device TinyML plan) is archived in "Plan_v1.md". The pivot rationale lives in "App/cholera_sensor_ml_approach.md". Read those two if any decision below seems to come out of nowhere. This document provides the outline for the steps taken under the new pivoted objective (reliable data collection). 

## 0. Where we are and what we're building

The project is no longer "ship an on-device classifier trained on the existing datasets." After grouped + temporal evaluation, three-sensor classification on `full_dataset.csv` was indistinguishable from a majority-class dummy (macro-F1 ≈ 0.32, "issues/issues_v2.md" §6.2). That ceiling is in the *labels*, not the *model* — none of the four "Week 1" datasets pair sensor measurements with health outcomes.

The current build is a **two-leg data-collection system**:

- **Sensor leg.** A low-cost field node posts readings (pH, turbidity, temperature, UV, ORP, rainfall) to a Flask `/ingest` endpoint, authenticated by a shared `DEVICE_SECRET`. Inference does not run on the device YET.
- **Reporting leg.** Community members text a station number to a Twilio phone number when illness is suspected. The Flask `/sms` webhook validates the Twilio signature, parses the station ID, retro-labels the trailing window of readings at that station as *unsafe*, writes an `illness_reports` row, and replies acknowledging receipt. These decisions will be further explained in this document. 

The server-side ML pipeline will be **designed** (see "ML pipeline discipline" in "CLAUDE.md" and "App/cholera_sensor_ml_approach.md" §6) but **deferred** — it trains once labelled windows have accumulated. Until then, the pipeline is validated against a *proxy* dataset to demonstrate the imbalance-handling and leakage-avoidance discipline.

## 1. Deliverables

By 2026-06-11 the repo should contain:

1. **Working Gen-1 backend** — Flask + SQLite + Twilio + sensor `/ingest`, runnable locally with `ngrok` and (stretch) deployable to Railway.
2. **Sensor simulator** — a script that posts plausible readings on a cadence so the demo and the labelling pipeline have data to operate on.
3. **Dashboard** — recent sensor readings + recent SMS reports, side by side, auto-refreshing. Not user-facing; for supervisors and developers.
4. **Labelling logic** with a defensible trailing-window definition; full audit trail (which reading was labelled, by which report, with what window). Decisions must be made about how to handle different waterborne disease incubation periods (and thus labelling windows) based on medical reports and symptoms. This will most likely involve probability assignments to the various possible illnesses. 
5. **ML pipeline validation on a proxy dataset** (e.g. "full_dataset.csv") — We want to design a high quality ML model's training process and acknowledge the fact that, for the time being, it must be validated purely on synthetic data or datasets that we have already proven to be faliable. 
6. **Model card / project write-up** that prominently states the cholera-proxy limitation, the ML-deferral framing, and the open linkage question.
7. **Risk register** — "issues/issues_v3.md", kept current (live document).

## 2. Calendar

Two hard milestones drive the cadence: the **interim presentation on 2026-06-01** and the **final submission on 2026-06-11**.

### 2026-05-27 — docs pivot + Gen-1 scaffold
- Update "CLAUDE.md" to reflect the pivot. 
- Archive "issues/issues_v1.md" and "PLAN_v1.md". 
- Write "issues/issues_v3.md" covering phase-2 risks (Twilio abuse, linkage, label noise, etc.). 
- Scaffold `App/backend/`: `app.py`, `database.py`, `labels.py`, `sensor_ingest.py`, `requirements.txt`, `Procfile`, `.env.example`, `templates/dashboard.html`.
- Write `scripts/simulate_sensor.py` so the demo has live readings.
- Write `App/DEMO.md` walking through Twilio + ngrok setup for tomorrow.
- Gate: backend runs locally end-to-end on a stubbed `/sms` POST (no real Twilio yet).

### 2026-05-28 — live demo
- Set up Twilio trial account + phone number; install ngrok; configure webhook.
- Live walk-through: text the Twilio number with a station ID from a real phone, watch the dashboard update with the labelled readings + the new illness report.

### 2026-05-29 to 2026-05-31 — harden the Gen-1 pipeline
- **Label audit trail.** When a report retro-labels readings, the labelling rule + window length are stored on the row.
- **Multi-station parser.** Lenient parser logs rejections for human review. Invalid/extraneous datapoints should be identified and labeled as such so that we can detect when our sensors are failing or a communication process in the pipeline has been disrupted. 
- **Persistence sanity.** Decide whether SQLite file lives in repo "App/backend/data/" or external; back it up before any session that writes to it.

### 2026-06-01 — interim presentation
- Story: phase-1 ceiling → pivot → Gen-1 system → ML pipeline on proxy data → linkage question.
- Demo: as 2026-05-28, but with the hardening from the previous three days visible. We want to inclue the following in the demo: simulated sensor values updating at regular intervals (not necessarily the actual interval that will be used), coordination between SMS/medical reporting and the borehole status, parsing through borehole stations using neighborhoods, map of the stations in Zimbabwe, language options (at least three to cover our bases), and buttons to send teams into the field for medical support or laboratory-grade water quality testing. 

### 2026-06-02 to 2026-06-08 — ML pipeline + linkage outreach + user-facing UI sketch
- **Linkage outreach.** Discuss partnerships with Allen Chafa. Does he know anyone that might be able to provide more information on the use of such a tool and its practicality considerations? Can he put us in contact with any VHWs directly to understand their experience?
- **User-facing app sketch.** A separate page from the dev dashboard, modelled loosely on "App/Ideation.md": shows the status of a station ("water at Station 4: contaminated reports in last 48h — boil before drinking"), in English first, with the multi-language hook following. 

### 2026-06-11 — submission
- Tag a release commit. Push. Submit.

## 3. Decisions still open/considered

These need answers but are not blocking the current build. Recorded so they don't get lost and may be useful for future teams to consider. 

1. **Pilot / deployment site framing.** The pivot doc recommends Bengal Delta (`icddr,b`) for data density and predictability. However, our deployment and project is focused on Harare, Zimbabwe. CLAUDE.md is currently *site-agnostic*. To be locked when partnerships are in place.
2. **Database location.** "App/backend/data/water_safety.db" is the obvious default for local dev. Production needs either Postgres on Railway or persistent SQLite with a backup story. Decision: Postgres on Railway. 
3. **User-facing language strategy.** Per "App/Ideation.md", eventually multi-language. Decision: Implement three languages (English, Shona, Ndebele) using "Babel" or "Google Translate" tools. These cover roughly 90% of Zimbabwe's population. 
4. **Treatment recommendations in the auto-reply?** Decision: **no** (legal exposure, see `issues_v3.md` §C6). Auto-reply is acknowledgement only; recommendations move to the user-facing app screen. Note: Auto-reply is designed to keep users in the loop (acknowledgement of their report) in order to address some of the motivation challenges frequently encountered with water quality projects.

## 4. What we are explicitly NOT doing in Gen-1

To prevent our scope from blowing up and to keep "App/Ideation.md" aspirational:

- **No live inference.** No trained model running against incoming sensor data. A trained model will follow ONCE data has been collected.
- **No clinical-record linkage.** We do not touch patient data; we collect community-reported symptoms only.
- **No treatment recommendations via SMS.** Acknowledgement only.
- **No on-device firmware or hardware build.** The sensor is simulated for Gen-1. We do not consider mechanical/electrical changes to Allen Chafa's original design. Instead, we want to provide a structure for the data collection pipeline.

## Gen-1 Continuation

After further research, particularly into the domain of digital healthcare in Zimbabwe, we have decided to build our data collection app on top of the open-source DHIS2 software. This will feature in Plan_v3.md where we will document the next steps taken to deploy this approach. 
