A guide to what is in this repository and where to find it.

- ML/ — ML.md explains the overall ML work and key findings
  - ML Full dataset/ — ML Full dataset.md covers the primary analysis on full_dataset.csv using pH, turbidity and temperature with XGBoost and Logistic Regression
  - ML water potability/ — water potability.md covers the secondary analysis on the Kaggle potability dataset using nine chemistry features
  - plans and specs/ — plan.md records which datasets were analysed and why; other files are technical AI documents for rebuilding the analyses

- App/ — the Flask data collection system
  - cholera_sensor_ml_approach.md — explains the pivot away from TinyML toward a sensor + SMS data collection system and why
  - DEMO.md — step by step guide for running a live demo of the system
  - Ideation.md — early sketch of the user-facing application
  - backend/ — all Flask application code, database, routes, and tests
  - scripts/ — utility scripts: simulate_sensor.py for testing the ingest endpoint, translate_po.py for updating translation files, crop_logo.py for the logo asset
  - docs/ — technical documents for the app
    - handoffs/ — record of the Postgres migration and what one step remains
    - superpowers/ — specs and implementation plans for each app feature (AI-facing)

- issues/ — issue_chronology.md explains the three versions; v1 and v2 cover data quality problems from Phase 1; v3 is the live risk register for the current system

- Research/ — literature notes including the sensor approach and site selection rationale

- Meetings/ — notes from meetings with Allen Chafa and supervisors
