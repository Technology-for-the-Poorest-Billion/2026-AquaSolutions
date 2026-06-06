This folder contains all machine learning work done on existing water quality datasets. Having worked out that no existing data is good enough to train our sensor, we aimed to test whether sensor-based chemical measurements can classify water safety well enough to be useful and to identify the best method before collecting our own data.


Folders

ML Full dataset — primary analysis. Runs XGBoost and Logistic Regression on ../Datasets/full_dataset.csv, which has three sensor features (pH, turbidity, temperature) and an E. coli risk label. Two versions: V1 explores the baseline and adds temporal features; V2 tightens the validation and adds a deployment guardrail that flags when the model should defer to a lab.

ML water potability — secondary analysis on ../Datasets/water_potability.csv, a Kaggle dataset with nine chemistry features and a binary potability label. Used to test whether more features lift performance above the ceiling seen on the full dataset.

Compressed Bootstrap — a complete XGBoost pipeline ready to train on real field data once illness-report labels accumulate. Currently runs on 500 synthetic sensor readings (pH, turbidity, chlorine residual, UV, ORP) labelled by threshold rules with confidence weights, which will be replaced by real data when available. Trains XGBoost with confidence scores as sample weights, evaluates with confusion matrix, ROC/AUC and SHAP feature importance. Then exports the trained model to C via m2cgen for edge deployment on a microcontroller.


Key findings

XGBoost was consistently the strongest method across all datasets, outperforming Logistic Regression and dummy baselines.

pH was the most important feature in both analyses — it carried more signal than any other measurement.

More chemistry features do lift performance. The nine-feature water potability classifier scored meaningfully higher than the three-feature full dataset classifier, which is evidence that adding sensors to the physical node would improve predictions.

The honest performance ceiling on full_dataset.csv is low. Under a strict grouped and temporal split — the only kind that honestly represents deployment — the model barely beats a dummy that always predicts high risk. This is a data problem, not a modelling problem.


The bottom line

The method works. XGBoost on sensor-derived chemistry features can classify water safety above a random baseline, and the signal gets stronger with more features. But none of the datasets used here have labels tied to real illness outcomes. They use lab thresholds or aquaculture standards instead. A model trained on these cannot predict disease risk.

The next step is to collect field data labelled by actual health reports, which is what the Generation-1 sensor and SMS system is designed to do. Once that data accumulates, the same XGBoost pipeline used here is the starting point for a deployable model.
