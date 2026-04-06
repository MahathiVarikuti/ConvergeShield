"""
ConvergeShield: Conpot/HoneyPot Integration Demo
This script demonstrates how to integrate with industrial protocol simulators
like Conpot for live attack simulation and detection.

For the hackathon demo, we use our built-in attack simulator since setting up
Conpot requires additional infrastructure (Docker, network config).

CONPOT SETUP (if you want to use real simulator):
1. Install: pip install conpot
2. Run: conpot --template default
3. This creates a simulated SCADA/ICS environment on local ports

Our ConvergeShield system can detect attacks in two ways:
1. Built-in Attack Simulator (what we demo) - Simulates SCADA sensor data attacks
2. Conpot Integration (production) - Real Modbus/S7comm/DNP3 traffic
"""

import sys
import time
import json
import random
import requests
from datetime import datetime

# ConvergeShield API base URL
API_BASE = "http://127.0.0.1:5000"


def simulate_attack_via_api(attack_type="sensor_manipulation", intensity=0.8):
    """Simulate an attack through ConvergeShield's API"""
    print(f"\n{'='*60}")
    print(f"SIMULATING ATTACK: {attack_type.upper()}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/attack/simulate",
            json={"attack_type": attack_type, "intensity": intensity},
            timeout=10
        )
        result = response.json()
        
        # Display results
        print(f"\n[ATTACK INFO]")
        print(f"  Type: {result['attack_info']['name']}")
        print(f"  MITRE ID: {result['attack_info']['mitre_id']}")
        print(f"  Severity: {result['attack_info']['severity']}")
        print(f"  Modified Features: {', '.join(result['attack_info']['modified_features'][:5])}")
        
        print(f"\n[DETECTION RESULT]")
        detected = result['detection']['detected']
        print(f"  Status: {'⚠️ DETECTED' if detected else '❌ NOT DETECTED'}")
        print(f"  Confidence: {result['detection']['confidence']*100:.1f}%")
        print(f"  Model Scores:")
        for model, score in result['detection']['individual_scores'].items():
            print(f"    - {model}: {score*100:.1f}%")
        
        print(f"\n[PHYSICS VALIDATION]")
        physics = result['physics_validation']
        print(f"  Valid: {'✓' if physics['is_valid'] else '✗'}")
        print(f"  Violations: {physics['violation_count']}")
        if physics['violations']:
            for v in physics['violations'][:3]:
                print(f"    - {v['rule']}: {v['severity']}")
        
        if result.get('shap_explanation'):
            print(f"\n[SHAP EXPLANATION]")
            for feat in result['shap_explanation'][:3]:
                direction = "↑" if feat['shap_value'] > 0 else "↓"
                print(f"  {feat['feature']}: {direction} {abs(feat['shap_value']):.3f}")
        
        if result['ips_response'].get('recommendation'):
            print(f"\n[IPS RECOMMENDATION]")
            print(f"  Action: {result['ips_response']['action']}")
            rec = result['ips_response']['recommendation']
            print(f"  {rec['attack_description']}")
            for r in rec['recommendations'][:2]:
                print(f"    → {r}")
        
        print(f"\n[NETWORK TRAFFIC]")
        for pkt in result['network_context']['packets'][:3]:
            threat = "🔴" if pkt['threat_score'] > 0.5 else "🟢"
            print(f"  {threat} {pkt['protocol']}: {pkt['src_ip']}:{pkt['src_port']} → {pkt['dst_ip']}:{pkt['dst_port']}")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def run_attack_sequence():
    """Simulate a multi-stage attack"""
    print("\n" + "="*60)
    print("MULTI-STAGE ATTACK SEQUENCE")
    print("="*60)
    print("\nSimulating realistic attack chain:")
    print("  1. Reconnaissance → 2. Probe → 3. Exploit → 4. Impact\n")
    
    try:
        response = requests.post(
            f"{API_BASE}/api/attack/sequence",
            json={"duration": 15},
            timeout=30
        )
        result = response.json()
        
        print(f"Total Attacks: {result['total_attacks']}")
        print(f"Detected: {result['detected']}")
        print(f"Detection Rate: {result['detection_rate']*100:.1f}%")
        
        print("\nTimeline:")
        for i, attack in enumerate(result['sequence'][:10]):
            status = "✓" if attack['detected'] else "✗"
            print(f"  {i+1}. {attack['attack_type']}: {status} ({attack['confidence']*100:.1f}%)")
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def demo_modbus_attack():
    """
    Demonstrates what a real Modbus attack looks like.
    In production, this would use pymodbus to send actual Modbus commands.
    """
    print("\n" + "="*60)
    print("MODBUS PROTOCOL ATTACK SIMULATION")
    print("="*60)
    print("""
    In a real deployment, we would use:
    
    from pymodbus.client import ModbusTcpClient
    client = ModbusTcpClient('192.168.1.100', port=502)
    
    # Read holding registers (normal operation)
    result = client.read_holding_registers(0, 10, unit=1)
    
    # Attack: Write malicious values to PLC
    client.write_register(1, 9999, unit=1)  # Invalid setpoint
    
    ConvergeShield would detect this as:
    - Abnormal register value
    - Physics violation (impossible setpoint)
    - SHAP: register_value as top contributor
    """)
    
    # Simulate via our API
    return simulate_attack_via_api("command_injection", 0.9)


def main():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  ConvergeShield - Attack Simulation Demo                      ║
    ║  Demonstrating IT-OT Security Monitoring                      ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    This demo shows how ConvergeShield detects various SCADA/ICS attacks.
    
    Available attack types:
    1. sensor_manipulation - False data injection
    2. actuator_manipulation - Unauthorized pump/valve control
    3. command_injection - Malicious PLC commands
    4. dos_flood - Network flooding
    5. man_in_middle - Traffic interception
    6. replay_attack - Replayed legitimate traffic
    7. reconnaissance - Network scanning
    """)
    
    # Check if server is running
    try:
        status = requests.get(f"{API_BASE}/api/status", timeout=5).json()
        if status['status'] != 'ready':
            print("❌ ConvergeShield server not ready. Run: python app.py")
            return
        print("✓ ConvergeShield server is ready\n")
    except:
        print("❌ Cannot connect to ConvergeShield. Make sure it's running: python app.py")
        return
    
    # Demo different attack types
    attack_types = [
        ("sensor_manipulation", 0.8),
        ("actuator_manipulation", 0.9),
        ("command_injection", 0.85),
        ("dos_flood", 0.7),
    ]
    
    for attack_type, intensity in attack_types:
        simulate_attack_via_api(attack_type, intensity)
        time.sleep(1)
    
    # Run attack sequence
    run_attack_sequence()
    
    # Modbus demo
    demo_modbus_attack()
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nTo see live detection, open: http://127.0.0.1:5000/simulate")
    print("To see analytics: http://127.0.0.1:5000/analytics")


if __name__ == "__main__":
    main()
