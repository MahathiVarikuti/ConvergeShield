"""
ConvergeShield: Attack Simulator Module
Simulates various SCADA/ICS attacks for demonstration and testing
"""
import numpy as np
import random
from datetime import datetime
from typing import Dict, List, Tuple


class AttackSimulator:
    """
    Simulates various types of SCADA/ICS attacks.
    Used for demonstration when real attack tools (Conpot, OpenPLC) aren't available.
    """
    
    # Attack type definitions with MITRE ATT&CK ICS mapping
    ATTACK_TYPES = {
        'normal': {
            'name': 'Normal Traffic',
            'description': 'Legitimate SCADA operations',
            'mitre_id': None,
            'severity': 'none'
        },
        'dos_flood': {
            'name': 'DoS Flood Attack',
            'description': 'Denial of Service - overwhelming network with packets',
            'mitre_id': 'T0814',
            'severity': 'high',
            'affected_features': ['F_PU*', 'P_J*']
        },
        'sensor_manipulation': {
            'name': 'Sensor Manipulation',
            'description': 'False data injection into sensor readings',
            'mitre_id': 'T0832',
            'severity': 'critical',
            'affected_features': ['L_T*', 'P_J*']
        },
        'actuator_manipulation': {
            'name': 'Actuator Manipulation', 
            'description': 'Unauthorized control of pumps/valves',
            'mitre_id': 'T0855',
            'severity': 'critical',
            'affected_features': ['S_PU*', 'F_PU*', 'S_V2']
        },
        'replay_attack': {
            'name': 'Replay Attack',
            'description': 'Replaying captured legitimate traffic',
            'mitre_id': 'T0843',
            'severity': 'medium',
            'affected_features': ['*']
        },
        'man_in_middle': {
            'name': 'Man-in-the-Middle',
            'description': 'Intercepting and modifying SCADA communications',
            'mitre_id': 'T0830',
            'severity': 'critical',
            'affected_features': ['L_T*', 'F_PU*', 'P_J*']
        },
        'reconnaissance': {
            'name': 'Network Reconnaissance',
            'description': 'Scanning and probing SCADA network',
            'mitre_id': 'T0846',
            'severity': 'low',
            'affected_features': []
        },
        'command_injection': {
            'name': 'Command Injection',
            'description': 'Injecting malicious commands to PLCs',
            'mitre_id': 'T0821',
            'severity': 'critical',
            'affected_features': ['S_PU*', 'S_V2']
        }
    }
    
    def __init__(self, feature_names: List[str], baseline_data: np.ndarray = None):
        """
        Initialize attack simulator.
        
        Args:
            feature_names: List of feature names from the dataset
            baseline_data: Normal traffic data to base attacks on
        """
        self.feature_names = feature_names
        self.baseline_data = baseline_data
        self.attack_history = []
        
        # Feature indices by category
        self.tank_indices = [i for i, f in enumerate(feature_names) if f.startswith('L_T')]
        self.pump_flow_indices = [i for i, f in enumerate(feature_names) if f.startswith('F_PU')]
        self.pump_status_indices = [i for i, f in enumerate(feature_names) if f.startswith('S_PU')]
        self.pressure_indices = [i for i, f in enumerate(feature_names) if f.startswith('P_J')]
        self.valve_indices = [i for i, f in enumerate(feature_names) if f.startswith('F_V') or f.startswith('S_V')]
    
    def get_baseline_sample(self) -> np.ndarray:
        """Get a random baseline (normal) sample"""
        if self.baseline_data is not None:
            idx = random.randint(0, len(self.baseline_data) - 1)
            return self.baseline_data[idx].copy()
        else:
            # Generate synthetic normal sample
            sample = np.zeros(len(self.feature_names))
            for i in self.tank_indices:
                sample[i] = random.uniform(2, 6)  # Normal tank levels
            for i in self.pump_flow_indices:
                sample[i] = random.uniform(0, 100)
            for i in self.pump_status_indices:
                sample[i] = random.choice([0, 1])
            for i in self.pressure_indices:
                sample[i] = random.uniform(20, 90)
            return sample
    
    def simulate_attack(self, attack_type: str, intensity: float = 0.5) -> Dict:
        """
        Simulate a specific attack type.
        
        Args:
            attack_type: Type of attack from ATTACK_TYPES
            intensity: Attack intensity from 0.0 to 1.0
            
        Returns:
            Dict with attack details and modified sample
        """
        if attack_type not in self.ATTACK_TYPES:
            attack_type = 'normal'
        
        # Get baseline sample
        sample = self.get_baseline_sample()
        original_sample = sample.copy()
        
        attack_info = self.ATTACK_TYPES[attack_type].copy()
        modifications = []
        
        if attack_type == 'normal':
            # No modifications for normal traffic
            pass
            
        elif attack_type == 'dos_flood':
            # DoS: Erratic readings due to network congestion
            for i in self.pump_flow_indices[:3]:
                noise = random.uniform(-50, 50) * intensity
                sample[i] = max(0, sample[i] + noise)
                modifications.append(self.feature_names[i])
            for i in self.pressure_indices[:3]:
                noise = random.uniform(-20, 20) * intensity
                sample[i] = max(0, sample[i] + noise)
                modifications.append(self.feature_names[i])
                
        elif attack_type == 'sensor_manipulation':
            # False data injection on sensors
            # Tank levels manipulated
            for i in self.tank_indices:
                if random.random() < intensity:
                    # Inject false reading
                    sample[i] = random.uniform(-2, 15)  # Out of normal bounds
                    modifications.append(self.feature_names[i])
            # Pressure sensors
            for i in self.pressure_indices[:4]:
                if random.random() < intensity:
                    sample[i] = sample[i] * (1 + random.uniform(0.5, 2) * intensity)
                    modifications.append(self.feature_names[i])
                    
        elif attack_type == 'actuator_manipulation':
            # Unauthorized pump/valve control
            # Turn pumps on/off unexpectedly
            for i, flow_i in enumerate(self.pump_flow_indices[:5]):
                status_i = self.pump_status_indices[i] if i < len(self.pump_status_indices) else None
                if random.random() < intensity:
                    if status_i:
                        # Inconsistent state: pump OFF but flow detected
                        sample[status_i] = 0
                        sample[flow_i] = random.uniform(30, 80)  # Flow without pump!
                        modifications.append(self.feature_names[flow_i])
                        modifications.append(self.feature_names[status_i])
                        
        elif attack_type == 'replay_attack':
            # Replay old data - values don't change naturally
            # Make multiple readings identical (suspicious)
            for i in self.tank_indices:
                sample[i] = round(sample[i], 0)  # Suspiciously round numbers
                modifications.append(self.feature_names[i])
                
        elif attack_type == 'man_in_middle':
            # MITM: Subtle modifications to intercepted traffic
            # Small but consistent bias
            bias = 0.1 * intensity
            for i in self.tank_indices:
                sample[i] *= (1 + bias)
                modifications.append(self.feature_names[i])
            for i in self.pump_flow_indices:
                sample[i] *= (1 - bias)
                modifications.append(self.feature_names[i])
                
        elif attack_type == 'reconnaissance':
            # Recon doesn't modify data, but we can simulate probe patterns
            # Just return normal data with recon flag
            pass
            
        elif attack_type == 'command_injection':
            # Malicious commands to PLCs
            # All pumps suddenly change state
            for i in self.pump_status_indices:
                sample[i] = 1 - sample[i]  # Toggle all pumps
                modifications.append(self.feature_names[i])
            # Valve manipulation
            for i in self.valve_indices:
                if 'S_V' in self.feature_names[i]:
                    sample[i] = 1 - sample[i]
                    modifications.append(self.feature_names[i])
        
        # Record attack
        attack_record = {
            'timestamp': datetime.now().isoformat(),
            'attack_type': attack_type,
            'attack_name': attack_info['name'],
            'description': attack_info['description'],
            'mitre_id': attack_info.get('mitre_id'),
            'severity': attack_info['severity'],
            'intensity': intensity,
            'modified_features': list(set(modifications)),
            'sample': sample,
            'original_sample': original_sample,
            'is_attack': attack_type != 'normal'
        }
        
        self.attack_history.append(attack_record)
        
        return attack_record
    
    def simulate_attack_sequence(self, duration_seconds: int = 60) -> List[Dict]:
        """
        Simulate a realistic attack sequence (recon -> exploit -> persist).
        
        Args:
            duration_seconds: Duration of the attack sequence
            
        Returns:
            List of attack records
        """
        sequence = []
        
        # Phase 1: Reconnaissance (10%)
        for _ in range(max(1, duration_seconds // 10)):
            sequence.append(self.simulate_attack('reconnaissance', 0.3))
        
        # Phase 2: Initial Access - probe sensors (20%)
        for _ in range(duration_seconds // 5):
            sequence.append(self.simulate_attack('sensor_manipulation', 0.2))
        
        # Phase 3: Escalation - actuator manipulation (40%)
        for _ in range(2 * duration_seconds // 5):
            attack_type = random.choice(['actuator_manipulation', 'command_injection'])
            sequence.append(self.simulate_attack(attack_type, 0.7))
        
        # Phase 4: Impact - full attack (30%)
        for _ in range(3 * duration_seconds // 10):
            attack_type = random.choice(['sensor_manipulation', 'actuator_manipulation', 'man_in_middle'])
            sequence.append(self.simulate_attack(attack_type, 0.9))
        
        return sequence
    
    def get_attack_statistics(self) -> Dict:
        """Get statistics about simulated attacks"""
        if not self.attack_history:
            return {'total': 0, 'by_type': {}, 'by_severity': {}}
        
        by_type = {}
        by_severity = {}
        
        for attack in self.attack_history:
            atype = attack['attack_type']
            sev = attack['severity']
            
            by_type[atype] = by_type.get(atype, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        return {
            'total': len(self.attack_history),
            'by_type': by_type,
            'by_severity': by_severity,
            'recent': self.attack_history[-10:]
        }
    
    def clear_history(self):
        """Clear attack history"""
        self.attack_history = []


class NetworkTrafficGenerator:
    """
    Generates simulated network traffic patterns for SCADA/Modbus protocols.
    Mimics what tools like Zeek would capture.
    """
    
    PROTOCOLS = {
        'modbus': {'port': 502, 'name': 'Modbus TCP'},
        'dnp3': {'port': 20000, 'name': 'DNP3'},
        's7comm': {'port': 102, 'name': 'Siemens S7'},
        'opcua': {'port': 4840, 'name': 'OPC-UA'},
        'mqtt': {'port': 1883, 'name': 'MQTT'}
    }
    
    def __init__(self):
        self.packet_counter = 0
        self.connections = []
    
    def generate_packet(self, protocol: str = 'modbus', is_malicious: bool = False) -> Dict:
        """Generate a simulated network packet"""
        self.packet_counter += 1
        
        proto_info = self.PROTOCOLS.get(protocol, self.PROTOCOLS['modbus'])
        
        packet = {
            'id': self.packet_counter,
            'timestamp': datetime.now().isoformat(),
            'protocol': proto_info['name'],
            'src_ip': f"192.168.1.{random.randint(1, 50)}",
            'dst_ip': f"192.168.1.{random.randint(100, 150)}",
            'src_port': random.randint(1024, 65535),
            'dst_port': proto_info['port'],
            'length': random.randint(64, 1500),
            'flags': 'PSH,ACK' if not is_malicious else 'SYN,FIN',
        }
        
        if protocol == 'modbus':
            packet['modbus_function'] = random.choice([
                'Read Coils (0x01)',
                'Read Holding Registers (0x03)',
                'Write Single Coil (0x05)',
                'Write Multiple Registers (0x10)'
            ]) if not is_malicious else 'Illegal Function (0x80)'
            packet['unit_id'] = random.randint(1, 10)
        
        if is_malicious:
            packet['alert'] = 'Suspicious traffic pattern detected'
            packet['threat_score'] = random.uniform(0.7, 1.0)
        else:
            packet['threat_score'] = random.uniform(0.0, 0.2)
        
        return packet
    
    def generate_traffic_burst(self, count: int = 10, attack_ratio: float = 0.0) -> List[Dict]:
        """Generate a burst of network packets"""
        packets = []
        for _ in range(count):
            is_attack = random.random() < attack_ratio
            protocol = random.choice(list(self.PROTOCOLS.keys()))
            packets.append(self.generate_packet(protocol, is_attack))
        return packets


# Zeek-style log generator
class ZeekLogSimulator:
    """
    Simulates Zeek (Bro) network security monitor logs.
    """
    
    def __init__(self):
        self.uid_counter = 0
    
    def generate_conn_log(self, is_attack: bool = False) -> Dict:
        """Generate Zeek conn.log entry"""
        self.uid_counter += 1
        
        return {
            'ts': datetime.now().timestamp(),
            'uid': f"C{self.uid_counter:08d}",
            'id.orig_h': f"192.168.1.{random.randint(1, 50)}",
            'id.orig_p': random.randint(1024, 65535),
            'id.resp_h': f"192.168.1.{random.randint(100, 150)}",
            'id.resp_p': 502,  # Modbus
            'proto': 'tcp',
            'service': 'modbus',
            'duration': random.uniform(0.001, 5.0),
            'orig_bytes': random.randint(100, 10000),
            'resp_bytes': random.randint(100, 10000),
            'conn_state': 'SF' if not is_attack else 'REJ',
            'missed_bytes': 0 if not is_attack else random.randint(100, 1000),
            'history': 'ShADadFf' if not is_attack else 'S',
            'orig_pkts': random.randint(5, 100),
            'resp_pkts': random.randint(5, 100),
        }
    
    def generate_notice_log(self, attack_type: str) -> Dict:
        """Generate Zeek notice.log entry for detected threats"""
        notices = {
            'dos_flood': 'Scan::Port_Scan',
            'sensor_manipulation': 'Modbus::Invalid_Data',
            'actuator_manipulation': 'Modbus::Unauthorized_Write',
            'command_injection': 'Modbus::Illegal_Function',
            'reconnaissance': 'Scan::Address_Scan',
            'man_in_middle': 'SSL::Invalid_Server_Cert'
        }
        
        return {
            'ts': datetime.now().timestamp(),
            'note': notices.get(attack_type, 'SCADA::Anomaly'),
            'msg': f"Potential {attack_type.replace('_', ' ')} detected",
            'src': f"192.168.1.{random.randint(1, 50)}",
            'dst': f"192.168.1.{random.randint(100, 150)}",
            'p': 502,
            'actions': ['Notice::ACTION_LOG', 'Notice::ACTION_ALARM'],
            'suppress_for': 3600.0
        }
