#!/usr/bin/env python3
"""
create_prediction_features.py

Create proper prediction features that match the training data format.
This transforms today's FanDuel slate into the same feature structure used for model training.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

print("STEP: Creating Proper Prediction Features")
print("="*60)

# Paths
data_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data"

# 1. Load today's FanDuel slate (base player list)
print("\n1. Loading FanDuel slate...")
fd_slate = pd.read_csv(os.path.join(data_dir, "fd_hitter_features_final.csv"))
print(f"   FD slate: {fd_slate.shape}")
print(f"   Players: {fd_slate['player_id'].nunique()}")

# 2. Load historical rolling features to understand the feature structure
print("\n2. Loading historical feature structure...")
historical_features = pd.read_csv(os.path.join(data_dir, "hitter_rolling_5game_features.csv"))
print(f"   Historical features: {historical_features.shape}")
print(f"   Historical columns: {list(historical_features.columns)}")

# Get the feature columns (exclude ID/date/target columns)
feature_columns = [col for col in historical_features.columns if col not in 
                  ['player_id', 'name', 'date', 'team', 'opponent']]
print(f"   Feature columns needed: {feature_columns}")

# 3. Load the aggregated stats that have real player data
print("\n3. Loading player statistical data...")
stats_files = [
    "aggregated_hitter_features_with_context.csv",
    "fd_hitter_features_with_context.csv", 
    "aggregated_hitter_features_2025.csv"
]

player_stats = None
for file in stats_files:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        df = pd.read_csv(path)
        print(f"   {file}: {df.shape}")
        if player_stats is None and 'player_id' in df.columns:
            player_stats = df
            print(f"   Using {file} for player stats")
            break

# 4. Create the prediction feature set
print("\n4. Creating prediction features...")

# Start with FD slate for structure
prediction_features = fd_slate[['player_id', 'First Name', 'Last Name', 'Team', 'Opponent']].copy()

# Create name key for merging
prediction_features['name'] = (prediction_features['First Name'] + ' ' + prediction_features['Last Name']).str.lower()
prediction_features['name_key'] = prediction_features['name'].str.replace(' ', '')

print(f"   Base prediction features: {prediction_features.shape}")

# 5. Merge with player stats
if player_stats is not None:
    # Create merge key for stats if needed
    if 'name_key' not in player_stats.columns and 'name' in player_stats.columns:
        player_stats['name_key'] = player_stats['name'].str.lower().str.replace(' ', '')
    
    # Merge on the best available key
    merge_key = 'player_id' if 'player_id' in player_stats.columns else 'name_key'
    
    print(f"   Merging on: {merge_key}")
    prediction_features = prediction_features.merge(
        player_stats, 
        on=merge_key, 
        how='left',
        suffixes=('', '_stats')
    )
    print(f"   After stats merge: {prediction_features.shape}")

# 6. Ensure all required feature columns exist
print("\n6. Adding missing feature columns...")
missing_features = []
for col in feature_columns:
    if col not in prediction_features.columns:
        # Set reasonable defaults based on column name
        if any(x in col.lower() for x in ['avg', 'obp', 'slg', 'ops']):
            prediction_features[col] = 0.250  # Reasonable batting average baseline
        elif any(x in col.lower() for x in ['temp', 'wind']):
            prediction_features[col] = 72.0 if 'temp' in col.lower() else 5.0  # Weather defaults
        elif 'park_factor' in col.lower():
            prediction_features[col] = 1.0  # Neutral park factor
        else:
            prediction_features[col] = 0.0  # Default to 0 for counting stats
        
        missing_features.append(col)

if missing_features:
    print(f"   Added {len(missing_features)} missing features: {missing_features[:5]}...")

# 7. Create recent performance estimates
print("\n7. Estimating recent performance...")

# If we have aggregated stats, create rolling estimates
if any(col in prediction_features.columns for col in ['atBats', 'hits', 'homeRuns']):
    # Create basic rate stats if we have counting stats
    for stat in ['hits', 'doubles', 'triples', 'homeRuns', 'rbi', 'runs', 'strikeOuts', 'baseOnBalls']:
        if stat in prediction_features.columns and 'atBats' in prediction_features.columns:
            # Create rate per at-bat
            rate_col = f'{stat}_per_ab'
            if rate_col in feature_columns:
                prediction_features[rate_col] = (
                    prediction_features[stat].fillna(0) / 
                    prediction_features['atBats'].fillna(1).replace(0, 1)
                )

# 8. Handle team/opponent encoding
print("\n8. Encoding team/opponent...")
if 'Team' in prediction_features.columns and 'Opponent' in prediction_features.columns:
    # Create simple team strength indicators (you could enhance this with historical data)
    strong_teams = ['LAD', 'ATL', 'HOU', 'NYY', 'SD', 'PHI']  # Example strong teams
    
    if 'team_strength' in feature_columns:
        prediction_features['team_strength'] = prediction_features['Team'].apply(
            lambda x: 1.1 if x in strong_teams else 1.0
        )
    
    if 'opponent_strength' in feature_columns:
        prediction_features['opponent_strength'] = prediction_features['Opponent'].apply(
            lambda x: 1.1 if x in strong_teams else 1.0
        )

# 9. Add today's date
today = datetime.now()
prediction_features['date'] = today.strftime('%Y-%m-%d')

# 10. Final feature preparation
print("\n10. Final feature preparation...")

# Select only the columns that exist in both training and prediction
final_columns = ['player_id', 'name', 'date', 'Team', 'Opponent'] + feature_columns
available_columns = [col for col in final_columns if col in prediction_features.columns]

final_prediction_features = prediction_features[available_columns].copy()

# Fill any remaining NaN values
numeric_columns = final_prediction_features.select_dtypes(include=[np.number]).columns
final_prediction_features[numeric_columns] = final_prediction_features[numeric_columns].fillna(0)

print(f"   Final prediction features: {final_prediction_features.shape}")
print(f"   Feature columns: {len([col for col in final_prediction_features.columns if col in feature_columns])}")

# 11. Save the prediction-ready features
output_path = os.path.join(data_dir, "prediction_ready_features.csv")
final_prediction_features.to_csv(output_path, index=False)
print(f"\nSUCCESS: Saved prediction-ready features to: {output_path}")

# 12. Test with a sample prediction
print("\n12. Testing sample prediction...")
try:
    import joblib
    
    # Load a trained model to test
    model_path = os.path.join(data_dir, "total_bases_pipeline.joblib")
    if os.path.exists(model_path):
        model = joblib.load(model_path)
        
        # Get feature columns for prediction
        prediction_cols = [col for col in feature_columns if col in final_prediction_features.columns]
        X_test = final_prediction_features[prediction_cols].fillna(0)
        
        print(f"   Prediction data shape: {X_test.shape}")
        
        # Make predictions
        predictions = model.predict(X_test)
        
        print(f"   Sample predictions: {predictions[:5]}")
        print(f"   Prediction range: {predictions.min():.3f} to {predictions.max():.3f}")
        print(f"   Mean prediction: {predictions.mean():.3f}")
        
        if predictions.std() > 0.01:  # Check if predictions vary
            print("   SUCCESS: SUCCESS: Predictions are varying!")
            
            # Show some example predictions
            print(f"\n   Sample player predictions:")
            for i in range(min(5, len(final_prediction_features))):
                player_name = final_prediction_features.iloc[i]['name'] if 'name' in final_prediction_features.columns else f"Player {i+1}"
                print(f"     {player_name}: {predictions[i]:.2f} total bases")
                
        else:
            print("   ERROR: WARNING: Predictions are still identical")
            
    else:
        print(f"   Model not found at: {model_path}")
        
except Exception as e:
    print(f"   ERROR: Test prediction failed: {e}")

print("\n" + "="*60)
print("SUCCESS: PREDICTION FEATURES CREATED SUCCESSFULLY")
print(f"Use 'prediction_ready_features.csv' for model predictions")
print("="*60)
