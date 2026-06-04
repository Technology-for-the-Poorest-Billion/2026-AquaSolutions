This folder considers our plan for which ML methods we will run on which datasets.

Full Dataset - 3 sensor parameters and a risk measurement - definitely worth analysing. This is the primary project track.

Water Potability - Kaggle sandbox dataset (3,276 rows, 9 features). Useful for testing whether more features lift macro-F1 above the ~0.45 plateau seen on the Full Dataset. Results are an optimistic upper bound as no grouped/temporal split is possible (no site_id or date).

Combined Dataset - Takes sensor data and calculates the WQI. Any ML would just figure out the WQI with high accuracy. Deprioritised — not worth pursuing.

WQD - High potential, lots of features and a balanced 3-class water quality label (0/1/2, ~1,400 rows each, 4,300 total). Meaning of classes unclear from the file — needs checking against the Mendeley source before use.


The other files in this folder are technical documents written for AI. They record the exact steps followed to build each analysis and are intended for rebuilding or adapting the work, not for reading as a summary.
