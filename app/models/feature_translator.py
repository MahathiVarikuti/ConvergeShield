"""
ConvergeShield: Feature Translator Module
Converts technical SCADA features into human-readable explanations
"""


class FeatureTranslator:
    """
    Translates technical feature names and SHAP values into 
    operator-friendly explanations for industrial environments.
    """
    
    # Feature category mappings
    FEATURE_CATEGORIES = {
        # Tank Levels
        'L_T1': 'Tank 1 Water Level',
        'L_T2': 'Tank 2 Water Level',
        'L_T3': 'Tank 3 Water Level',
        'L_T4': 'Tank 4 Water Level',
        'L_T5': 'Tank 5 Water Level',
        'L_T6': 'Tank 6 Water Level',
        'L_T7': 'Tank 7 Water Level',
        
        # Pump Flows
        'F_PU1': 'Pump 1 Flow Rate',
        'F_PU2': 'Pump 2 Flow Rate',
        'F_PU3': 'Pump 3 Flow Rate',
        'F_PU4': 'Pump 4 Flow Rate',
        'F_PU5': 'Pump 5 Flow Rate',
        'F_PU6': 'Pump 6 Flow Rate',
        'F_PU7': 'Pump 7 Flow Rate',
        'F_PU8': 'Pump 8 Flow Rate',
        'F_PU9': 'Pump 9 Flow Rate',
        'F_PU10': 'Pump 10 Flow Rate',
        'F_PU11': 'Pump 11 Flow Rate',
        
        # Pump Status
        'S_PU1': 'Pump 1 Status',
        'S_PU2': 'Pump 2 Status',
        'S_PU3': 'Pump 3 Status',
        'S_PU4': 'Pump 4 Status',
        'S_PU5': 'Pump 5 Status',
        'S_PU6': 'Pump 6 Status',
        'S_PU7': 'Pump 7 Status',
        'S_PU8': 'Pump 8 Status',
        'S_PU9': 'Pump 9 Status',
        'S_PU10': 'Pump 10 Status',
        'S_PU11': 'Pump 11 Status',
        
        # Junction Pressures
        'P_J14': 'Junction 14 Pressure',
        'P_J256': 'Junction 256 Pressure',
        'P_J269': 'Junction 269 Pressure',
        'P_J280': 'Junction 280 Pressure',
        'P_J289': 'Junction 289 Pressure',
        'P_J300': 'Junction 300 Pressure',
        'P_J302': 'Junction 302 Pressure',
        'P_J306': 'Junction 306 Pressure',
        'P_J307': 'Junction 307 Pressure',
        'P_J317': 'Junction 317 Pressure',
        'P_J415': 'Junction 415 Pressure',
        'P_J422': 'Junction 422 Pressure',
        
        # Valves
        'F_V2': 'Valve 2 Flow Rate',
        'S_V2': 'Valve 2 Status',
    }
    
    # Pattern-based explanations
    BEHAVIOR_PATTERNS = {
        'tank_spike': 'Unusual tank level change',
        'pump_anomaly': 'Abnormal pump behavior',
        'pressure_deviation': 'Pressure anomaly detected',
        'flow_inconsistency': 'Unexpected flow pattern',
        'valve_irregularity': 'Valve control irregularity',
        'multiple_components': 'Coordinated system anomaly'
    }
    
    def translate_feature(self, feature_name):
        """Translate a single feature name to human-readable"""
        return self.FEATURE_CATEGORIES.get(feature_name, feature_name)
    
    def generate_human_reasons(self, shap_contributors, top_n=3):
        """
        Convert SHAP feature contributors into human-readable reasons.
        
        Args:
            shap_contributors: List of {feature, value, shap_value}
            top_n: Number of top reasons to return
            
        Returns:
            List of human-readable reason strings
        """
        if not shap_contributors:
            return ["Unusual system behavior detected"]
        
        reasons = []
        feature_types = set()
        
        for contrib in shap_contributors[:top_n]:
            feature = contrib['feature']
            shap_value = contrib['shap_value']
            
            # Categorize feature
            if feature.startswith('L_T'):
                category = 'tank'
                feature_types.add('tank')
            elif feature.startswith('F_PU'):
                category = 'pump_flow'
                feature_types.add('pump')
            elif feature.startswith('S_PU'):
                category = 'pump_status'
                feature_types.add('pump')
            elif feature.startswith('P_J'):
                category = 'pressure'
                feature_types.add('pressure')
            elif feature.startswith('F_V') or feature.startswith('S_V'):
                category = 'valve'
                feature_types.add('valve')
            else:
                category = 'unknown'
            
            # Generate human explanation
            human_name = self.translate_feature(feature)
            
            if shap_value > 0:
                direction = "elevated" if category in ['pressure', 'tank', 'pump_flow'] else "activated unexpectedly"
            else:
                direction = "decreased abnormally" if category in ['pressure', 'tank', 'pump_flow'] else "deactivated unexpectedly"
            
            reason = f"{human_name} {direction}"
            reasons.append(reason)
        
        # Add pattern-based summary if multiple component types affected
        if len(feature_types) > 2:
            reasons.insert(0, "Multiple system components showing abnormal behavior")
        
        return reasons[:top_n]
    
    def detect_attack_pattern(self, shap_contributors):
        """
        Detect the likely attack pattern based on affected features.
        
        Returns:
            String describing the attack pattern
        """
        if not shap_contributors:
            return "Unknown anomaly"
        
        feature_names = [c['feature'] for c in shap_contributors[:5]]
        
        # Pattern detection
        has_tanks = any(f.startswith('L_T') for f in feature_names)
        has_pumps = any(f.startswith('F_PU') or f.startswith('S_PU') for f in feature_names)
        has_pressure = any(f.startswith('P_J') for f in feature_names)
        has_valves = any(f.startswith('V') for f in feature_names)
        
        affected_count = sum([has_tanks, has_pumps, has_pressure, has_valves])
        
        if affected_count >= 3:
            return "Coordinated multi-component attack"
        elif has_pumps and has_tanks:
            return "Pump/tank manipulation attack"
        elif has_pumps:
            return "Unauthorized pump control"
        elif has_tanks:
            return "Tank level manipulation"
        elif has_pressure:
            return "Pressure system attack"
        elif has_valves:
            return "Valve tampering attempt"
        else:
            return "Suspicious industrial activity"
    
    def get_severity_indicator(self, physics_violations, ml_confidence):
        """
        Determine severity level based on detections.
        
        Returns:
            Tuple of (severity_level, severity_color, severity_icon)
        """
        if physics_violations >= 5 or ml_confidence > 0.8:
            return ("CRITICAL", "#dc2626", "fa-skull-crossbones")
        elif physics_violations >= 3 or ml_confidence > 0.6:
            return ("HIGH", "#f59e0b", "fa-exclamation-triangle")
        elif physics_violations >= 1 or ml_confidence > 0.4:
            return ("MEDIUM", "#eab308", "fa-exclamation-circle")
        else:
            return ("LOW", "#10b981", "fa-info-circle")
