"""
ConvergeShield: Model Training Script
Trains all ML models and saves them for production use
"""
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
import joblib

from app.models.data_processor import DataProcessor
from app.models.ensemble import EnsembleDetector
from app.models.shap_explainer import SHAPExplainer
from app.models.physics_validator import PhysicsValidator


def train_models():
    print("="*60)
    print("ConvergeShield: AI-Assisted IT-OT Security Monitoring System")
    print("Model Training Pipeline (Optimized for Recall)")
    print("="*60)
    
    # Initialize components
    processor = DataProcessor(data_path='files')
    detector = EnsembleDetector(model_dir='trained_models')
    
    # ==================== BATADAL Dataset ====================
    print("\n[1/6] Loading BATADAL dataset...")
    df_batadal = processor.load_batadal_data()
    X_batadal, y_batadal, features_batadal = processor.preprocess_batadal(df_batadal)
    
    print(f"  Shape: {X_batadal.shape}")
    print(f"  Normal samples: {(y_batadal == 0).sum()}")
    print(f"  Attack samples: {(y_batadal == 1).sum()}")
    print(f"  Attack ratio: {y_batadal.mean():.2%}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_batadal, y_batadal, test_size=0.3, random_state=42, stratify=y_batadal
    )
    
    # Scale features
    print("\n[2/6] Scaling features...")
    X_train_scaled, X_test_scaled = processor.scale_features(X_train, X_test)
    
    # Apply SMOTE to balance the training data
    print("\n[3/6] Applying SMOTE oversampling...")
    print(f"  Before SMOTE: {(y_train == 0).sum()} normal, {(y_train == 1).sum()} attacks")
    
    smote = SMOTE(sampling_strategy=0.5, random_state=42)  # 50% minority ratio
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_scaled, y_train)
    
    print(f"  After SMOTE:  {(y_train_resampled == 0).sum()} normal, {(y_train_resampled == 1).sum()} attacks")
    
    # Save scaler for inference
    joblib.dump(processor.scaler, 'trained_models/scaler.joblib')
    joblib.dump(features_batadal, 'trained_models/feature_names.joblib')
    print("  ✓ Scaler and feature names saved")
    
    # ==================== Train Models ====================
    print("\n[4/6] Training ML models (optimized for recall)...")
    detector.train_all(X_train_resampled, y_train_resampled)
    
    # ==================== Evaluate Models ====================
    print("\n[5/6] Evaluating models...")
    # Use lower threshold (0.35) for better recall
    results = detector.evaluate(X_test_scaled, y_test, threshold=0.35)
    
    print("\n" + "="*60)
    print("MODEL EVALUATION RESULTS")
    print("="*60)
    
    for model, metrics in results.items():
        print(f"\n{model.upper()}:")
        print(f"  Accuracy:  {metrics['accuracy']:.4f}")
        print(f"  Precision: {metrics['precision']:.4f}")
        print(f"  Recall:    {metrics['recall']:.4f}")
        print(f"  F1 Score:  {metrics['f1']:.4f}")
        if 'auc' in metrics:
            print(f"  AUC-ROC:   {metrics['auc']:.4f}")
        print(f"  Confusion Matrix: {metrics['confusion_matrix']}")
    
    # Feature importance
    importance = detector.get_feature_importance(features_batadal)
    print("\nTop 10 Important Features (Average):")
    sorted_imp = sorted(importance['average'].items(), key=lambda x: x[1], reverse=True)[:10]
    for feat, imp in sorted_imp:
        print(f"  {feat}: {imp:.4f}")
    
    # Save feature importance
    joblib.dump(importance, 'trained_models/feature_importance.joblib')
    
    # ==================== SHAP Explainer ====================
    print("\n[6/6] Initializing SHAP explainers...")
    explainer = SHAPExplainer(model_dir='trained_models')
    explainer.initialize_explainers(detector, X_train_resampled, features_batadal)
    
    # Test explanation
    anomaly_idx = np.where(y_test == 1)[0][0]
    explanation = explainer.explain_prediction(X_test_scaled[anomaly_idx])
    print("\nSample SHAP explanation for an anomaly:")
    print(explainer.generate_explanation_text(explanation))
    
    # Save everything
    explainer.save_explainers()
    detector.save_models()
    
    # ==================== Physics Validator Test ====================
    print("\n[Bonus] Testing Physics Validator...")
    validator = PhysicsValidator()
    
    # Test on a few samples
    n_violations = 0
    for i in range(min(100, len(X_test))):
        result = validator.validate_sample(X_test[i])
        if not result['is_valid']:
            n_violations += 1
    
    print(f"  Physics violations in test set: {n_violations}/100 samples")
    
    # ==================== Summary ====================
    print("\n" + "="*60)
    print("TRAINING COMPLETE!")
    print("="*60)
    print(f"\nModels saved to: trained_models/")
    print(f"  - isolation_forest.joblib")
    print(f"  - random_forest.joblib")
    print(f"  - xgboost.joblib")
    print(f"  - ensemble_config.joblib")
    print(f"  - scaler.joblib")
    print(f"  - feature_names.joblib")
    print(f"  - shap_state.joblib")
    
    # Print benchmark comparison
    print("\n" + "="*60)
    print("BENCHMARK COMPARISON (vs Reference Paper)")
    print("="*60)
    print(f"\n{'Model':<20} {'Paper':<15} {'SENTINEL-OT':<15}")
    print("-"*50)
    print(f"{'OCSVM (F1)':<20} {'0.91':<15} {'N/A':<15}")
    print(f"{'IF (F1)':<20} {'0.13':<15} {results['isolation_forest']['f1']:.2f}")
    print(f"{'Ensemble (F1)':<20} {'0.20 (CSAD)':<15} {results['ensemble']['f1']:.2f}")
    print(f"{'RF (F1)':<20} {'N/A':<15} {results['random_forest']['f1']:.2f}")
    print(f"{'XGBoost (F1)':<20} {'N/A':<15} {results['xgboost']['f1']:.2f}")
    
    return results


if __name__ == '__main__':
    results = train_models()
