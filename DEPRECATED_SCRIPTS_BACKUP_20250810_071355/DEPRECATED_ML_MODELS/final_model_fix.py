import pandas as pd
import os
import glob
import numpy as np
from datetime import datetime
import joblib
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("FINAL MODEL FIX - COMPREHENSIVE SOLUTION")
print("=" * 60)

# Paths
data_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data"
scripts_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

# 1. Load the original FD features
print("\n1. Loading original FD features...")
fd_features = pd.read_csv(os.path.join(data_dir, "fd_hitter_features_final.csv"))
print(f"Original FD features shape: {fd_features.shape}")
print(f"Original FD columns: {list(fd_features.columns)}")

# 2. Load the training data template to see what features we actually need
print("\n2. Loading training data to identify required features...")
training_files = glob.glob(os.path.join(data_dir, "*game_logs*.csv"))
if training_files:
    training_data = pd.read_csv(training_files[0])
    print(f"Training data shape: {training_data.shape}")
    print(f"Training columns: {list(training_data.columns)}")
    
    # Get the feature columns used in training (excluding target columns)
    target_columns = ['1B', '2B', '3B', 'HR', 'SO', 'BB', 'GB', 'FB', 'LD', 'IFFB', 'FIP', 
                     'hits', 'total_bases', 'runs', 'rbi', 'home_runs', 'hrr', 'stolen_bases', 
                     'hr_binary', 'strikeouts', 'outs', 'win_binary']
    
    feature_columns = [col for col in training_data.columns if col not in target_columns and 
                      col not in ['player_id', 'game_id', 'date', 'team', 'opponent', 'name']]
    
    print(f"Required feature columns ({len(feature_columns)}): {feature_columns}")
else:
    print("No training data found!")
    feature_columns = []

# 3. Load aggregated features that should have the real data
print("\n3. Loading aggregated features...")
agg_files = [
    "aggregated_hitter_features.csv",
    "aggregated_hitter_features_2025.csv",
    "fd_hitter_features_enriched.csv",
    "fd_hitter_features_with_context.csv"
]

best_features = None
best_shape = 0

for file in agg_files:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"{file}: {df.shape} - {list(df.columns)[:10]}...")
        if df.shape[1] > best_shape:
            best_features = df
            best_shape = df.shape[1]
            best_file = file

if best_features is not None:
    print(f"\nUsing {best_file} as the base features with {best_features.shape}")
    
    # 4. Create proper feature alignment
    print("\n4. Creating proper feature alignment...")
    
    # Start with FD slate data for player info
    aligned_features = fd_features[['Id', 'Position', 'First Name', 'Nickname', 'Last Name', 
                                  'FPPG', 'Played', 'Salary', 'Game', 'Team', 'Opponent',
                                  'Injury Indicator', 'Injury Details', 'Tier', 'Probable Pitcher',
                                  'Batting Order', 'Roster Position', 'player_id', 'proj_points',
                                  'name_key', 'game_pk']].copy()
    
    print(f"Base aligned features: {aligned_features.shape}")
    
    # 5. Merge with the best features available
    # Create a mapping key
    if 'name_key' in best_features.columns:
        merge_key = 'name_key'
    elif 'player_id' in best_features.columns:
        merge_key = 'player_id'
    else:
        # Create name_key for merging
        if 'name' in best_features.columns:
            best_features['name_key'] = best_features['name'].str.lower().str.replace(' ', '')
            merge_key = 'name_key'
        else:
            print("Cannot find suitable merge key!")
            merge_key = None
    
    if merge_key:
        print(f"Merging on: {merge_key}")
        aligned_features = aligned_features.merge(
            best_features, 
            on=merge_key, 
            how='left', 
            suffixes=('', '_stats')
        )
        
        print(f"After merge: {aligned_features.shape}")
        print(f"Columns after merge: {list(aligned_features.columns)}")
        
        # Fill missing values with reasonable defaults
        numeric_cols = aligned_features.select_dtypes(include=[np.number]).columns
        aligned_features[numeric_cols] = aligned_features[numeric_cols].fillna(0)
        
        # 6. Ensure we have the required training features
        print("\n6. Ensuring required training features...")
        for col in feature_columns:
            if col not in aligned_features.columns:
                aligned_features[col] = 0
                print(f"Added missing column: {col}")
        
        # 7. Save the properly aligned features
        output_path = os.path.join(data_dir, "fd_hitter_features_properly_aligned.csv")
        aligned_features.to_csv(output_path, index=False)
        print(f"\nSaved properly aligned features to: {output_path}")
        print(f"Final shape: {aligned_features.shape}")
        
        # Show sample of actual data
        print("\nSample of aligned data (first player, key stats):")
        sample_cols = ['name_key', 'Team', 'Opponent'] + [col for col in ['atBats', 'hits', 'homeRuns', 'rbi', 'runs'] if col in aligned_features.columns][:5]
        print(aligned_features[sample_cols].head(1))
        
        # 8. Quick retrain with properly aligned data
        print("\n8. Quick retrain test with aligned data...")
        
        if training_files and len(feature_columns) > 0:
            # Load training data
            train_df = pd.read_csv(training_files[0])
            
            # Test on hits model
            if 'hits' in train_df.columns:
                X_train = train_df[feature_columns].fillna(0)
                y_train = train_df['hits'].fillna(0)
                
                # Quick train
                model = GradientBoostingRegressor(n_estimators=50, random_state=42)
                model.fit(X_train, y_train)
                
                # Test prediction on aligned data
                X_pred = aligned_features[feature_columns].fillna(0)
                predictions = model.predict(X_pred)
                
                print(f"Training data shape: {X_train.shape}")
                print(f"Prediction data shape: {X_pred.shape}")
                print(f"Sample predictions: {predictions[:5]}")
                print(f"Prediction range: {predictions.min():.3f} to {predictions.max():.3f}")
                
                if len(set(predictions)) > 1:
                    print("✅ SUCCESS: Predictions are varying!")
                    
                    # Save this working model
                    model_path = os.path.join(data_dir, "hits_model_fixed.pkl")
                    joblib.dump(model, model_path)
                    print(f"Saved working model to: {model_path}")
                else:
                    print("❌ ISSUE: Predictions are still identical")
        
        print("\n" + "="*60)
        print("FINAL MODEL FIX COMPLETE")
        print("Use fd_hitter_features_properly_aligned.csv for predictions")
        print("="*60)
        
    else:
        print("Could not create proper alignment - no suitable merge key found")
else:
    print("No suitable feature files found!")
