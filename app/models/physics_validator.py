"""
SENTINEL-OT: Physics-Based Validation Layer
Implements SCADA-specific rules for validating anomaly detections
"""
import numpy as np


class PhysicsValidator:
    """
    Validates anomaly detections using SCADA physics rules.
    Reduces false positives by checking physical feasibility.
    """
    
    def __init__(self):
        # BATADAL-specific thresholds (water distribution system)
        self.tank_bounds = (0, 10)  # Tank level bounds (meters)
        self.pressure_bounds = (0, 120)  # Pressure bounds (psi)
        self.flow_bounds = (0, 150)  # Flow rate bounds (L/s)
        
        # Feature indices (assuming BATADAL column order)
        self.tank_indices = list(range(0, 7))  # L_T1 to L_T7
        self.pump_flow_indices = [7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27]  # F_PU1-11
        self.pump_status_indices = [8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28]  # S_PU1-11
        self.valve_flow_idx = 29  # F_V2
        self.valve_status_idx = 30  # S_V2
        self.pressure_indices = list(range(31, 43))  # P_J*
        
    def check_tank_bounds(self, sample):
        """Check if tank levels are within physical bounds"""
        violations = []
        for idx in self.tank_indices:
            if idx < len(sample):
                level = sample[idx]
                if level < self.tank_bounds[0] or level > self.tank_bounds[1]:
                    violations.append({
                        'rule': 'tank_bounds',
                        'feature_idx': idx,
                        'value': level,
                        'bounds': self.tank_bounds,
                        'severity': 'high' if abs(level) > 20 else 'medium'
                    })
        return violations
    
    def check_pump_flow_consistency(self, sample):
        """Check: If pump is OFF, flow should be ~0"""
        violations = []
        for i, (flow_idx, status_idx) in enumerate(
            zip(self.pump_flow_indices, self.pump_status_indices)):
            if flow_idx < len(sample) and status_idx < len(sample):
                flow = sample[flow_idx]
                status = sample[status_idx]
                
                # If pump OFF (status=0) but significant flow detected
                if status == 0 and abs(flow) > 5:
                    violations.append({
                        'rule': 'pump_flow_consistency',
                        'pump_id': i + 1,
                        'status': status,
                        'flow': flow,
                        'severity': 'critical'
                    })
                # If pump ON but no flow (could indicate blockage or attack)
                elif status == 1 and abs(flow) < 1:
                    violations.append({
                        'rule': 'pump_no_flow',
                        'pump_id': i + 1,
                        'status': status,
                        'flow': flow,
                        'severity': 'high'
                    })
        return violations
    
    def check_pressure_bounds(self, sample):
        """Check if pressure readings are within physical bounds"""
        violations = []
        for idx in self.pressure_indices:
            if idx < len(sample):
                pressure = sample[idx]
                if pressure < self.pressure_bounds[0] or pressure > self.pressure_bounds[1]:
                    violations.append({
                        'rule': 'pressure_bounds',
                        'feature_idx': idx,
                        'value': pressure,
                        'bounds': self.pressure_bounds,
                        'severity': 'high' if pressure > 150 else 'medium'
                    })
        return violations
    
    def check_rate_of_change(self, current_sample, previous_sample, time_delta=1):
        """Check for physically impossible rate of change in tank levels"""
        violations = []
        if previous_sample is None:
            return violations
            
        max_rate = 2.0  # Maximum realistic rate of change per time unit
        
        for idx in self.tank_indices:
            if idx < len(current_sample) and idx < len(previous_sample):
                rate = abs(current_sample[idx] - previous_sample[idx]) / time_delta
                if rate > max_rate:
                    violations.append({
                        'rule': 'rate_of_change',
                        'feature_idx': idx,
                        'rate': rate,
                        'max_rate': max_rate,
                        'severity': 'critical'
                    })
        return violations
    
    def check_correlated_sensors(self, sample):
        """
        Check for suspicious patterns in correlated sensors.
        In water systems, multiple related sensors should show consistent behavior.
        """
        violations = []
        
        # Check if all pumps suddenly change state simultaneously
        pump_statuses = [sample[idx] for idx in self.pump_status_indices if idx < len(sample)]
        if len(set(pump_statuses)) == 1 and len(pump_statuses) > 3:
            # All pumps in same state - could be coordinated attack
            violations.append({
                'rule': 'correlated_pump_states',
                'pattern': 'all_same_state',
                'state': pump_statuses[0],
                'severity': 'medium'
            })
        
        return violations
    
    def validate_sample(self, sample, previous_sample=None):
        """
        Perform all physics validations on a sample.
        Returns validation result with all violations found.
        """
        all_violations = []
        
        all_violations.extend(self.check_tank_bounds(sample))
        all_violations.extend(self.check_pump_flow_consistency(sample))
        all_violations.extend(self.check_pressure_bounds(sample))
        all_violations.extend(self.check_rate_of_change(sample, previous_sample))
        all_violations.extend(self.check_correlated_sensors(sample))
        
        # Calculate overall physics anomaly score
        severity_weights = {'critical': 1.0, 'high': 0.7, 'medium': 0.4, 'low': 0.2}
        physics_score = sum(
            severity_weights.get(v.get('severity', 'low'), 0.2) 
            for v in all_violations
        )
        physics_score = min(physics_score / 3.0, 1.0)  # Normalize to 0-1
        
        return {
            'is_valid': len(all_violations) == 0,
            'violations': all_violations,
            'violation_count': len(all_violations),
            'physics_anomaly_score': physics_score,
            'has_critical': any(v.get('severity') == 'critical' for v in all_violations)
        }
    
    def validate_batch(self, X):
        """Validate a batch of samples"""
        results = []
        previous = None
        
        for i, sample in enumerate(X):
            result = self.validate_sample(sample, previous)
            result['sample_idx'] = i
            results.append(result)
            previous = sample
        
        return results
    
    def get_physics_scores(self, X):
        """Get physics anomaly scores for batch (for ensemble integration)"""
        results = self.validate_batch(X)
        return np.array([r['physics_anomaly_score'] for r in results])
    
    def enhance_predictions(self, ml_predictions, ml_scores, X, weight=0.2):
        """
        Enhance ML predictions with physics validation.
        Combines ML anomaly scores with physics-based scores.
        """
        physics_scores = self.get_physics_scores(X)
        
        # Weighted combination
        enhanced_scores = (1 - weight) * ml_scores + weight * physics_scores
        
        # Also flag samples where physics violations are critical
        validation_results = self.validate_batch(X)
        critical_flags = np.array([r['has_critical'] for r in validation_results])
        
        # Force prediction to 1 (anomaly) if critical physics violation
        enhanced_predictions = ml_predictions.copy()
        enhanced_predictions[critical_flags] = 1
        
        return enhanced_predictions, enhanced_scores, validation_results


if __name__ == '__main__':
    # Test physics validator
    validator = PhysicsValidator()
    
    # Create a test sample (normal)
    normal_sample = np.array([
        2.5, 3.0, 2.8, 4.0, 3.5, 5.0, 4.0,  # Tank levels (normal)
        50.0, 1, 45.0, 1, 0.0, 0, 30.0, 1, 0.0, 0, 0.0, 0, 40.0, 1, 35.0, 1, 0.0, 0, 25.0, 1, 0.0, 0,  # Pumps
        80.0, 1,  # Valve
        30.0, 35.0, 28.0, 85.0, 27.0, 85.0, 20.0, 82.0, 20.0, 70.0, 30.0, 28.0  # Pressures
    ])
    
    # Create an anomalous sample (pump OFF but flow detected)
    attack_sample = normal_sample.copy()
    attack_sample[9] = 0  # Pump 2 status = OFF
    attack_sample[8] = 50.0  # But flow is 50 (impossible!)
    
    print("Normal sample validation:")
    result = validator.validate_sample(normal_sample)
    print(f"  Valid: {result['is_valid']}")
    print(f"  Violations: {result['violation_count']}")
    
    print("\nAttack sample validation:")
    result = validator.validate_sample(attack_sample)
    print(f"  Valid: {result['is_valid']}")
    print(f"  Violations: {result['violation_count']}")
    for v in result['violations']:
        print(f"    - {v['rule']}: {v.get('severity', 'unknown')}")
