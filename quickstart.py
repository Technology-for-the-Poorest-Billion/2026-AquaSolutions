#!/usr/bin/env python3
"""
Quick-Start Guide for Water Quality TinyML System
Walks through setup and first use
"""

import os
import subprocess
import sys


def print_section(title):
    """Print formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def run_command(cmd, description):
    """Run a shell command with error handling"""
    print(f"► {description}")
    print(f"  $ {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False)
        if result.returncode != 0:
            print(f"✗ Command failed with exit code {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False


def check_python_version():
    """Check Python version"""
    print_section("Step 0: Checking Python Version")
    
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("✗ Python 3.8+ required")
        return False
    
    print("✓ Python version OK")
    return True


def install_dependencies():
    """Install required packages"""
    print_section("Step 1: Installing Dependencies")
    
    cmd = "pip install -r water_quality_requirements.txt"
    return run_command(cmd, "Installing packages from requirements.txt")


def generate_training_data():
    """Generate initial training data"""
    print_section("Step 2: Generating WNTR Training Data")
    
    print("This will create ~200 training samples from water quality simulations")
    print("(Estimated time: 2-5 minutes)\n")
    
    cmd = "python water_quality_ml_pipeline.py"
    return run_command(cmd, "Running data generation pipeline")


def train_classifier():
    """Train the TinyML classifier"""
    print_section("Step 3: Training E. coli Classifier")
    
    print("This will train a neural network to predict E. coli presence")
    print("(Estimated time: 1-2 minutes)\n")
    
    cmd = "python tinyml_ecoli_classifier.py"
    return run_command(cmd, "Training TinyML classifier")


def test_treatment_advisor():
    """Test treatment recommendations"""
    print_section("Step 4: Testing Treatment Advisor")
    
    print("This will demonstrate treatment recommendations for various scenarios\n")
    
    cmd = "python treatment_advisor.py"
    return run_command(cmd, "Running treatment advisor")


def run_complete_pipeline():
    """Run the complete integrated pipeline"""
    print_section("Step 5: Running Complete End-to-End Pipeline")
    
    print("This integrates all components and tests the system")
    print("(Estimated time: 5-10 minutes)\n")
    
    cmd = "python complete_pipeline.py --scenarios 10 --output ./water_quality_models"
    return run_command(cmd, "Running complete pipeline")


def verify_outputs():
    """Verify generated files"""
    print_section("Step 6: Verifying Outputs")
    
    expected_files = [
        'water_quality_models/water_quality_training_data.csv',
        'water_quality_models/ecoli_classifier.tflite',
        'water_quality_models/scaler.pkl',
        'water_quality_models/model_config.json',
        'water_quality_models/test_results.json'
    ]
    
    all_exist = True
    for file_path in expected_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✓ {file_path:50s} ({size:,d} bytes)")
        else:
            print(f"✗ {file_path:50s} MISSING")
            all_exist = False
    
    return all_exist


def print_next_steps():
    """Print recommendations for next steps"""
    print_section("Next Steps")
    
    print("""
1. INTEGRATE WITH YOUR DATA:
   - Collect field measurements of your water network
   - Update training data with real samples
   - Retrain classifier for your specific location

2. DEPLOY TO EDGE DEVICES:
   - Use ecoli_classifier.tflite on microcontroller/mobile
   - Implement preprocessing using scaler.pkl statistics
   - Run inference at monitoring stations

3. BUILD USER INTERFACE:
   - Create mobile app showing water quality
   - Display treatment recommendations
   - Alert users when treatment needed

4. EXTEND FUNCTIONALITY:
   - Add more water quality parameters
   - Predict other pathogens (Cryptosporidium, Giardia)
   - Include time-series analysis for trend detection

5. VALIDATE WITH REAL DATA:
   - Compare predictions to lab test results
   - Collect feedback from water utilities
   - Improve model accuracy over time

USEFUL COMMANDS:
   # Generate more training data (5 scenarios = ~100 samples)
   python water_quality_ml_pipeline.py

   # Retrain classifier with new data
   python tinyml_ecoli_classifier.py

   # Test with custom water sample
   python -c "
from tinyml_ecoli_classifier import TinyMLEcoliClassifier
c = TinyMLEcoliClassifier()
c.train('water_quality_training_data.csv')
print(c.predict({
    'temperature': 22,
    'pH': 7.0,
    'turbidity': 0.5,
    'chlorine_residual': 0.6,
    'dissolved_oxygen': 8,
    'conductivity': 500
}))
   "

DOCUMENTATION:
   - See WATER_QUALITY_ML_README.md for full documentation
   - Check individual Python files for detailed docstrings
   - Review test_results.json for example predictions
    """)


def main():
    """Run the complete quick-start"""
    
    print("\n" + "="*70)
    print("  WATER QUALITY TINYML SYSTEM - QUICK START GUIDE")
    print("="*70)
    
    steps = [
        ("Python Version Check", check_python_version),
        ("Install Dependencies", install_dependencies),
        ("Generate Training Data", generate_training_data),
        ("Train Classifier", train_classifier),
        ("Test Treatment Advisor", test_treatment_advisor),
        ("Run Complete Pipeline", run_complete_pipeline),
        ("Verify Outputs", verify_outputs),
    ]
    
    completed = 0
    for step_num, (step_name, step_func) in enumerate(steps, 1):
        print(f"\n{'─'*70}")
        print(f"Step {step_num}/{len(steps)}: {step_name}")
        print(f"{'─'*70}")
        
        try:
            if step_func():
                completed += 1
            else:
                print(f"\n✗ Step {step_num} failed. Stopping.")
                break
        except KeyboardInterrupt:
            print("\n\nSetup cancelled by user")
            sys.exit(1)
    
    # Summary
    print("\n" + "="*70)
    if completed == len(steps):
        print(f"✓ SETUP COMPLETE! All {completed} steps successful.")
    else:
        print(f"⚠ Setup incomplete: {completed}/{len(steps)} steps completed")
    print("="*70)
    
    print_next_steps()
    
    print("\n" + "="*70)
    print("  Setup finished! Check the output above and explore the generated")
    print("  files in ./water_quality_models/")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
