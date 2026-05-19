"""
Water Treatment Recommendation Engine
Maps water quality parameters and E. coli predictions to treatment suggestions
Provides actionable guidance for water safety
"""

import json
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple


class TreatmentMethod(Enum):
    """Available water treatment options"""
    NO_TREATMENT = "safe_to_consume"
    BOILING = "boiling"
    FILTRATION = "filtration"
    CHLORINATION = "chlorination"
    UV_TREATMENT = "uv_treatment"
    ACTIVATED_CARBON = "activated_carbon"
    DO_NOT_CONSUME = "do_not_consume"


@dataclass
class TreatmentRecommendation:
    """Structure for treatment recommendation"""
    primary_treatment: TreatmentMethod
    secondary_treatments: List[TreatmentMethod]
    rationale: str
    urgency: str  # 'SAFE', 'CAUTION', 'WARNING', 'CRITICAL'
    confidence: float
    parameters_of_concern: List[str]


class WaterTreatmentAdvisor:
    """
    AI-driven water treatment recommendation system
    Based on water quality parameters and E. coli classification
    """
    
    def __init__(self):
        self.risk_thresholds = {
            'temperature': {'safe': (10, 30), 'warning': (0, 50)},
            'pH': {'safe': (6.5, 8.5), 'warning': (5.5, 9.5)},
            'turbidity': {'safe': (0, 1.0), 'warning': (0, 5.0)},  # NTU
            'chlorine_residual': {'safe': (0.2, 2.0), 'warning': (0.0, 2.0)},  # mg/L
            'dissolved_oxygen': {'safe': (5.0, 12.0), 'warning': (3.0, 15.0)},  # mg/L
            'conductivity': {'safe': (0, 1000), 'warning': (0, 2000)}  # µS/cm
        }
        
        self.treatment_matrix = self._build_treatment_matrix()
    
    def _build_treatment_matrix(self) -> Dict:
        """
        Build decision matrix mapping water quality issues to treatments
        """
        return {
            'ecoli_presence': {
                'high_confidence': [
                    TreatmentMethod.BOILING,
                    TreatmentMethod.UV_TREATMENT,
                    TreatmentMethod.CHLORINATION
                ],
                'low_confidence': [TreatmentMethod.FILTRATION]
            },
            'high_turbidity': {
                'primary': TreatmentMethod.FILTRATION,
                'secondary': [TreatmentMethod.ACTIVATED_CARBON]
            },
            'low_chlorine': {
                'primary': TreatmentMethod.CHLORINATION,
                'secondary': [TreatmentMethod.BOILING]
            },
            'poor_pH': {
                'primary': TreatmentMethod.FILTRATION,
                'secondary': [TreatmentMethod.ACTIVATED_CARBON]
            },
            'low_oxygen': {
                'primary': TreatmentMethod.BOILING,
                'secondary': [TreatmentMethod.ACTIVATED_CARBON]
            }
        }
    
    def analyze_water_quality(self, 
                             parameters: Dict,
                             ecoli_prediction: Dict) -> TreatmentRecommendation:
        """
        Comprehensive water quality analysis and treatment recommendation
        
        Args:
            parameters: Dictionary with water quality parameters
                {
                    'temperature': float,
                    'pH': float,
                    'turbidity': float,
                    'chlorine_residual': float,
                    'dissolved_oxygen': float,
                    'conductivity': float
                }
            ecoli_prediction: Output from ML classifier
                {
                    'ecoli_present': bool,
                    'probability': float,
                    'confidence': float
                }
        
        Returns:
            TreatmentRecommendation with suggested treatments
        """
        
        # Assess each parameter
        parameter_issues = self._assess_parameters(parameters)
        
        # Check E. coli classification
        ecoli_risk = self._assess_ecoli_risk(ecoli_prediction)
        
        # Combine assessments
        all_issues = parameter_issues + ecoli_risk
        
        # Determine urgency and recommendations
        recommendation = self._determine_recommendation(
            all_issues,
            parameter_issues,
            ecoli_prediction,
            parameters
        )
        
        return recommendation
    
    def _assess_parameters(self, parameters: Dict) -> List[Tuple[str, str, float]]:
        """
        Assess each water quality parameter
        
        Returns:
            List of (issue_name, severity, value) tuples
        """
        issues = []
        
        for param_name, param_value in parameters.items():
            if param_name not in self.risk_thresholds:
                continue
            
            thresholds = self.risk_thresholds[param_name]
            
            # Check against safe range
            safe_min, safe_max = thresholds['safe']
            if param_value < safe_min or param_value > safe_max:
                warn_min, warn_max = thresholds['warning']
                if param_value < warn_min or param_value > warn_max:
                    severity = 'CRITICAL'
                else:
                    severity = 'WARNING'
                
                issues.append((param_name, severity, param_value))
        
        return issues
    
    def _assess_ecoli_risk(self, ecoli_pred: Dict) -> List[Tuple[str, str, float]]:
        """Assess E. coli risk from ML prediction"""
        issues = []
        
        if ecoli_pred.get('ecoli_present', False):
            confidence = ecoli_pred.get('confidence', 0.5)
            probability = ecoli_pred.get('probability', 0.5)
            
            # High confidence E. coli = CRITICAL
            if confidence > 0.8:
                severity = 'CRITICAL'
            elif probability > 0.7:
                severity = 'WARNING'
            else:
                severity = 'CAUTION'
            
            issues.append(('ecoli_presence', severity, probability))
        
        return issues
    
    def _determine_recommendation(self,
                                  all_issues: List,
                                  param_issues: List,
                                  ecoli_pred: Dict,
                                  parameters: Dict) -> TreatmentRecommendation:
        """
        Determine treatment recommendation based on all assessments
        """
        
        # Check for critical safety issues
        critical_issues = [issue for issue in all_issues if issue[1] == 'CRITICAL']
        warning_issues = [issue for issue in all_issues if issue[1] == 'WARNING']
        caution_issues = [issue for issue in all_issues if issue[1] == 'CAUTION']
        
        parameters_of_concern = [issue[0] for issue in all_issues]
        
        # Decision logic
        if not all_issues and not ecoli_pred.get('ecoli_present', False):
            # Water is safe
            return TreatmentRecommendation(
                primary_treatment=TreatmentMethod.NO_TREATMENT,
                secondary_treatments=[],
                rationale="Water quality parameters are within safe ranges and "
                         "no E. coli detected",
                urgency='SAFE',
                confidence=ecoli_pred.get('confidence', 1.0),
                parameters_of_concern=[]
            )
        
        # E. coli present = immediate action needed
        if ecoli_pred.get('ecoli_present', False):
            ecoli_confidence = ecoli_pred.get('confidence', 0.5)
            
            if ecoli_confidence > 0.9:
                urgency = 'CRITICAL'
                primary = TreatmentMethod.BOILING  # Most reliable for pathogens
                secondary = [
                    TreatmentMethod.UV_TREATMENT,
                    TreatmentMethod.CHLORINATION
                ]
                rationale = f"E. coli detected with {ecoli_confidence:.0%} confidence. " \
                           "Boiling is recommended as most effective against pathogens."
            else:
                urgency = 'WARNING'
                primary = TreatmentMethod.CHLORINATION  # Cost-effective
                secondary = [TreatmentMethod.FILTRATION]
                rationale = f"E. coli detected with {ecoli_confidence:.0%} confidence. " \
                           "Chlorination or boiling recommended."
        
        # Critical parameter issues
        elif critical_issues:
            urgency = 'CRITICAL'
            issue_names = [issue[0] for issue in critical_issues]
            
            # Map critical issues to treatments
            if 'turbidity' in issue_names:
                primary = TreatmentMethod.FILTRATION
                secondary = [TreatmentMethod.BOILING]
                rationale = "Severe turbidity requires immediate filtration. Consider boiling."
            elif 'chlorine_residual' in issue_names and \
                 parameters.get('chlorine_residual', 0) < 0.1:
                primary = TreatmentMethod.BOILING
                secondary = [TreatmentMethod.CHLORINATION, TreatmentMethod.UV_TREATMENT]
                rationale = "Critical: No disinfectant detected. Boiling essential."
            else:
                primary = TreatmentMethod.BOILING
                secondary = [TreatmentMethod.FILTRATION]
                rationale = f"Critical issues detected: {', '.join(issue_names)}"
        
        # Warning level issues
        elif warning_issues:
            urgency = 'WARNING'
            issue_names = [issue[0] for issue in warning_issues]
            
            # Recommend based on primary issue
            if 'turbidity' in issue_names:
                primary = TreatmentMethod.FILTRATION
                secondary = [TreatmentMethod.ACTIVATED_CARBON]
            elif 'chlorine_residual' in issue_names:
                primary = TreatmentMethod.CHLORINATION
                secondary = [TreatmentMethod.BOILING]
            else:
                primary = TreatmentMethod.FILTRATION
                secondary = [TreatmentMethod.ACTIVATED_CARBON, TreatmentMethod.BOILING]
            
            rationale = f"Issues detected requiring treatment: {', '.join(issue_names)}"
        
        # Caution level
        else:
            urgency = 'CAUTION'
            primary = TreatmentMethod.FILTRATION
            secondary = []
            rationale = "Minor water quality concerns. Basic filtration recommended."
        
        return TreatmentRecommendation(
            primary_treatment=primary,
            secondary_treatments=secondary,
            rationale=rationale,
            urgency=urgency,
            confidence=ecoli_pred.get('confidence', 0.5),
            parameters_of_concern=parameters_of_concern
        )
    
    def format_recommendation(self, rec: TreatmentRecommendation) -> str:
        """Format recommendation as human-readable text"""
        
        urgency_symbols = {
            'SAFE': '✓',
            'CAUTION': '⚠',
            'WARNING': '⚠⚠',
            'CRITICAL': '🚨'
        }
        
        symbol = urgency_symbols.get(rec.urgency, '?')
        
        output = f"\n{'='*70}\n"
        output += f"{symbol} WATER TREATMENT RECOMMENDATION [{rec.urgency}]\n"
        output += f"{'='*70}\n\n"
        
        output += f"PRIMARY TREATMENT: {rec.primary_treatment.value.replace('_', ' ').title()}\n"
        
        if rec.secondary_treatments:
            secondary_list = ', '.join([t.value.replace('_', ' ').title() 
                                       for t in rec.secondary_treatments])
            output += f"SECONDARY OPTIONS: {secondary_list}\n"
        
        output += f"\nRATIONALE:\n{rec.rationale}\n"
        
        if rec.parameters_of_concern:
            output += f"\nPARAMETERS OF CONCERN: {', '.join(rec.parameters_of_concern)}\n"
        
        output += f"\nCONFIDENCE: {rec.confidence:.0%}\n"
        output += f"{'='*70}\n"
        
        return output


# Example usage
if __name__ == "__main__":
    advisor = WaterTreatmentAdvisor()
    
    # Example 1: Safe water
    print("\n" + "="*70)
    print("EXAMPLE 1: SAFE WATER")
    print("="*70)
    
    safe_water = {
        'temperature': 22.0,
        'pH': 7.2,
        'turbidity': 0.5,
        'chlorine_residual': 0.7,
        'dissolved_oxygen': 8.0,
        'conductivity': 500
    }
    
    safe_ecoli = {
        'ecoli_present': False,
        'probability': 0.1,
        'confidence': 0.95
    }
    
    rec = advisor.analyze_water_quality(safe_water, safe_ecoli)
    print(advisor.format_recommendation(rec))
    
    # Example 2: E. coli detected
    print("\n" + "="*70)
    print("EXAMPLE 2: E. COLI DETECTED")
    print("="*70)
    
    contaminated_water = {
        'temperature': 25.0,
        'pH': 7.0,
        'turbidity': 1.5,
        'chlorine_residual': 0.1,  # Low disinfectant
        'dissolved_oxygen': 6.0,
        'conductivity': 550
    }
    
    contaminated_ecoli = {
        'ecoli_present': True,
        'probability': 0.92,
        'confidence': 0.94
    }
    
    rec = advisor.analyze_water_quality(contaminated_water, contaminated_ecoli)
    print(advisor.format_recommendation(rec))
    
    # Example 3: Warning level - poor parameters
    print("\n" + "="*70)
    print("EXAMPLE 3: HIGH TURBIDITY & LOW CHLORINE")
    print("="*70)
    
    poor_water = {
        'temperature': 20.0,
        'pH': 6.2,  # Low pH
        'turbidity': 3.0,  # High turbidity
        'chlorine_residual': 0.05,  # Very low chlorine
        'dissolved_oxygen': 4.0,  # Low oxygen
        'conductivity': 800
    }
    
    uncertain_ecoli = {
        'ecoli_present': True,
        'probability': 0.65,
        'confidence': 0.72
    }
    
    rec = advisor.analyze_water_quality(poor_water, uncertain_ecoli)
    print(advisor.format_recommendation(rec))
