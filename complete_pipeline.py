"""
Complete Water Quality ML Pipeline
Integrates data generation, classifier training, and treatment recommendations
"""

import sys
import json
import argparse
from pathlib import Path

# Import custom modules
from water_quality_ml_pipeline import WaterQualityDataPipeline
from tinyml_ecoli_classifier import TinyMLEcoliClassifier
from treatment_advisor import WaterTreatmentAdvisor


class CompletePipeline:
    """
    End-to-end water quality monitoring and treatment recommendation system
    """
    
    def __init__(self, output_dir='./water_quality_models'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.data_pipeline = None
        self.classifier = None
        self.advisor = WaterTreatmentAdvisor()
    
    def step1_generate_training_data(self, num_scenarios=10):
        """Step 1: Generate WNTR simulations and create training dataset"""
        
        print("\n" + "="*70)
        print("STEP 1: GENERATING TRAINING DATA FROM WNTR SIMULATIONS")
        print("="*70)
        
        self.data_pipeline = WaterQualityDataPipeline()
        
        # Generate simulations
        self.data_pipeline.generate_simulation_batch(
            num_scenarios=num_scenarios,
            duration_hours=24
        )
        
        # Build training dataset
        training_data = self.data_pipeline.build_training_dataset()
        
        # Save to disk
        training_path = self.output_dir / 'water_quality_training_data.csv'
        self.data_pipeline.save_training_data(str(training_path))
        
        print(f"\n✓ Training data saved to: {training_path}")
        return training_data
    
    def step2_train_classifier(self, training_data_path=None):
        """Step 2: Train TinyML E. coli classifier"""
        
        print("\n" + "="*70)
        print("STEP 2: TRAINING TINYML E. COLI CLASSIFIER")
        print("="*70)
        
        if training_data_path is None:
            training_data_path = self.output_dir / 'water_quality_training_data.csv'
        
        self.classifier = TinyMLEcoliClassifier()
        
        # Train
        self.classifier.train(
            str(training_data_path),
            epochs=50,
            batch_size=8
        )
        
        # Convert to TensorFlow Lite
        tflite_path = self.output_dir / 'ecoli_classifier.tflite'
        self.classifier.convert_to_tflite(str(tflite_path))
        
        # Save artifacts
        scaler_path = self.output_dir / 'scaler.pkl'
        config_path = self.output_dir / 'model_config.json'
        
        self.classifier.save_scaler(str(scaler_path))
        self.classifier.save_model_config(str(config_path))
        
        print(f"\n✓ Model artifacts saved:")
        print(f"  - TensorFlow Lite: {tflite_path}")
        print(f"  - Scaler: {scaler_path}")
        print(f"  - Config: {config_path}")
    
    def step3_test_end_to_end(self):
        """Step 3: Test complete pipeline with example scenarios"""
        
        print("\n" + "="*70)
        print("STEP 3: END-TO-END TESTING WITH EXAMPLE SCENARIOS")
        print("="*70)
        
        test_scenarios = [
            {
                'name': 'Safe Drinking Water',
                'parameters': {
                    'temperature': 20.0,
                    'pH': 7.2,
                    'turbidity': 0.4,
                    'chlorine_residual': 0.8,
                    'dissolved_oxygen': 8.5,
                    'conductivity': 480
                }
            },
            {
                'name': 'Contaminated Water (E. coli Risk)',
                'parameters': {
                    'temperature': 25.0,
                    'pH': 6.8,
                    'turbidity': 2.0,
                    'chlorine_residual': 0.1,
                    'dissolved_oxygen': 5.0,
                    'conductivity': 650
                }
            },
            {
                'name': 'Degraded Quality',
                'parameters': {
                    'temperature': 18.0,
                    'pH': 6.0,
                    'turbidity': 3.5,
                    'chlorine_residual': 0.05,
                    'dissolved_oxygen': 4.2,
                    'conductivity': 900
                }
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n{'─'*70}")
            print(f"Testing: {scenario['name']}")
            print(f"{'─'*70}")
            
            # Make prediction
            ecoli_pred = self.classifier.predict(scenario['parameters'])
            
            # Get treatment recommendation
            recommendation = self.advisor.analyze_water_quality(
                scenario['parameters'],
                ecoli_pred
            )
            
            # Print results
            print(f"\nWater Parameters:")
            for param, value in scenario['parameters'].items():
                print(f"  {param:20s}: {value:6.2f}")
            
            print(f"\nE. coli Classification:")
            print(f"  Presence Predicted: {ecoli_pred['ecoli_present']}")
            print(f"  Probability: {ecoli_pred['probability']:.2%}")
            print(f"  Confidence: {ecoli_pred['confidence']:.2%}")
            
            print(advisor.format_recommendation(recommendation))
            
            results.append({
                'scenario': scenario['name'],
                'parameters': scenario['parameters'],
                'ecoli_prediction': ecoli_pred,
                'recommendation': {
                    'primary': recommendation.primary_treatment.value,
                    'secondary': [t.value for t in recommendation.secondary_treatments],
                    'urgency': recommendation.urgency,
                    'rationale': recommendation.rationale
                }
            })
        
        # Save results
        results_path = self.output_dir / 'test_results.json'
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n✓ Test results saved to: {results_path}")
        return results
    
    def run_complete_pipeline(self, num_scenarios=10):
        """Run all steps of the pipeline"""
        
        print("\n" + "="*70)
        print("WATER QUALITY ML PIPELINE - COMPLETE RUN")
        print("="*70)
        print(f"Output directory: {self.output_dir}")
        
        try:
            # Step 1: Generate data
            self.step1_generate_training_data(num_scenarios=num_scenarios)
            
            # Step 2: Train classifier
            self.step2_train_classifier()
            
            # Step 3: Test
            self.step3_test_end_to_end()
            
            print("\n" + "="*70)
            print("✓ PIPELINE COMPLETE!")
            print("="*70)
            print(f"\nOutput files in: {self.output_dir}")
            print("\nGenerated files:")
            for f in sorted(self.output_dir.glob('*')):
                print(f"  - {f.name}")
            
            return True
        
        except Exception as e:
            print(f"\n✗ Pipeline failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(
        description='Water Quality ML Pipeline - E. coli Detection & Treatment Recommendations'
    )
    parser.add_argument(
        '--scenarios',
        type=int,
        default=5,
        help='Number of simulation scenarios to generate (default: 5)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='./water_quality_models',
        help='Output directory for models and results (default: ./water_quality_models)'
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = CompletePipeline(output_dir=args.output)
    success = pipeline.run_complete_pipeline(num_scenarios=args.scenarios)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
