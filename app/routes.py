"""
ConvergeShield: Flask Routes and API Endpoints
"""
import os
import sys
import json
import time
import random
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
import numpy as np
import pandas as pd
import joblib

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.ensemble import EnsembleDetector
from app.models.physics_validator import PhysicsValidator
from app.models.shap_explainer import SHAPExplainer
from app.models.ips_recommender import IPSRecommender
from app.models.data_processor import DataProcessor
from app.models.attack_simulator import AttackSimulator, NetworkTrafficGenerator, ZeekLogSimulator

main_bp = Blueprint('main', __name__)

# Global instances (initialized on first request)
detector = None
validator = None
explainer = None
recommender = None
scaler = None
feature_names = None
live_data = None
live_data_idx = 0
attack_simulator = None
traffic_generator = None
zeek_simulator = None


def init_models():
    """Initialize all models and components"""
    global detector, validator, explainer, recommender, scaler, feature_names, live_data
    global attack_simulator, traffic_generator, zeek_simulator
    
    model_dir = 'trained_models'
    
    if detector is None:
        print("Initializing ConvergeShield components...")
        
        # Load ensemble detector
        detector = EnsembleDetector(model_dir=model_dir)
        if not detector.load_models():
            print("Warning: Models not found. Please run train.py first.")
            return False
        
        # Load scaler and feature names
        scaler = joblib.load(os.path.join(model_dir, 'scaler.joblib'))
        feature_names = joblib.load(os.path.join(model_dir, 'feature_names.joblib'))
        
        # Initialize components
        validator = PhysicsValidator()
        explainer = SHAPExplainer(model_dir=model_dir)
        explainer.load_explainers(detector)
        recommender = IPSRecommender()
        
        # Load live data for simulation
        try:
            processor = DataProcessor(data_path='files')
            df = processor.load_batadal_data()
            X, y, _ = processor.preprocess_batadal(df)
            live_data = {'X': X, 'y': y}
            print(f"Live data loaded: {len(X)} samples")
            
            # Initialize attack simulator with baseline data
            attack_simulator = AttackSimulator(feature_names, X[y == 0])  # Normal data as baseline
            traffic_generator = NetworkTrafficGenerator()
            zeek_simulator = ZeekLogSimulator()
            print("✓ Attack simulator initialized")
            
        except Exception as e:
            print(f"Warning: Could not load live data: {e}")
            live_data = None
        
        print("✓ ConvergeShield initialized successfully")
        return True
    
    return True


# ==================== Page Routes ====================

@main_bp.route('/')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')


@main_bp.route('/incidents')
def incidents():
    """Incident explorer page"""
    return render_template('incidents.html')


@main_bp.route('/simulate')
def simulate():
    """Attack simulation page"""
    return render_template('simulate.html')


@main_bp.route('/analytics')
def analytics():
    """Analytics and explainability page"""
    return render_template('analytics.html')


# ==================== API Routes ====================

@main_bp.route('/api/status')
def api_status():
    """Check system status"""
    initialized = init_models()
    return jsonify({
        'status': 'ready' if initialized else 'not_initialized',
        'models_loaded': detector is not None,
        'timestamp': datetime.now().isoformat()
    })


@main_bp.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Predict anomaly for given features.
    Expects JSON with 'features' array.
    """
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features in request'}), 400
    
    try:
        # Get features
        features = np.array(data['features']).reshape(1, -1)
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Get ensemble prediction
        predictions, scores, individual_probas = detector.ensemble_predict(features_scaled)
        
        prediction = int(predictions[0])
        confidence = float(scores[0])
        
        # Physics validation
        physics_result = validator.validate_sample(features[0])
        
        # SHAP explanation (only for anomalies)
        shap_explanation = None
        if prediction == 1:
            shap_explanation = explainer.explain_prediction(features_scaled[0])
        
        # IPS recommendation
        ips_result = recommender.process_detection(
            sample_data=features[0],
            ml_prediction=prediction,
            ml_confidence=confidence,
            shap_explanation=shap_explanation,
            physics_result=physics_result
        )
        
        return jsonify({
            'prediction': prediction,
            'label': 'ANOMALY' if prediction == 1 else 'NORMAL',
            'confidence': confidence,
            'individual_scores': {
                'isolation_forest': float(individual_probas['isolation_forest'][0]),
                'random_forest': float(individual_probas['random_forest'][0]),
                'xgboost': float(individual_probas['xgboost'][0])
            },
            'physics_validation': physics_result,
            'shap_explanation': shap_explanation,
            'ips_recommendation': ips_result['recommendation'],
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/stream')
def api_stream():
    """
    Get next sample from live data stream.
    Simulates real-time packet capture.
    """
    global live_data_idx
    
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    if live_data is None:
        return jsonify({'error': 'Live data not loaded'}), 500
    
    try:
        # Get current sample
        idx = live_data_idx % len(live_data['X'])
        sample = live_data['X'][idx]
        true_label = int(live_data['y'][idx])
        
        # Increment index
        live_data_idx += 1
        
        # Scale features
        sample_scaled = scaler.transform(sample.reshape(1, -1))
        
        # Get prediction
        predictions, scores, individual_probas = detector.ensemble_predict(sample_scaled)
        prediction = int(predictions[0])
        confidence = float(scores[0])
        
        # Physics validation
        physics_result = validator.validate_sample(sample)
        
        # SHAP explanation for anomalies
        shap_explanation = None
        if prediction == 1:
            shap_explanation = explainer.explain_prediction(sample_scaled[0])
        
        # IPS recommendation
        ips_result = recommender.process_detection(
            sample_data=sample,
            ml_prediction=prediction,
            ml_confidence=confidence,
            shap_explanation=shap_explanation,
            physics_result=physics_result
        )
        
        # Build feature dict for display
        feature_values = {}
        for i, fname in enumerate(feature_names):
            if i < len(sample):
                feature_values[fname] = round(float(sample[i]), 3)
        
        return jsonify({
            'sample_id': idx,
            'features': feature_values,
            'prediction': prediction,
            'label': 'ANOMALY' if prediction == 1 else 'NORMAL',
            'true_label': true_label,
            'correct': prediction == true_label,
            'confidence': confidence,
            'individual_scores': {
                'isolation_forest': float(individual_probas['isolation_forest'][0]),
                'random_forest': float(individual_probas['random_forest'][0]),
                'xgboost': float(individual_probas['xgboost'][0])
            },
            'physics_valid': physics_result['is_valid'],
            'physics_violations': physics_result['violation_count'],
            'shap_top_features': shap_explanation['top_contributors'][:5] if shap_explanation else None,
            'ips_action': ips_result['action'],
            'ips_severity': ips_result['recommendation']['severity'] if ips_result['recommendation'] else 'none',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/metrics')
def api_metrics():
    """Get model performance metrics"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    try:
        # Load saved metrics
        model_dir = 'trained_models'
        config = joblib.load(os.path.join(model_dir, 'ensemble_config.joblib'))
        metrics = config.get('metrics', {})
        
        # Load feature importance
        importance = joblib.load(os.path.join(model_dir, 'feature_importance.joblib'))
        
        # Get top features
        avg_importance = importance.get('average', {})
        top_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)[:15]
        
        return jsonify({
            'model_metrics': metrics,
            'feature_importance': top_features,
            'model_weights': detector.weights,
            'ips_statistics': recommender.get_statistics()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/explain', methods=['POST'])
def api_explain():
    """Get detailed SHAP explanation for a sample"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    data = request.get_json()
    if not data or 'features' not in data:
        return jsonify({'error': 'Missing features'}), 400
    
    try:
        features = np.array(data['features']).reshape(1, -1)
        features_scaled = scaler.transform(features)
        
        # Get explanations from both models
        rf_explanation = explainer.explain_prediction(features_scaled[0], model='random_forest', top_k=15)
        xgb_explanation = explainer.explain_prediction(features_scaled[0], model='xgboost', top_k=15)
        
        # Generate text explanation
        text = explainer.generate_explanation_text(rf_explanation)
        
        return jsonify({
            'random_forest_shap': rf_explanation,
            'xgboost_shap': xgb_explanation,
            'explanation_text': text
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/ips/stats')
def api_ips_stats():
    """Get IPS statistics"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    return jsonify(recommender.get_statistics())


@main_bp.route('/api/ips/clear', methods=['POST'])
def api_ips_clear():
    """Clear IPS action log"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    recommender.clear_log()
    return jsonify({'status': 'cleared'})


# ==================== Attack Simulation API ====================

@main_bp.route('/api/attack/types')
def api_attack_types():
    """Get available attack types"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    return jsonify({
        'attack_types': attack_simulator.ATTACK_TYPES
    })


@main_bp.route('/api/attack/simulate', methods=['POST'])
def api_simulate_attack():
    """
    Simulate a specific attack and run it through the detection pipeline.
    """
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    data = request.get_json() or {}
    attack_type = data.get('attack_type', 'sensor_manipulation')
    intensity = float(data.get('intensity', 0.7))
    
    try:
        # Generate attack sample
        attack_record = attack_simulator.simulate_attack(attack_type, intensity)
        sample = attack_record['sample']
        
        # Scale and predict
        sample_scaled = scaler.transform(sample.reshape(1, -1))
        predictions, scores, individual_probas = detector.ensemble_predict(sample_scaled, threshold=0.35)
        
        prediction = int(predictions[0])
        confidence = float(scores[0])
        
        # Physics validation
        physics_result = validator.validate_sample(sample)
        
        # SHAP explanation
        shap_explanation = None
        if prediction == 1:
            shap_explanation = explainer.explain_prediction(sample_scaled[0])
        
        # IPS recommendation
        ips_result = recommender.process_detection(
            sample_data=sample,
            ml_prediction=prediction,
            ml_confidence=confidence,
            shap_explanation=shap_explanation,
            physics_result=physics_result
        )
        
        # Generate network traffic context
        traffic_packets = traffic_generator.generate_traffic_burst(5, 0.8 if attack_type != 'normal' else 0.0)
        zeek_log = zeek_simulator.generate_conn_log(attack_type != 'normal')
        zeek_notice = zeek_simulator.generate_notice_log(attack_type) if attack_type != 'normal' else None
        
        # Build feature dict
        feature_values = {}
        for i, fname in enumerate(feature_names):
            if i < len(sample):
                feature_values[fname] = round(float(sample[i]), 3)
        
        return jsonify({
            'attack_info': {
                'type': attack_type,
                'name': attack_record['attack_name'],
                'description': attack_record['description'],
                'mitre_id': attack_record['mitre_id'],
                'severity': attack_record['severity'],
                'intensity': intensity,
                'modified_features': attack_record['modified_features']
            },
            'detection': {
                'prediction': prediction,
                'label': 'ANOMALY DETECTED' if prediction == 1 else 'NOT DETECTED',
                'detected': prediction == 1,
                'confidence': confidence,
                'individual_scores': {
                    'isolation_forest': float(individual_probas['isolation_forest'][0]),
                    'random_forest': float(individual_probas['random_forest'][0]),
                    'xgboost': float(individual_probas['xgboost'][0])
                }
            },
            'physics_validation': physics_result,
            'shap_explanation': shap_explanation['top_contributors'][:5] if shap_explanation else None,
            'ips_response': ips_result,
            'network_context': {
                'packets': traffic_packets,
                'zeek_conn': zeek_log,
                'zeek_notice': zeek_notice
            },
            'features': feature_values,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/attack/sequence', methods=['POST'])
def api_attack_sequence():
    """Simulate a multi-stage attack sequence"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    data = request.get_json() or {}
    duration = int(data.get('duration', 10))
    
    try:
        sequence = attack_simulator.simulate_attack_sequence(duration)
        
        results = []
        detected_count = 0
        
        for attack in sequence:
            sample = attack['sample']
            sample_scaled = scaler.transform(sample.reshape(1, -1))
            predictions, scores, _ = detector.ensemble_predict(sample_scaled, threshold=0.35)
            
            detected = int(predictions[0]) == 1
            if detected:
                detected_count += 1
            
            results.append({
                'attack_type': attack['attack_type'],
                'detected': detected,
                'confidence': float(scores[0])
            })
        
        return jsonify({
            'total_attacks': len(sequence),
            'detected': detected_count,
            'detection_rate': detected_count / len(sequence) if sequence else 0,
            'sequence': results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@main_bp.route('/api/attack/stats')
def api_attack_stats():
    """Get attack simulation statistics"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    return jsonify(attack_simulator.get_attack_statistics())


@main_bp.route('/api/traffic/generate')
def api_generate_traffic():
    """Generate simulated network traffic"""
    if not init_models():
        return jsonify({'error': 'Models not initialized'}), 500
    
    count = int(request.args.get('count', 10))
    attack_ratio = float(request.args.get('attack_ratio', 0.0))
    
    packets = traffic_generator.generate_traffic_burst(count, attack_ratio)
    
    return jsonify({
        'packets': packets,
        'total': len(packets),
        'malicious': sum(1 for p in packets if p.get('threat_score', 0) > 0.5)
    })
