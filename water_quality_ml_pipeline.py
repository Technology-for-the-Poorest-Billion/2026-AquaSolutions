"""
Water Quality ML Pipeline
Generates training data from WNTR simulations combined with field measurements
for TinyML E. coli classification and treatment recommendations
"""

import numpy as np
import pandas as pd
import wntr
from datetime import datetime, timedelta
import json


class WaterQualityDataPipeline:
    """
    Integrates WNTR simulations with real measurements to create ML training data.
    Features: pH, Turbidity, Temperature, Chlorine residual, Dissolved oxygen, Conductivity
    Target: E. coli presence (binary classifier: present/absent)
    """
    
    def __init__(self, network_file=None):
        """
        Initialize pipeline
        
        Args:
            network_file: Path to EPANET network file (.inp) or use default network
        """
        if network_file:
            self.wn = wntr.network.WaterNetworkModel(network_file)
        else:
            # Use WNTR's built-in Net3 network for demonstration
            self.wn = wntr.network.WaterNetworkModel('Net3')
        
        self.simulations = []
        self.measurements = []
        self.training_data = None
        
        print(f"Pipeline initialized with network: {self.wn.name}")
        print(f"Network has {len(self.wn.nodes)} nodes and {len(self.wn.links)} links")
    
    def generate_simulation_batch(self, num_scenarios=10, duration_hours=24):
        """
        Generate multiple WNTR simulations under different conditions
        
        Args:
            num_scenarios: Number of different scenarios to simulate
            duration_hours: Simulation duration
            
        Returns:
            List of simulation results with physical/chemical parameters
        """
        print(f"\nGenerating {num_scenarios} simulation scenarios...")
        
        sim_results = []
        
        for scenario_id in range(num_scenarios):
            # Vary conditions for each scenario
            demand_multiplier = 0.5 + (scenario_id % 3) * 0.25  # 0.5, 0.75, 1.0, ...
            temperature = 15 + (scenario_id % 4) * 5  # 15-25°C
            
            # Configure network for each scenario
            wn_scenario = self.wn.copy()
            
            # Set hydraulic options
            wn_scenario.options.hydraulic.demand_multiplier = demand_multiplier
            
            # Set water quality option (chemical tracking)
            wn_scenario.options.quality.parameter = 'CHEMICAL'
            wn_scenario.options.time.duration = duration_hours * 3600  # seconds
            wn_scenario.options.time.report_timestep = 3600  # 1-hour intervals
            
            # Add chemical source (e.g., chlorine injection at treatment plant)
            # Find a suitable source node (usually reservoir or treatment plant)
            source_node = list(wn_scenario.nodes())[0]
            if hasattr(wn_scenario.get_node(source_node), 'base_demand'):
                # Look for a node without base demand (likely a source)
                for node_name, node in wn_scenario.nodes():
                    if node.base_demand == 0:
                        source_node = node_name
                        break
            
            # Add chlorine source (concentration in mg/L)
            chlorine_conc = 0.5 + (scenario_id % 3) * 0.25  # 0.5-1.0 mg/L
            source = wntr.network.Source(source_node, 'SETPOINT', 
                                        chlorine_conc, 'mg/L')
            wn_scenario.add_source('chlorine_source', source)
            
            # Run simulation
            try:
                sim = wntr.sim.EpanetSimulator(wn_scenario)
                results = sim.run_sim()
                
                # Extract simulation results
                scenario_data = self._extract_simulation_features(
                    results, 
                    scenario_id=scenario_id,
                    temperature=temperature,
                    demand_mult=demand_multiplier,
                    chlorine_dose=chlorine_conc
                )
                
                sim_results.extend(scenario_data)
                print(f"  Scenario {scenario_id + 1}: {len(scenario_data)} samples generated")
                
            except Exception as e:
                print(f"  Scenario {scenario_id + 1} failed: {str(e)}")
                continue
        
        self.simulations = sim_results
        print(f"Total simulation samples: {len(self.simulations)}")
        return sim_results
    
    def _extract_simulation_features(self, results, scenario_id, temperature, 
                                     demand_mult, chlorine_dose):
        """
        Extract physical/chemical features from WNTR simulation results
        
        Returns:
            List of feature dictionaries for each timestep/node combination
        """
        features_list = []
        
        try:
            # Get node quality results (chlorine concentration)
            quality_results = results.node['quality']
            
            # Iterate through timesteps and nodes
            for timestep_idx, timestamp in enumerate(quality_results.index):
                for node_name in quality_results.columns:
                    try:
                        node = self.wn.get_node(node_name)
                        
                        # Get node pressure for turbidity proxy
                        pressure = results.node['pressure'].loc[timestamp, node_name]
                        
                        # Extract chemical concentration
                        chemical_conc = quality_results.loc[timestamp, node_name]
                        
                        # Generate synthetic feature values based on simulation + parameters
                        # In production: combine with actual sensor measurements
                        features = {
                            'scenario_id': scenario_id,
                            'timestamp': timestamp,
                            'node_name': node_name,
                            'temperature': temperature + np.random.normal(0, 0.5),  # ±0.5°C noise
                            'pH': 7.0 + np.random.normal(0, 0.3),  # Neutral water with noise
                            'turbidity': max(0.1, 0.5 + pressure * 0.001 + np.random.normal(0, 0.2)),  # NTU
                            'chlorine_residual': max(0, chemical_conc + np.random.normal(0, 0.1)),  # mg/L
                            'dissolved_oxygen': 8.0 - (temperature / 10) + np.random.normal(0, 0.3),  # mg/L
                            'conductivity': 500 + np.random.normal(0, 50),  # µS/cm
                            'pressure': pressure,
                            'demand_multiplier': demand_mult,
                        }
                        
                        features_list.append(features)
                    
                    except Exception as e:
                        continue
        
        except Exception as e:
            print(f"    Error extracting features: {str(e)}")
        
        return features_list
    
    def add_field_measurements(self, measurements_df):
        """
        Add real field measurements to pipeline
        
        Args:
            measurements_df: DataFrame with columns:
                - timestamp: datetime
                - node_name: str (node identifier)
                - temperature, pH, turbidity, chlorine_residual, 
                  dissolved_oxygen, conductivity: float
                - ecoli_present: bool (E. coli presence ground truth)
        """
        self.measurements = measurements_df
        print(f"\nAdded {len(measurements_df)} field measurements")
        return measurements_df
    
    def generate_synthetic_ecoli_labels(self, simulation_data=None):
        """
        Generate synthetic E. coli labels based on water quality indicators
        This creates realistic correlations for demonstration
        
        In production: use actual E. coli testing results
        
        Args:
            simulation_data: List of simulation features (or uses self.simulations)
            
        Returns:
            Updated data with E. coli labels
        """
        if simulation_data is None:
            data_to_label = self.simulations.copy()
        else:
            data_to_label = simulation_data.copy()
        
        if not data_to_label:
            print("No data to label. Run generate_simulation_batch() first.")
            return []
        
        print(f"\nGenerating synthetic E. coli labels for {len(data_to_label)} samples...")
        
        for sample in data_to_label:
            # E. coli presence is MORE LIKELY when:
            # - Low chlorine residual (<0.2 mg/L)
            # - High turbidity (>2 NTU)
            # - Low pH (<6.5 or >8.5)
            # - High temperature (>25°C)
            # - Low dissolved oxygen (<5 mg/L)
            
            risk_score = 0.0
            
            # Chlorine: primary disinfectant
            if sample['chlorine_residual'] < 0.2:
                risk_score += 0.4
            elif sample['chlorine_residual'] < 0.5:
                risk_score += 0.2
            
            # Turbidity: can shield pathogens
            if sample['turbidity'] > 2.0:
                risk_score += 0.3
            elif sample['turbidity'] > 1.0:
                risk_score += 0.1
            
            # pH: affects disinfection effectiveness
            if sample['pH'] < 6.5 or sample['pH'] > 8.5:
                risk_score += 0.2
            
            # Temperature: affects organism survival
            if sample['temperature'] > 25:
                risk_score += 0.1
            
            # Dissolved oxygen: indicates water quality
            if sample['dissolved_oxygen'] < 5:
                risk_score += 0.2
            
            # Add some randomness
            risk_score += np.random.normal(0, 0.1)
            risk_score = np.clip(risk_score, 0, 1)
            
            # Threshold for E. coli presence (tunable)
            sample['ecoli_present'] = risk_score > 0.5
            sample['ecoli_risk_score'] = risk_score
        
        positive_count = sum(1 for s in data_to_label if s['ecoli_present'])
        print(f"E. coli labels generated: {positive_count} positive, "
              f"{len(data_to_label) - positive_count} negative")
        
        return data_to_label
    
    def build_training_dataset(self):
        """
        Combine simulations and measurements into ML training dataset
        
        Returns:
            DataFrame with features and E. coli labels
        """
        print("\nBuilding training dataset...")
        
        # Generate E. coli labels for simulations if not already done
        labeled_simulations = self.generate_synthetic_ecoli_labels(self.simulations)
        
        # Convert to DataFrame
        df_sim = pd.DataFrame(labeled_simulations)
        
        # If field measurements exist, combine them
        if not self.measurements.empty:
            # Ensure measurements have E. coli labels
            if 'ecoli_present' not in self.measurements.columns:
                self.measurements['ecoli_present'] = False
            df_combined = pd.concat([df_sim, self.measurements], ignore_index=True)
        else:
            df_combined = df_sim
        
        # Feature columns for ML model
        feature_cols = [
            'temperature', 'pH', 'turbidity', 'chlorine_residual',
            'dissolved_oxygen', 'conductivity'
        ]
        
        # Ensure all features present
        for col in feature_cols:
            if col not in df_combined.columns:
                df_combined[col] = 0.0
        
        # Select features and target
        self.training_data = df_combined[feature_cols + ['ecoli_present']]
        
        print(f"Training dataset shape: {self.training_data.shape}")
        print(f"\nFeature summary:\n{self.training_data[feature_cols].describe()}")
        print(f"\nTarget distribution:\n{self.training_data['ecoli_present'].value_counts()}")
        
        return self.training_data
    
    def save_training_data(self, filepath):
        """Save training dataset to CSV"""
        if self.training_data is not None:
            self.training_data.to_csv(filepath, index=False)
            print(f"\nTraining data saved to {filepath}")
        else:
            print("No training data to save. Run build_training_dataset() first.")
    
    def export_features_json(self, filepath):
        """Export simulation features as JSON for inspection"""
        if self.simulations:
            with open(filepath, 'w') as f:
                json.dump(self.simulations[:10], f, indent=2, default=str)
            print(f"Sample features exported to {filepath}")


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = WaterQualityDataPipeline()
    
    # Generate WNTR simulations
    pipeline.generate_simulation_batch(num_scenarios=5, duration_hours=24)
    
    # Build training dataset
    training_data = pipeline.build_training_dataset()
    
    # Save for ML training
    pipeline.save_training_data('water_quality_training_data.csv')
    pipeline.export_features_json('sample_features.json')
    
    print("\n✓ Data pipeline complete! Ready for TinyML model training.")
