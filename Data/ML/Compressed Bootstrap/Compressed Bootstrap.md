# Compressed Bootstrap

An end-to-end ML pipeline built on synthetic data, designed for conversion to the full system when real illness-report-labelled data is available.

## Steps

**1. Synthetic data generation**
500 sensor readings are generated from realistic statistical distributions: pH, turbidity, chlorine residual, UV absorbance and ORP.

**2. Threshold-based labelling with confidence weights**
Each reading is labelled `risk` or `safe` using WHO-aligned thresholds. Risk labels carry a confidence weight (0.3–0.9) reflecting how far the reading sits from the boundary (the further from safe, the higher the weight) and Safety labels are given confidence 0.1 reflecting the reduced information content of a safety reading. 10% of rows are withheld as unlabelled, simulating stations with no illness report.

**3. XGBoost training with sample weights**
An `XGBClassifier` is trained on labelled rows using confidence scores as `sample_weight`.

**4. Evaluation**
- Classification report (precision, recall, F1 per class)
- Confusion matrix
- ROC curve and AUC score
- SHAP summary plot showing per-feature contribution to risk predictions

**5. Edge deployment via m2cgen**
The trained model is saved to `model.json` then converted to a standalone C file (`water_quality_edge.c`) using m2cgen. The C output encodes the full decision-tree logic and can be compiled and flashed to a microcontroller for local inference with no internet connection.

## Outputs

`model.json` - Trained XGBoost model in XGBoost's JSON format
`water_quality_edge.c` - Model exported to C for edge/microcontroller deployment

## Interpreting the results

Metrics (97% accuracy, AUC ≈ 1) are high because the test set is drawn from the same synthetic distribution used to generate labels, i.e. the model recovers the thresholds it was trained against. These are **not** real-world performance claims but are prepared for analysis of real data once it has been implemented. 