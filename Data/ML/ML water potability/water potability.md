This folder contains code and documents for running a gradient boosting method on water quality data - water_potability.csv


water_potability_eda_V1.ipynb

Loads water_potability.csv with nine chemistry features including pH, turbidity, hardness and chloramines
Handles missing values with median imputation and missingness indicators for heavily incomplete columns
Splits data 80/20 with stratified random sampling (dataset has no site or date so grouped splitting is not possible)
Trains an XGBoost classifier with balanced class weights to handle the 61/39 class imbalance
Compares against a Logistic Regression baseline and an always-majority dummy
Plots feature importance three ways: gain, weight, cover
Cross-notebook comparison against the three-feature full_dataset baseline to test whether more sensors lift performance


Key findings

XGBoost was the strongest model, clearly outperforming both the logistic regression and dummy baselines
pH was the most important feature across all importance measures
More chemistry features do appear to lift performance above the three-sensor ceiling seen in full_dataset — the improvement was large enough to be meaningful even accounting for the more generous split used here
The bottom line is that sensor-based chemical proxies carry a real signal for classifying water safety, but this dataset uses lab-defined thresholds rather than real illness outcomes — to go further we need field data labelled by actual health reports, which is what the SMS system is designed to collect
