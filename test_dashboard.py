"""
Quick test of the enhanced dashboard API
"""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_enhanced_simulation():
    """Test the enhanced attack simulation endpoint"""
    
    attack_types = [
        ('sensor_manipulation', 'Tank Attack'),
        ('actuator_manipulation', 'Pump Attack'),
        ('command_injection', 'Critical Attack')
    ]
    
    for attack_type, name in attack_types:
        print(f"\n{'='*60}")
        print(f"Testing: {name} ({attack_type})")
        print('='*60)
        
        response = requests.post(
            f"{BASE_URL}/api/attack/simulate/enhanced",
            json={
                'attack_type': attack_type,
                'intensity': 0.85
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n✅ DETECTION SUCCESSFUL")
            print(f"   Severity: {data['attack_info']['severity_level']}")
            print(f"   Pattern: {data['attack_info']['attack_pattern']}")
            print(f"   Confidence: {data['detection']['confidence_percent']}%")
            
            print(f"\n📊 HUMAN-READABLE EXPLANATIONS:")
            for i, reason in enumerate(data['explanations']['reasons'][:3], 1):
                print(f"   {i}. {reason}")
            
            print(f"\n🔧 SAFE RECOMMENDATIONS:")
            for i, action in enumerate(data['recommendations']['simple_actions'][:4], 1):
                print(f"   {i}. {action}")
            
            print(f"\n⚠️  {data['recommendations']['safety_note']}")
            
        else:
            print(f"❌ ERROR: {response.status_code}")
            print(response.text)

if __name__ == '__main__':
    print("ConvergeShield - Enhanced Dashboard API Test")
    print("="*60)
    
    # Wait for server to be ready
    import time
    print("\nWaiting for server to start...")
    time.sleep(2)
    
    try:
        test_enhanced_simulation()
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("Dashboard: http://127.0.0.1:5000/")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the Flask server is running (python app.py)")
