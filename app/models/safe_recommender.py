"""
ConvergeShield: Safe Recommendation Engine
Provides OT-safe, actionable recommendations (no auto-blocking)
"""


class SafeRecommendationEngine:
    """
    Generates SAFE, actionable recommendations for OT environments.
    Key principle: Decision support, NOT automation.
    Never suggests automatic blocking or shutdowns.
    """
    
    # Safe recommendation templates
    SAFE_ACTIONS = {
        'critical': [
            "🔍 Immediately verify system integrity with field inspection",
            "📞 Alert control room operators and security team",
            "📊 Review recent activity logs and access records",
            "🔐 Verify authentication credentials for recent sessions",
            "⚠️ Consider isolating affected components if issue persists",
            "📝 Document incident details for investigation"
        ],
        'high': [
            "🔍 Monitor affected components closely for next 30 minutes",
            "📊 Cross-check with physical sensors and gauges",
            "📞 Notify security operations center (SOC)",
            "🔐 Review recent user access and commands",
            "⚠️ Restrict non-essential operations temporarily",
            "📝 Log incident for pattern analysis"
        ],
        'medium': [
            "🔍 Monitor system behavior for unusual patterns",
            "📊 Verify readings match expected operational ranges",
            "📞 Inform shift supervisor of anomaly",
            "🔐 Check for unauthorized access attempts",
            "⚠️ Increase monitoring frequency",
            "📝 Record event in security log"
        ],
        'low': [
            "🔍 Continue normal monitoring",
            "📊 Verify readings are within acceptable range",
            "📝 Note event in daily operations log",
            "⚠️ Watch for repeat occurrences"
        ]
    }
    
    # Component-specific recommendations
    COMPONENT_RECOMMENDATIONS = {
        'pump': {
            'critical': "Verify pump controller integrity and check for unauthorized commands",
            'high': "Monitor pump flow rates and compare with expected operation schedule",
            'medium': "Check pump status indicators match control system readings"
        },
        'tank': {
            'critical': "Manually verify tank levels with dipstick or visual inspection",
            'high': "Cross-check level sensors with backup measurement systems",
            'medium': "Monitor tank fill/drain rates for consistency"
        },
        'pressure': {
            'critical': "Compare pressure readings with physical gauges immediately",
            'high': "Verify pressure sensor calibration and check for spoofed data",
            'medium': "Monitor pressure trends across multiple junction points"
        },
        'valve': {
            'critical': "Manually verify valve positions match control signals",
            'high': "Check valve actuator logs for unexpected commands",
            'medium': "Monitor valve operation cycles for irregularities"
        }
    }
    
    # Attack pattern specific recommendations
    ATTACK_SPECIFIC_ACTIONS = {
        'sensor_manipulation': {
            'critical': [
                "🔍 Immediately validate sensor readings with manual measurements",
                "📊 Cross-reference with backup sensors and historical data",
                "🚨 Isolate affected sensor networks from main control system",
                "📞 Contact field technicians for physical sensor inspection"
            ],
            'high': [
                "🔍 Compare sensor readings with expected operational ranges",
                "📊 Check sensor calibration logs for recent changes",
                "📞 Verify sensor integrity with maintenance team"
            ],
            'medium': [
                "🔍 Monitor sensor drift patterns for anomalies",
                "📊 Log sensor variance for trend analysis"
            ]
        },
        'actuator_manipulation': {
            'critical': [
                "🔧 Immediately switch to manual actuator control mode",
                "🔍 Verify actuator positions match control commands",
                "🚨 Lock out remote actuator access until investigation complete",
                "📞 Dispatch field operators to verify valve/pump positions"
            ],
            'high': [
                "🔧 Monitor actuator response times for deviations",
                "🔍 Cross-check actuator status with expected operations",
                "📞 Verify no unauthorized maintenance is in progress"
            ],
            'medium': [
                "🔧 Check actuator operation logs for irregularities",
                "🔍 Monitor for unexpected start/stop commands"
            ]
        },
        'command_injection': {
            'critical': [
                "🛡️ Immediately review recent command logs for unauthorized entries",
                "🔐 Change all administrative passwords and access codes",
                "🚨 Isolate compromised systems from network immediately",
                "📞 Activate incident response team and forensic analysis"
            ],
            'high': [
                "🛡️ Audit user access logs for suspicious activity patterns",
                "🔐 Verify authentication tokens and session validity",
                "📞 Review recent administrative access attempts"
            ],
            'medium': [
                "🛡️ Monitor command execution patterns for anomalies",
                "🔐 Log administrative actions for review"
            ]
        },
        'coordinated_attack': {
            'critical': [
                "🚨 Activate emergency response protocol immediately",
                "🔒 Isolate entire affected system from external networks",
                "📞 Contact security operations center and plant management",
                "🛡️ Initiate backup control systems if available"
            ],
            'high': [
                "🚨 Increase monitoring on all interconnected systems",
                "🔒 Restrict network access to essential operations only",
                "📞 Alert cybersecurity incident response team"
            ]
        },
        'pressure_attack': {
            'critical': [
                "⚡ Immediately verify pressure readings with manual gauges",
                "🔧 Check pressure relief valve operation status",
                "🚨 Prepare for emergency shutdown if pressures exceed limits",
                "📞 Alert process engineers and safety officers"
            ],
            'high': [
                "⚡ Monitor pressure trends across all measurement points",
                "🔧 Verify pressure control loop integrity"
            ]
        },
        'tank_overflow': {
            'critical': [
                "🛢️ Immediately check tank levels with visual inspection",
                "⚡ Verify overflow protection systems are operational",
                "🔧 Switch to manual tank level control if needed",
                "📞 Position operators near critical tank areas"
            ],
            'high': [
                "🛢️ Monitor tank fill/drain rates for consistency",
                "⚡ Check level sensor calibration and functionality"
            ]
        }
    }

    def generate_recommendations(self, severity, affected_components, attack_pattern, physics_violations):
        """
        Generate safe, actionable recommendations with attack-specific customization.
        
        Args:
            severity: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
            affected_components: List of component types (e.g., ['pump', 'tank'])
            attack_pattern: Description of detected pattern
            physics_violations: Number of physics rule violations
            
        Returns:
            Dict with structured recommendations
        """
        severity_lower = severity.lower()
        
        # Try to match attack pattern to specific recommendations
        pattern_key = self._map_attack_pattern_to_key(attack_pattern)
        attack_specific_actions = []
        
        if pattern_key and pattern_key in self.ATTACK_SPECIFIC_ACTIONS:
            attack_actions = self.ATTACK_SPECIFIC_ACTIONS[pattern_key].get(severity_lower, [])
            attack_specific_actions = attack_actions[:3]  # Top 3 attack-specific actions
        
        # Base recommendations for severity level
        base_actions = self.SAFE_ACTIONS.get(severity_lower, self.SAFE_ACTIONS['low'])
        
        # Component-specific recommendations
        component_actions = []
        for comp in set(affected_components):
            if comp in self.COMPONENT_RECOMMENDATIONS:
                comp_rec = self.COMPONENT_RECOMMENDATIONS[comp].get(severity_lower)
                if comp_rec:
                    component_actions.append(f"🔧 {comp_rec}")
        
        # Prioritize attack-specific actions, then component-specific, then base actions
        priority_actions = []
        if attack_specific_actions:
            priority_actions.extend(attack_specific_actions)
        if component_actions and len(priority_actions) < 4:
            priority_actions.extend(component_actions[:2])
        if len(priority_actions) < 4:
            remaining_slots = 4 - len(priority_actions)
            priority_actions.extend(base_actions[:remaining_slots])
        
        # Safety note with attack context
        safety_note = self._get_safety_note(severity_lower, physics_violations, attack_pattern)
        
        return {
            'severity': severity,
            'attack_pattern': attack_pattern,
            'priority_actions': priority_actions[:4],  # Limit to 4 actions
            'safety_note': safety_note,
            'escalation_required': severity_lower in ['critical', 'high'],
            'attack_type': pattern_key,
            'timestamp': None  # Will be set by caller
        }
    
    def _map_attack_pattern_to_key(self, attack_pattern):
        """Map attack pattern description to specific action key"""
        pattern_lower = attack_pattern.lower()
        
        if 'sensor' in pattern_lower or 'tank' in pattern_lower and 'manipulation' in pattern_lower:
            return 'sensor_manipulation'
        elif 'pump' in pattern_lower and ('control' in pattern_lower or 'manipulation' in pattern_lower):
            return 'actuator_manipulation'
        elif 'command' in pattern_lower or 'injection' in pattern_lower:
            return 'command_injection'
        elif 'coordinated' in pattern_lower or 'multi-component' in pattern_lower:
            return 'coordinated_attack'
        elif 'pressure' in pattern_lower:
            return 'pressure_attack'
        elif 'tank' in pattern_lower and 'level' in pattern_lower:
            return 'tank_overflow'
        else:
            return None
    
    def _get_safety_note(self, severity, physics_violations, attack_pattern=None):
        """Generate safety-focused note with attack context"""
        base_note = ""
        
        if severity == 'critical':
            if physics_violations >= 5:
                base_note = "⚠️ SAFETY ALERT: Multiple physics violations detected. Do not override safety protocols without supervisor approval."
            else:
                base_note = "⚠️ HIGH PRIORITY: Immediate operator attention required. Verify physical safety before proceeding."
        elif severity == 'high':
            base_note = "⚠️ CAUTION: Verify operations with field personnel before making changes."
        elif severity == 'medium':
            base_note = "ℹ️ ADVISORY: Continue normal operations with increased vigilance."
        else:
            base_note = "ℹ️ INFO: Normal monitoring recommended."
        
        # Add attack-specific safety context
        if attack_pattern:
            pattern_lower = attack_pattern.lower()
            if 'command' in pattern_lower or 'injection' in pattern_lower:
                base_note += " Potential unauthorized system access detected - change passwords immediately."
            elif 'coordinated' in pattern_lower:
                base_note += " Multi-system attack suspected - consider network isolation."
            elif 'pressure' in pattern_lower:
                base_note += " Pressure anomalies can cause equipment damage or injury."
            elif 'tank' in pattern_lower:
                base_note += " Tank level anomalies may lead to overflow or process disruption."
        
        return base_note
    
    def get_simple_action_list(self, severity):
        """
        Get a simplified action checklist for dashboard display.
        
        Returns:
            List of 3-4 simple action items
        """
        severity_lower = severity.lower()
        
        simple_actions = {
            'critical': [
                "Verify system with field inspection",
                "Alert operators and security team",
                "Review recent activity logs",
                "Restrict non-critical operations"
            ],
            'high': [
                "Monitor affected components closely",
                "Cross-check with physical sensors",
                "Review user access records",
                "Notify security operations"
            ],
            'medium': [
                "Monitor system behavior",
                "Verify operational ranges",
                "Inform shift supervisor",
                "Increase monitoring frequency"
            ],
            'low': [
                "Continue normal monitoring",
                "Verify readings",
                "Note event in log"
            ]
        }
        
        return simple_actions.get(severity_lower, simple_actions['low'])
    
    def get_do_not_actions(self):
        """
        List of what NOT to do (OT safety principles).
        """
        return [
            "❌ DO NOT automatically shut down systems",
            "❌ DO NOT block traffic without verification",
            "❌ DO NOT override physical safety controls",
            "❌ DO NOT take action without operator approval"
        ]
