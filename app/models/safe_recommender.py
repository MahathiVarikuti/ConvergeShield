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
    
    def generate_recommendations(self, severity, affected_components, attack_pattern, physics_violations):
        """
        Generate safe, actionable recommendations.
        
        Args:
            severity: "CRITICAL", "HIGH", "MEDIUM", or "LOW"
            affected_components: List of component types (e.g., ['pump', 'tank'])
            attack_pattern: Description of detected pattern
            physics_violations: Number of physics rule violations
            
        Returns:
            Dict with structured recommendations
        """
        severity_lower = severity.lower()
        
        # Base recommendations for severity level
        base_actions = self.SAFE_ACTIONS.get(severity_lower, self.SAFE_ACTIONS['low'])
        
        # Component-specific recommendations
        component_actions = []
        for comp in set(affected_components):
            if comp in self.COMPONENT_RECOMMENDATIONS:
                comp_rec = self.COMPONENT_RECOMMENDATIONS[comp].get(severity_lower)
                if comp_rec:
                    component_actions.append(f"🔧 {comp_rec}")
        
        # Priority actions (top 4-5)
        priority_count = 5 if severity_lower in ['critical', 'high'] else 4
        priority_actions = base_actions[:priority_count]
        
        # Add component-specific if available
        if component_actions:
            priority_actions = component_actions[:2] + priority_actions[:3]
        
        # Safety note
        safety_note = self._get_safety_note(severity_lower, physics_violations)
        
        return {
            'severity': severity,
            'attack_pattern': attack_pattern,
            'priority_actions': priority_actions,
            'safety_note': safety_note,
            'escalation_required': severity_lower in ['critical', 'high'],
            'timestamp': None  # Will be set by caller
        }
    
    def _get_safety_note(self, severity, physics_violations):
        """Generate safety-focused note"""
        if severity == 'critical':
            if physics_violations >= 5:
                return "⚠️ SAFETY ALERT: Multiple physics violations detected. Do not override safety protocols without supervisor approval."
            return "⚠️ HIGH PRIORITY: Immediate operator attention required. Verify physical safety before proceeding."
        elif severity == 'high':
            return "⚠️ CAUTION: Verify operations with field personnel before making changes."
        elif severity == 'medium':
            return "ℹ️ ADVISORY: Continue normal operations with increased vigilance."
        else:
            return "ℹ️ INFO: Normal monitoring recommended."
    
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
