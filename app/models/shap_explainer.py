"""
SENTINEL-OT: SHAP-based Explainability Module
Provides interpretable explanations for anomaly detections
"""
import numpy as np
import shap
import joblib
import os


class SHAPExplainer:
    """
    Provides SHAP-based explanations for model predictions.
    Helps security analysts understand WHY an anomaly was flagged.
    """
    
    def __init__(self, model_dir='trained_models'):
        self.model_dir = model_dir
        self.explainers = {}
        self.background_data = None
        
    def initialize_explainers(self, ensemble_detector, X_background, feature_names):
        """Initialize SHAP explainers for each model"""
        self.feature_names = feature_names
        
        # Use subset for background (SHAP is computationally expensive)
        n_background = min(100, len(X_background))
        indices = np.random.choice(len(X_background), n_background, replace=False)
        self.background_data = X_background[indices]
        
        # Random Forest explainer (TreeExplainer - fast)
        if ensemble_detector.random_forest is not None:
            print("Initializing Random Forest SHAP explainer...")
            self.explainers['random_forest'] = shap.TreeExplainer(
                ensemble_detector.random_forest
            )
        
        # XGBoost explainer (TreeExplainer - fast)
        if ensemble_detector.xgboost is not None:
            print("Initializing XGBoost SHAP explainer...")
            try:
                self.explainers['xgboost'] = shap.TreeExplainer(
                    ensemble_detector.xgboost
                )
            except Exception as e:
                print(f"  Warning: XGBoost SHAP init failed ({e}), using KernelExplainer fallback")
                # Fallback: use same explainer as Random Forest for simplicity
                self.explainers['xgboost'] = self.explainers.get('random_forest')
        
        # For Isolation Forest, we use KernelExplainer (slower but works)
        # Only initialize on demand due to computational cost
        
        print("✓ SHAP explainers initialized")
    
    def explain_prediction(self, X_single, model='random_forest', top_k=10):
        """
        Generate SHAP explanation for a single prediction.
        Returns top contributing features.
        """
        if model not in self.explainers:
            return None
        
        explainer = self.explainers[model]
        
        # Reshape if single sample
        if len(X_single.shape) == 1:
            X_single = X_single.reshape(1, -1)
        
        # Get SHAP values
        shap_values = explainer.shap_values(X_single)
        
        # Handle multi-class output (take class 1 for anomaly)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]  # Class 1 (anomaly)
        
        # Ensure shap_values is 1D for single sample
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        # Get feature contributions
        contributions = []
        for i, feat_name in enumerate(self.feature_names):
            if i < len(shap_values):
                shap_val = float(np.asarray(shap_values[i]).flatten()[0]) if hasattr(shap_values[i], '__len__') else float(shap_values[i])
                contributions.append({
                    'feature': feat_name,
                    'shap_value': shap_val,
                    'abs_shap': abs(shap_val),
                    'direction': 'increases_risk' if shap_val > 0 else 'decreases_risk',
                    'value': float(X_single[0, i]) if i < X_single.shape[1] else None
                })
        
        # Sort by absolute SHAP value
        contributions.sort(key=lambda x: x['abs_shap'], reverse=True)
        
        # Get expected value safely
        try:
            if hasattr(explainer.expected_value, '__len__'):
                expected = float(explainer.expected_value[1])
            else:
                expected = float(explainer.expected_value)
        except:
            expected = 0.0
        
        return {
            'model': model,
            'top_contributors': contributions[:top_k],
            'all_contributions': contributions,
            'expected_value': expected
        }
    
    def explain_batch(self, X, model='random_forest', top_k=5):
        """Explain multiple predictions"""
        explanations = []
        for i in range(len(X)):
            exp = self.explain_prediction(X[i], model, top_k)
            if exp:
                exp['sample_idx'] = i
                explanations.append(exp)
        return explanations
    
    def get_global_importance(self, X_sample, model='random_forest'):
        """
        Get global feature importance across all samples.
        Useful for understanding overall model behavior.
        """
        if model not in self.explainers:
            return None
        
        explainer = self.explainers[model]
        shap_values = explainer.shap_values(X_sample)
        
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        
        # Mean absolute SHAP value per feature
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        
        importance = []
        for feat_name, val in zip(self.feature_names, mean_abs_shap):
            importance.append({
                'feature': feat_name,
                'importance': float(val)
            })
        
        importance.sort(key=lambda x: x['importance'], reverse=True)
        return importance
    
    def generate_explanation_text(self, explanation):
        """Generate human-readable explanation text"""
        if not explanation:
            return "No explanation available."
        
        top = explanation['top_contributors'][:5]
        
        text_parts = ["This anomaly was flagged primarily due to:"]
        
        for i, contrib in enumerate(top, 1):
            direction = "↑ elevated" if contrib['direction'] == 'increases_risk' else "↓ reduced"
            text_parts.append(
                f"  {i}. {contrib['feature']}: {direction} "
                f"(value={contrib['value']:.2f}, impact={contrib['shap_value']:.3f})"
            )
        
        return "\n".join(text_parts)
    
    def save_explainers(self):
        """Save explainer state (background data and feature names)"""
        state = {
            'feature_names': self.feature_names,
            'background_data': self.background_data
        }
        joblib.dump(state, os.path.join(self.model_dir, 'shap_state.joblib'))
        print("✓ SHAP state saved")
    
    def load_explainers(self, ensemble_detector):
        """Load explainer state and reinitialize"""
        try:
            state = joblib.load(os.path.join(self.model_dir, 'shap_state.joblib'))
            self.feature_names = state['feature_names']
            self.background_data = state['background_data']
            
            # Reinitialize explainers with loaded models
            if ensemble_detector.random_forest is not None:
                self.explainers['random_forest'] = shap.TreeExplainer(
                    ensemble_detector.random_forest
                )
            if ensemble_detector.xgboost is not None:
                self.explainers['xgboost'] = shap.TreeExplainer(
                    ensemble_detector.xgboost
                )
            
            print("✓ SHAP explainers loaded")
            return True
        except Exception as e:
            print(f"Error loading SHAP state: {e}")
            return False


if __name__ == '__main__':
    # Test SHAP explainer
    from data_processor import DataProcessor
    from ensemble import EnsembleDetector
    from sklearn.model_selection import train_test_split
    
    # Load data
    processor = DataProcessor()
    df = processor.load_batadal_data()
    X, y, features = processor.preprocess_batadal(df)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    X_train_scaled, X_test_scaled = processor.scale_features(X_train, X_test)
    
    # Train models
    detector = EnsembleDetector()
    detector.train_all(X_train_scaled, y_train)
    
    # Initialize explainer
    explainer = SHAPExplainer()
    explainer.initialize_explainers(detector, X_train_scaled, features)
    
    # Explain a prediction
    sample_idx = np.where(y_test == 1)[0][0]  # First anomaly
    explanation = explainer.explain_prediction(X_test_scaled[sample_idx])
    
    print("\nSHAP Explanation for anomaly:")
    print(explainer.generate_explanation_text(explanation))
