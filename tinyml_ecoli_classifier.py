"""
TinyML E. coli Classifier
Lightweight neural network trained on water quality parameters
Optimized for microcontroller, edge device, and mobile deployment via TensorFlow Lite
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import json
import joblib


class TinyMLEcoliClassifier:
    """
    Lightweight E. coli presence classifier using TensorFlow Lite
    Features: temperature, pH, turbidity, chlorine_residual, dissolved_oxygen, conductivity
    Target: E. coli presence (binary classification)
    """
    
    FEATURE_NAMES = [
        'temperature', 'pH', 'turbidity', 'chlorine_residual',
        'dissolved_oxygen', 'conductivity'
    ]
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.model_size_kb = 0
    
    def build_model(self, input_shape=6):
        """
        Build lightweight neural network suitable for edge devices
        
        Architecture:
        - Input: 6 features (physical/chemical parameters)
        - Dense: 16 neurons (ReLU) - minimal for TinyML
        - Dense: 8 neurons (ReLU)
        - Output: 1 neuron (Sigmoid) for binary classification
        
        Model size: ~2-4 KB when quantized
        """
        self.model = keras.Sequential([
            keras.layers.Dense(16, activation='relu', input_shape=(input_shape,)),
            keras.layers.Dropout(0.1),  # Minimal dropout for edge
            keras.layers.Dense(8, activation='relu'),
            keras.layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy', tf.keras.metrics.AUC()]
        )
        
        print("Model architecture:")
        self.model.summary()
        return self.model
    
    def train(self, training_data_path, test_size=0.2, epochs=50, batch_size=8):
        """
        Train classifier on water quality data
        
        Args:
            training_data_path: Path to CSV with features and 'ecoli_present' target
            test_size: Fraction for test set
            epochs: Training epochs
            batch_size: Batch size (small for embedded deployment)
        """
        print("\nLoading training data...")
        df = pd.read_csv(training_data_path)
        
        # Extract features and target
        X = df[self.FEATURE_NAMES].values
        y = df['ecoli_present'].values.astype(float)
        
        print(f"Samples: {len(X)}")
        print(f"Positive class: {y.sum():.0f} ({100*y.mean():.1f}%)")
        print(f"Negative class: {(1-y).sum():.0f} ({100*(1-y.mean()):.1f}%)")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # Normalize features (essential for neural networks)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        print(f"\nTraining set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        # Build and train model
        self.build_model(input_shape=len(self.FEATURE_NAMES))
        
        print("\nTraining model...")
        history = self.model.fit(
            X_train_scaled, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        # Evaluate
        print("\nEvaluating model...")
        y_pred_proba = self.model.predict(X_test_scaled, verbose=0).flatten()
        y_pred = (y_pred_proba > 0.5).astype(int)
        
        print("\nTest Set Performance:")
        print(classification_report(y_test, y_pred, 
                                   target_names=['No E. coli', 'E. coli Present']))
        print(f"ROC AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")
        print(f"Confusion Matrix:\n{confusion_matrix(y_test, y_pred)}")
        
        self.is_trained = True
        return history
    
    def predict(self, features_dict):
        """
        Make prediction from physical/chemical parameters
        
        Args:
            features_dict: Dictionary with keys matching FEATURE_NAMES
                          e.g., {'temperature': 20, 'pH': 7.0, ...}
        
        Returns:
            Dictionary with prediction and confidence
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
        
        # Create feature vector in correct order
        features = np.array([[features_dict[f] for f in self.FEATURE_NAMES]])
        
        # Scale using training statistics
        features_scaled = self.scaler.transform(features)
        
        # Predict
        probability = self.model.predict(features_scaled, verbose=0)[0][0]
        
        prediction = {
            'ecoli_present': bool(probability > 0.5),
            'probability': float(probability),
            'confidence': float(max(probability, 1 - probability))
        }
        
        return prediction
    
    def convert_to_tflite(self, output_path='ecoli_classifier.tflite'):
        """
        Convert trained model to TensorFlow Lite format
        Optimized for embedded devices (microcontroller, mobile)
        
        Returns:
            Size of quantized model in KB
        """
        if not self.is_trained:
            raise ValueError("Model must be trained first!")
        
        print(f"\nConverting model to TensorFlow Lite...")
        
        # Convert to TFLite with quantization for smaller size
        converter = tf.lite.TFLiteConverter.from_keras_model(self.model)
        
        # Quantization: reduce model size by 4x
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        tflite_model = converter.convert()
        
        # Save
        with open(output_path, 'wb') as f:
            f.write(tflite_model)
        
        model_size_kb = len(tflite_model) / 1024
        self.model_size_kb = model_size_kb
        
        print(f"✓ TFLite model saved: {output_path}")
        print(f"  Model size: {model_size_kb:.1f} KB (suitable for edge devices)")
        
        return model_size_kb
    
    def save_scaler(self, filepath='scaler.pkl'):
        """Save feature scaler for inference time normalization"""
        joblib.dump(self.scaler, filepath)
        print(f"✓ Scaler saved: {filepath}")
    
    def save_model_config(self, filepath='model_config.json'):
        """Save model configuration for deployment"""
        config = {
            'features': self.FEATURE_NAMES,
            'model_type': 'TensorFlow Lite Binary Classifier',
            'input_shape': len(self.FEATURE_NAMES),
            'threshold': 0.5,
            'model_size_kb': self.model_size_kb
        }
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Model config saved: {filepath}")


# Example usage
if __name__ == "__main__":
    # Initialize classifier
    classifier = TinyMLEcoliClassifier()
    
    # Train on data from pipeline
    try:
        classifier.train('water_quality_training_data.csv', epochs=50)
        
        # Convert to TensorFlow Lite for edge deployment
        classifier.convert_to_tflite('ecoli_classifier.tflite')
        classifier.save_scaler('scaler.pkl')
        classifier.save_model_config('model_config.json')
        
        # Example prediction
        print("\n" + "="*60)
        print("EXAMPLE PREDICTION")
        print("="*60)
        
        test_sample = {
            'temperature': 22.0,
            'pH': 7.2,
            'turbidity': 0.8,
            'chlorine_residual': 0.4,
            'dissolved_oxygen': 7.5,
            'conductivity': 520
        }
        
        print(f"\nInput water parameters:\n{json.dumps(test_sample, indent=2)}")
        
        result = classifier.predict(test_sample)
        print(f"\nPrediction result:\n{json.dumps(result, indent=2)}")
        
        if result['ecoli_present']:
            print("\n⚠ E. COLI DETECTED - Water treatment recommended")
        else:
            print("\n✓ No E. coli detected - Water appears safe")
        
    except FileNotFoundError:
        print("Error: Training data not found.")
        print("Run water_quality_ml_pipeline.py first to generate training data.")
