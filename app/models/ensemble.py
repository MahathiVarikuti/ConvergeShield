"""
SENTINEL-OT: Ensemble Anomaly Detection System
Combines Isolation Forest, Random Forest, and XGBoost with weighted voting
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report, roc_auc_score
)
import xgboost as xgb
import joblib
import os


class EnsembleDetector:
    def __init__(self, model_dir='trained_models'):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize models
        self.isolation_forest = None
        self.random_forest = None
        self.xgboost = None
        
        # Model weights for ensemble (tuned based on performance)
        self.weights = {
            'isolation_forest': 0.25,
            'random_forest': 0.40,
            'xgboost': 0.35
        }
        
        # Performance metrics storage
        self.metrics = {}
        
    def train_isolation_forest(self, X_train, contamination=0.15):
        """Train Isolation Forest for unsupervised anomaly detection"""
        print("Training Isolation Forest...")
        self.isolation_forest = IsolationForest(
            n_estimators=150,
            contamination=contamination,  # Higher contamination for better recall
            max_samples='auto',
            random_state=42,
            n_jobs=-1
        )
        self.isolation_forest.fit(X_train)
        print("✓ Isolation Forest trained")
        return self.isolation_forest
    
    def train_random_forest(self, X_train, y_train):
        """Train Random Forest classifier"""
        print("Training Random Forest...")
        self.random_forest = RandomForestClassifier(
            n_estimators=150,
            max_depth=20,
            min_samples_split=3,
            min_samples_leaf=1,
            class_weight={0: 1, 1: 5},  # Higher weight for attacks
            random_state=42,
            n_jobs=-1
        )
        self.random_forest.fit(X_train, y_train)
        print("✓ Random Forest trained")
        return self.random_forest
    
    def train_xgboost(self, X_train, y_train):
        """Train XGBoost classifier"""
        print("Training XGBoost...")
        
        # Higher scale_pos_weight for better recall on minority class
        scale_pos_weight = max((y_train == 0).sum() / max((y_train == 1).sum(), 1), 3)
        
        self.xgboost = xgb.XGBClassifier(
            n_estimators=150,
            max_depth=10,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            use_label_encoder=False,
            eval_metric='aucpr',  # AUC-PR is better for imbalanced data
            random_state=42,
            n_jobs=-1
        )
        self.xgboost.fit(X_train, y_train)
        print("✓ XGBoost trained")
        return self.xgboost
    
    def train_all(self, X_train, y_train, contamination=None):
        """Train all three models"""
        # Auto-calculate contamination from labels if not provided
        if contamination is None:
            contamination = min(y_train.mean() + 0.05, 0.5)  # Add small buffer
        
        self.train_isolation_forest(X_train, contamination)
        self.train_random_forest(X_train, y_train)
        self.train_xgboost(X_train, y_train)
        
        print("\n✓ All models trained successfully!")
        
    def predict_isolation_forest(self, X):
        """Get predictions from Isolation Forest (-1=anomaly, 1=normal)"""
        if self.isolation_forest is None:
            raise ValueError("Isolation Forest not trained")
        preds = self.isolation_forest.predict(X)
        # Convert: -1 (anomaly) -> 1, 1 (normal) -> 0
        return (preds == -1).astype(int)
    
    def predict_random_forest(self, X):
        """Get predictions from Random Forest"""
        if self.random_forest is None:
            raise ValueError("Random Forest not trained")
        return self.random_forest.predict(X)
    
    def predict_xgboost(self, X):
        """Get predictions from XGBoost"""
        if self.xgboost is None:
            raise ValueError("XGBoost not trained")
        return self.xgboost.predict(X)
    
    def predict_proba_all(self, X):
        """Get probability scores from all models"""
        probas = {}
        
        # Isolation Forest: use decision function (more negative = more anomalous)
        if_scores = -self.isolation_forest.decision_function(X)
        # Normalize to 0-1
        if_scores = (if_scores - if_scores.min()) / (if_scores.max() - if_scores.min() + 1e-10)
        probas['isolation_forest'] = if_scores
        
        # Random Forest: use predict_proba
        rf_proba = self.random_forest.predict_proba(X)[:, 1]
        probas['random_forest'] = rf_proba
        
        # XGBoost: use predict_proba
        xgb_proba = self.xgboost.predict_proba(X)[:, 1]
        probas['xgboost'] = xgb_proba
        
        return probas
    
    def ensemble_predict(self, X, threshold=0.5):
        """Weighted ensemble prediction"""
        probas = self.predict_proba_all(X)
        
        # Weighted average
        ensemble_score = (
            self.weights['isolation_forest'] * probas['isolation_forest'] +
            self.weights['random_forest'] * probas['random_forest'] +
            self.weights['xgboost'] * probas['xgboost']
        )
        
        # Apply threshold
        predictions = (ensemble_score >= threshold).astype(int)
        
        return predictions, ensemble_score, probas
    
    def evaluate(self, X_test, y_test, threshold=0.5):
        """Evaluate all models and ensemble"""
        results = {}
        
        # Individual models
        models = {
            'isolation_forest': self.predict_isolation_forest(X_test),
            'random_forest': self.predict_random_forest(X_test),
            'xgboost': self.predict_xgboost(X_test)
        }
        
        # Ensemble
        ensemble_preds, ensemble_scores, _ = self.ensemble_predict(X_test, threshold)
        models['ensemble'] = ensemble_preds
        
        for name, preds in models.items():
            results[name] = {
                'accuracy': accuracy_score(y_test, preds),
                'precision': precision_score(y_test, preds, zero_division=0),
                'recall': recall_score(y_test, preds, zero_division=0),
                'f1': f1_score(y_test, preds, zero_division=0),
                'confusion_matrix': confusion_matrix(y_test, preds).tolist()
            }
            
            # Add AUC for ensemble
            if name == 'ensemble':
                try:
                    results[name]['auc'] = roc_auc_score(y_test, ensemble_scores)
                except:
                    results[name]['auc'] = 0.0
        
        self.metrics = results
        return results
    
    def get_feature_importance(self, feature_names):
        """Get feature importance from Random Forest and XGBoost"""
        importance = {}
        
        if self.random_forest is not None:
            rf_imp = self.random_forest.feature_importances_
            importance['random_forest'] = dict(zip(feature_names, rf_imp))
        
        if self.xgboost is not None:
            xgb_imp = self.xgboost.feature_importances_
            importance['xgboost'] = dict(zip(feature_names, xgb_imp))
        
        # Average importance
        if importance:
            avg_imp = {}
            for feat in feature_names:
                vals = [importance[m].get(feat, 0) for m in importance]
                avg_imp[feat] = np.mean(vals)
            importance['average'] = avg_imp
        
        return importance
    
    def save_models(self):
        """Save all trained models"""
        if self.isolation_forest:
            joblib.dump(self.isolation_forest, 
                       os.path.join(self.model_dir, 'isolation_forest.joblib'))
        if self.random_forest:
            joblib.dump(self.random_forest, 
                       os.path.join(self.model_dir, 'random_forest.joblib'))
        if self.xgboost:
            joblib.dump(self.xgboost, 
                       os.path.join(self.model_dir, 'xgboost.joblib'))
        
        # Save weights and metrics
        joblib.dump({
            'weights': self.weights,
            'metrics': self.metrics
        }, os.path.join(self.model_dir, 'ensemble_config.joblib'))
        
        print(f"✓ Models saved to {self.model_dir}/")
    
    def load_models(self):
        """Load all trained models"""
        try:
            self.isolation_forest = joblib.load(
                os.path.join(self.model_dir, 'isolation_forest.joblib'))
            self.random_forest = joblib.load(
                os.path.join(self.model_dir, 'random_forest.joblib'))
            self.xgboost = joblib.load(
                os.path.join(self.model_dir, 'xgboost.joblib'))
            
            config = joblib.load(os.path.join(self.model_dir, 'ensemble_config.joblib'))
            self.weights = config.get('weights', self.weights)
            self.metrics = config.get('metrics', {})
            
            print("✓ Models loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading models: {e}")
            return False


if __name__ == '__main__':
    # Test the ensemble
    from data_processor import DataProcessor
    
    processor = DataProcessor()
    df = processor.load_batadal_data()
    X, y, features = processor.preprocess_batadal(df)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Scale features
    X_train_scaled, X_test_scaled = processor.scale_features(X_train, X_test)
    
    # Train ensemble
    detector = EnsembleDetector()
    detector.train_all(X_train_scaled, y_train)
    
    # Evaluate
    results = detector.evaluate(X_test_scaled, y_test)
    
    print("\n" + "="*50)
    print("MODEL EVALUATION RESULTS")
    print("="*50)
    for model, metrics in results.items():
        print(f"\n{model.upper()}:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1']:.4f}")
    
    # Save models
    detector.save_models()
