These files contain code for running our first gradient boosting algorithm on water potability data


FirstGradBooster.ipynb

Loads full_dataset.csv and preps three sensor features: pH, turbidity, temperature (with median imputation and missingness indicator for the 45% missing temperature readings)
Splits data 80/20 by site using GroupShuffleSplit — no site appears in both train and test
Trains an XGBoost classifier with balanced class weights to handle the ~95% HIGH class imbalance
Compares against a Logistic Regression baseline
Plots feature importance three ways: gain, weight, cover
Also runs an XGBoost regressor on raw E. coli counts (log-transformed), plus a Tweedie regressor baseline
Adds temporal features (month, wet season flag, year) and re-trains to see if they improve macro-F1


FirstGradBooster_v2.ipynb — additions

Stricter train/test split: grouped by site AND temporal cutoff at 2015, so test genuinely represents future unseen sites
Adds an always-HIGH dummy baseline — any real model must beat its macro-F1 (~0.32) to be worth using
Prints the dominant feature by importance type in text, not just plots it
Implements an abstain state ("send sample to lab") triggered when sensor readings are outside the training distribution (p01–p99) or model confidence is below 60% — this is the key deployment guardrail