import requests
import json

# Test personalized recommendations
attack_types = [
    ('sensor_manipulation', 'Tank Attack'),
    ('actuator_manipulation', 'Pump Attack'), 
    ('command_injection', 'Critical Attack')
]

print('🔍 Testing Enhanced ConvergeShield System')
print('='*60)

for attack_type, name in attack_types:
    print(f'\n🎯 Testing: {name} ({attack_type})')
    print('-'*40)
    
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/attack/simulate/enhanced',
            json={'attack_type': attack_type, 'intensity': 0.85}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            attack_pattern = data.get('attack_info', {}).get('attack_pattern', 'Unknown')
            severity = data.get('attack_info', {}).get('severity_level', 'Unknown')
            
            print(f'✅ Attack Pattern: {attack_pattern}')
            print(f'⚡ Severity: {severity}')
            
            priority_actions = data.get('recommendations', {}).get('priority_actions', [])
            print(f'\n📊 Personalized Recommendations:')
            for i, action in enumerate(priority_actions[:3], 1):
                print(f'   {i}. {action}')
            
            safety_note = data.get('recommendations', {}).get('safety_note', '')
            print(f'\n⚠️ Safety Note: {safety_note[:80]}...')
            
        else:
            print(f'❌ Error: {response.status_code}')
            
    except Exception as e:
        print(f'❌ Exception: {e}')

print('\n' + '='*60)
print('✅ Enhanced system test completed!')