"""
SENTINEL-OT: IPS Recommender Module
Provides AI-powered security recommendations based on detected anomalies
"""
import numpy as np
from datetime import datetime


class IPSRecommender:
    """
    Intrusion Prevention System (IPS) Recommendation Engine.
    Generates actionable security recommendations based on:
    - ML model predictions
    - SHAP explanations
    - Physics validation results
    """
    
    def __init__(self):
        # Attack type signatures based on SCADA features
        self.attack_signatures = {
            'pump_manipulation': {
                'features': ['F_PU', 'S_PU'],
                'description': 'Unauthorized pump control manipulation',
                'severity': 'critical',
                'response': 'Isolate affected pump controllers, verify PLC integrity'
            },
            'tank_overflow': {
                'features': ['L_T'],
                'description': 'Tank level manipulation attack (potential overflow/underflow)',
                'severity': 'critical',
                'response': 'Enable manual tank level controls, alert field operators'
            },
            'pressure_attack': {
                'features': ['P_J'],
                'description': 'Pressure sensor manipulation or DoS on pressure monitors',
                'severity': 'high',
                'response': 'Cross-verify with physical gauges, check network for spoofed packets'
            },
            'valve_tampering': {
                'features': ['F_V', 'S_V'],
                'description': 'Valve control tampering detected',
                'severity': 'high',
                'response': 'Lock valve actuators, initiate manual override protocol'
            },
            'coordinated_attack': {
                'features': ['multiple'],
                'description': 'Coordinated multi-component attack detected',
                'severity': 'critical',
                'response': 'Activate emergency shutdown protocol, isolate SCADA network'
            },
            'data_injection': {
                'features': ['rate_of_change'],
                'description': 'False data injection attack suspected',
                'severity': 'high',
                'response': 'Enable redundant sensor validation, check communication channels'
            }
        }
        
        # Severity levels and their properties
        self.severity_levels = {
            'critical': {'priority': 1, 'color': '#ff4444', 'auto_block': True},
            'high': {'priority': 2, 'color': '#ff8800', 'auto_block': False},
            'medium': {'priority': 3, 'color': '#ffbb00', 'auto_block': False},
            'low': {'priority': 4, 'color': '#88cc00', 'auto_block': False}
        }
        
        # Action log
        self.action_log = []
    
    def analyze_threat(self, shap_explanation, physics_result, ml_confidence):
        """
        Analyze detected threat and determine attack type.
        """
        if not shap_explanation:
            return None
        
        top_features = shap_explanation.get('top_contributors', [])[:5]
        feature_names = [f['feature'] for f in top_features]
        
        # Identify attack type based on affected features
        detected_attacks = []
        
        for attack_type, signature in self.attack_signatures.items():
            sig_features = signature['features']
            
            if sig_features == ['multiple']:
                # Check for coordinated attack (multiple categories affected)
                categories = set()
                for fn in feature_names:
                    if fn.startswith('L_T'): categories.add('tank')
                    elif fn.startswith('F_PU') or fn.startswith('S_PU'): categories.add('pump')
                    elif fn.startswith('P_J'): categories.add('pressure')
                    elif fn.startswith('F_V') or fn.startswith('S_V'): categories.add('valve')
                
                if len(categories) >= 3:
                    detected_attacks.append(attack_type)
            else:
                for sig_feat in sig_features:
                    if any(fn.startswith(sig_feat) for fn in feature_names):
                        detected_attacks.append(attack_type)
                        break
        
        # Check physics violations
        if physics_result and physics_result.get('has_critical'):
            if 'coordinated_attack' not in detected_attacks:
                detected_attacks.append('data_injection')
        
        # Determine primary attack type (highest severity)
        if detected_attacks:
            primary_attack = min(detected_attacks, 
                               key=lambda x: self.severity_levels[self.attack_signatures[x]['severity']]['priority'])
        else:
            primary_attack = 'unknown'
        
        return {
            'primary_attack': primary_attack,
            'all_detected': detected_attacks,
            'affected_features': feature_names,
            'ml_confidence': ml_confidence
        }
    
    def generate_recommendation(self, threat_analysis, shap_explanation, physics_result):
        """
        Generate comprehensive security recommendation.
        """
        if not threat_analysis:
            return {
                'severity': 'low',
                'action': 'Monitor',
                'description': 'No specific threat pattern identified',
                'recommendations': ['Continue monitoring', 'Review in next analysis cycle']
            }
        
        primary_attack = threat_analysis['primary_attack']
        
        if primary_attack == 'unknown':
            severity = 'medium'
            signature = {
                'description': 'Anomalous behavior detected',
                'response': 'Investigate affected components and review logs'
            }
        else:
            signature = self.attack_signatures[primary_attack]
            severity = signature['severity']
        
        sev_props = self.severity_levels[severity]
        
        # Build recommendations
        recommendations = [signature.get('response', 'Investigate')]
        
        # Add physics-based recommendations
        if physics_result and physics_result.get('violations'):
            for violation in physics_result['violations'][:3]:
                rule = violation.get('rule', '')
                if rule == 'pump_flow_consistency':
                    recommendations.append(f"Verify Pump {violation.get('pump_id', '?')} physical status")
                elif rule == 'tank_bounds':
                    recommendations.append("Check tank level sensors for tampering")
                elif rule == 'rate_of_change':
                    recommendations.append("Investigate rapid sensor value changes")
        
        # Add SHAP-based recommendations
        if shap_explanation:
            top_contrib = shap_explanation.get('top_contributors', [])[:2]
            for contrib in top_contrib:
                feat = contrib['feature']
                if contrib['direction'] == 'increases_risk':
                    recommendations.append(f"High-risk feature: {feat} - verify sensor/actuator")
        
        # Build final recommendation object
        recommendation = {
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'severity_color': sev_props['color'],
            'priority': sev_props['priority'],
            'auto_block': sev_props['auto_block'],
            'attack_type': primary_attack,
            'attack_description': signature['description'],
            'action': 'BLOCK' if sev_props['auto_block'] else 'ALERT',
            'recommendations': recommendations,
            'affected_components': threat_analysis.get('affected_features', []),
            'confidence': threat_analysis.get('ml_confidence', 0)
        }
        
        # Log action
        self.action_log.append(recommendation)
        
        return recommendation
    
    def process_detection(self, sample_data, ml_prediction, ml_confidence, 
                         shap_explanation=None, physics_result=None):
        """
        Full IPS processing pipeline for a single detection.
        """
        if ml_prediction == 0:  # Normal
            return {
                'status': 'normal',
                'action': 'none',
                'recommendation': None
            }
        
        # Analyze threat
        threat_analysis = self.analyze_threat(shap_explanation, physics_result, ml_confidence)
        
        # Generate recommendation
        recommendation = self.generate_recommendation(
            threat_analysis, shap_explanation, physics_result
        )
        
        return {
            'status': 'anomaly',
            'action': recommendation['action'],
            'recommendation': recommendation
        }
    
    def get_statistics(self):
        """Get IPS statistics"""
        if not self.action_log:
            return {
                'total_alerts': 0,
                'by_severity': {},
                'by_attack_type': {},
                'blocked': 0
            }
        
        by_severity = {}
        by_attack_type = {}
        blocked = 0
        
        for action in self.action_log:
            sev = action.get('severity', 'unknown')
            by_severity[sev] = by_severity.get(sev, 0) + 1
            
            attack = action.get('attack_type', 'unknown')
            by_attack_type[attack] = by_attack_type.get(attack, 0) + 1
            
            if action.get('auto_block'):
                blocked += 1
        
        return {
            'total_alerts': len(self.action_log),
            'by_severity': by_severity,
            'by_attack_type': by_attack_type,
            'blocked': blocked,
            'recent_alerts': self.action_log[-10:]  # Last 10 alerts
        }
    
    def clear_log(self):
        """Clear action log"""
        self.action_log = []


if __name__ == '__main__':
    # Test IPS Recommender
    recommender = IPSRecommender()
    
    # Simulate a threat analysis
    mock_shap = {
        'top_contributors': [
            {'feature': 'F_PU2', 'shap_value': 0.45, 'direction': 'increases_risk'},
            {'feature': 'S_PU2', 'shap_value': 0.38, 'direction': 'increases_risk'},
            {'feature': 'L_T3', 'shap_value': 0.22, 'direction': 'increases_risk'}
        ]
    }
    
    mock_physics = {
        'is_valid': False,
        'violations': [
            {'rule': 'pump_flow_consistency', 'pump_id': 2, 'severity': 'critical'}
        ],
        'has_critical': True
    }
    
    # Process detection
    result = recommender.process_detection(
        sample_data=None,
        ml_prediction=1,
        ml_confidence=0.87,
        shap_explanation=mock_shap,
        physics_result=mock_physics
    )
    
    print("IPS Recommendation:")
    print(f"  Status: {result['status']}")
    print(f"  Action: {result['action']}")
    if result['recommendation']:
        rec = result['recommendation']
        print(f"  Severity: {rec['severity']}")
        print(f"  Attack Type: {rec['attack_type']}")
        print(f"  Description: {rec['attack_description']}")
        print(f"  Recommendations:")
        for r in rec['recommendations']:
            print(f"    - {r}")
