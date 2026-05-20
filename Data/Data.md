# Data

## Kaggle datasets

### `water_potability.csv`
- Kaggle water potability dataset
- 3,276 samples, 9 water-quality features, and a binary `Potability` label
- Good for supervised training of a potability classifier

### `waterQuality1.csv`
- Kaggle water safety dataset
- 7,999 samples, 20 water-quality features, and a binary `is_safe` label
- Good for supervised training of a safe/unsafe classifier, and useful for broader contaminant-risk modeling

### `Water Quality Testing.csv`
- Smaller water-quality sample set with physical measurements such as pH, temperature, turbidity, dissolved oxygen, and conductivity
- Useful as feature data, validation data, or a source for exploratory analysis
- If it does not contain a safety label, it is not enough by itself for supervised classification, but it can still help with preprocessing, feature selection, and calibration

## Other dataset

### `Water Quality Dataset.xlsx`
- Regional field measurements from Uganda compiled from published measurements
- Useful for real-world feature comparison and validation against the Kaggle data
- Better suited to analysis and comparison unless a target label is defined elsewhere

## Notes on training value

Yes, the Kaggle datasets are helpful for training. They are especially useful because they already include binary labels (`Potability` and `is_safe`), which makes them suitable for supervised machine learning.

The main caveat is that they measure water safety rather than E. coli directly, so they are best used to train a safe/unsafe classifier or a contamination-risk model. If the project goal is specifically E. coli prediction, these datasets can still help as a proxy, but you would ideally combine them with microbiological lab results or a dataset that includes pathogen labels.
