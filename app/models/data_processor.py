"""
SENTINEL-OT: Data Preprocessing Module
Handles loading and preprocessing of BATADAL and Windows datasets
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
import os

class DataProcessor:
    def __init__(self, data_path='files'):
        self.data_path = data_path
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_names = []
        
    def load_batadal_data(self):
        """Load and combine BATADAL datasets"""
        # Load training data (dataset03 - normal operations)
        df_train = pd.read_csv(os.path.join(self.data_path, 'BATADAL_dataset03.csv'))
        
        # Load test data with attacks (dataset04)
        df_test = pd.read_csv(os.path.join(self.data_path, 'BATADAL_dataset04.csv'))
        
        # Clean column names (remove leading spaces)
        df_train.columns = df_train.columns.str.strip()
        df_test.columns = df_test.columns.str.strip()
        
        # Standardize column names
        df_test.columns = df_train.columns
        
        # Combine datasets
        df_train['source'] = 'train'
        df_test['source'] = 'test'
        df = pd.concat([df_train, df_test], ignore_index=True)
        
        return df
    
    def load_windows_data(self):
        """Load Windows host-based dataset"""
        # Load Windows 10 data
        df_win10 = pd.read_csv(os.path.join(self.data_path, 'Train_Test_Windows_10.csv'))
        gt_win10 = pd.read_csv(os.path.join(self.data_path, 'GroundTruth_Windows10.csv'))
        
        # Load Windows 7 data
        df_win7 = pd.read_csv(os.path.join(self.data_path, 'Train_Test_Windows_7.csv'))
        gt_win7 = pd.read_csv(os.path.join(self.data_path, 'GroundTruth_Windows7.csv'))
        
        return {
            'win10': {'data': df_win10, 'ground_truth': gt_win10},
            'win7': {'data': df_win7, 'ground_truth': gt_win7}
        }
    
    def preprocess_batadal(self, df):
        """Preprocess BATADAL dataset"""
        # Drop datetime and source columns for modeling
        drop_cols = ['DATETIME', 'source']
        feature_cols = [c for c in df.columns if c not in drop_cols + ['ATT_FLAG']]
        
        # Handle missing/invalid attack flags (-999 means unlabeled)
        df['ATT_FLAG'] = df['ATT_FLAG'].replace(-999, 0)  # Treat unlabeled as normal for training
        
        # Store feature names
        self.feature_names = feature_cols
        
        # Extract features and labels
        X = df[feature_cols].values
        y = df['ATT_FLAG'].values
        
        # Handle NaN values
        X = np.nan_to_num(X, nan=0.0)
        
        return X, y, feature_cols
    
    def preprocess_windows(self, windows_data):
        """Preprocess Windows datasets"""
        results = {}
        
        for os_name, data in windows_data.items():
            df = data['data']
            gt = data['ground_truth']
            
            # Get timestamps from ground truth
            attack_timestamps = set(gt['ts'].values)
            
            # Create labels based on whether timestamp exists in ground truth
            # If data has 'ts' column, use it; otherwise create pseudo-labels
            if 'ts' in df.columns:
                df['label'] = df['ts'].apply(lambda x: 1 if x in attack_timestamps else 0)
            else:
                # Assume last N rows are test data with potential attacks
                df['label'] = 0
                # Mark based on ground truth length ratio
                attack_ratio = len(gt) / len(df)
                n_attacks = int(len(df) * attack_ratio)
                df.iloc[-n_attacks:, df.columns.get_loc('label')] = 1
            
            # Get numeric features only
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            feature_cols = [c for c in numeric_cols if c != 'label' and c != 'ts']
            
            X = df[feature_cols].values
            y = df['label'].values
            
            # Handle NaN/Inf values
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
            
            results[os_name] = {
                'X': X,
                'y': y,
                'features': feature_cols
            }
        
        return results
    
    def get_feature_groups(self):
        """Return feature groups for BATADAL dataset"""
        return {
            'tank_levels': [f'L_T{i}' for i in range(1, 8)],
            'pump_flows': [f'F_PU{i}' for i in range(1, 12)],
            'pump_status': [f'S_PU{i}' for i in range(1, 12)],
            'pressures': [c for c in self.feature_names if c.startswith('P_J')],
            'valve': ['F_V2', 'S_V2']
        }
    
    def scale_features(self, X_train, X_test=None):
        """Scale features using StandardScaler"""
        X_train_scaled = self.scaler.fit_transform(X_train)
        if X_test is not None:
            X_test_scaled = self.scaler.transform(X_test)
            return X_train_scaled, X_test_scaled
        return X_train_scaled


if __name__ == '__main__':
    # Test data loading
    processor = DataProcessor()
    df = processor.load_batadal_data()
    print(f"BATADAL data shape: {df.shape}")
    print(f"Attack distribution:\n{df['ATT_FLAG'].value_counts()}")
    
    X, y, features = processor.preprocess_batadal(df)
    print(f"\nFeatures shape: {X.shape}")
    print(f"Labels shape: {y.shape}")
    print(f"Attack ratio: {y.sum()/len(y):.2%}")
