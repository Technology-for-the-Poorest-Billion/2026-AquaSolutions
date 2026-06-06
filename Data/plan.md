This folder considers our plan for which ML methods we will run on which datasets.


Full Dataset - 3 sensor parameters and a risk measurement - definitely worth analysing. This is the primary project track.

Water Potability - Kaggle sandbox dataset (3,276 rows, 9 features). Useful for testing whether more features lift macro-F1 above the ~0.45 plateau seen on the Full Dataset. Results are an optimistic upper bound as no grouped/temporal split is possible (no site_id or date).

Combined Dataset - Takes sensor data and calculates the WQI. Any ML would just figure out the WQI with high accuracy. Deprioritised — not worth pursuing.

WQD - Fish-pond aquaculture dataset. The label is pond suitability, not human water safety, so it has no relevance to disease risk prediction. Left unanalysed — XGBoost had already been validated on the other datasets and nothing new would be learned from running it here.


