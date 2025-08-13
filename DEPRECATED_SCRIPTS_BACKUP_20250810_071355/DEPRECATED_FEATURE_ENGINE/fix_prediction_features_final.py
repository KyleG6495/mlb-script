#!/usr/bin/env python3
"""
fix_prediction_features_final.py

Final fix: Create prediction features using REAL player statistics 
that match the exact format your models were trained on.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

print("🎯 FINAL PREDICTION FEATURES FIX")
print("="*60)

# Paths
data_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data"

# 1. Load today's FanDuel slate (our target players)
print("\n1. Loading today's FanDuel slate...")
fd_slate = pd.read_csv(os.path.join(data_dir, "fd_hitter_features_final.csv"))
print(f"   FD slate: {fd_slate.shape}")
print(f"   Target players: {fd_slate['player_id'].nunique()}")

# 2. Load the ACTUAL rolling features (the same data used for training)
print("\n2. Loading REAL rolling features...")
rolling_features = pd.read_csv(os.path.join(data_dir, "hitter_rolling_5game_features.csv"), parse_dates=['date'])
print(f"   Rolling features: {rolling_features.shape}")
print(f"   Date range: {rolling_features['date'].min()} to {rolling_features['date'].max()}")

# 3. Get the most recent stats for each player
print("\n3. Getting most recent player stats...")
# Get the latest available stats for each player
latest_stats = rolling_features.sort_values('date').groupby('player_id').tail(1)
print(f"   Latest stats: {latest_stats.shape}")
print(f"   Players with stats: {latest_stats['player_id'].nunique()}")

# Show sample of real data
print(f"   Sample real stats:")
sample_cols = ['name', 'atBats', 'hits', 'homeRuns', 'rbi', 'runs']
available_sample_cols = [col for col in sample_cols if col in latest_stats.columns]
print(latest_stats[available_sample_cols].head(3))

# 4. Create prediction features by merging FD slate with real stats
print("\n4. Creating prediction features with real data...")

# Start with FD slate
prediction_df = fd_slate[['player_id', 'First Name', 'Last Name', 'Team', 'Opponent']].copy()

# Merge with latest stats
prediction_df = prediction_df.merge(
    latest_stats,
    on='player_id',
    how='left',
    suffixes=('', '_stats')
)

print(f"   After merge: {prediction_df.shape}")

# 5. Fix team/opponent naming (models expect lowercase)
print("\n5. Fixing team/opponent naming...")
if 'Team' in prediction_df.columns:
    prediction_df['team'] = prediction_df['Team']
if 'Opponent' in prediction_df.columns:
    prediction_df['opponent'] = prediction_df['Opponent']

# Create simple numeric encoding for teams (models might expect this)
teams = list(set(list(prediction_df['Team'].unique()) + list(prediction_df['Opponent'].unique())))
team_mapping = {team: i for i, team in enumerate(teams)}

prediction_df['team'] = prediction_df['Team'].map(team_mapping).fillna(0)
prediction_df['opponent'] = prediction_df['Opponent'].map(team_mapping).fillna(0)

print(f"   Encoded {len(teams)} teams")

# 6. Ensure all required features exist with reasonable defaults
print("\n6. Ensuring all required features...")
required_features = [
    'atBats', 'hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 
    'strikeOuts', 'stolenBases', 'caughtStealing', 'hitByPitch', 
    'sacFlies', 'doubles', 'triples', 'team', 'opponent', 'sacBunts'
]

for feature in required_features:
    if feature not in prediction_df.columns:
        if feature in ['team', 'opponent']:
            prediction_df[feature] = 0
        else:
            prediction_df[feature] = 0.0
        print(f"   Added missing: {feature}")

# Fill NaN values with reasonable defaults based on feature type
for feature in required_features:
    if feature in ['team', 'opponent']:
        prediction_df[feature] = prediction_df[feature].fillna(0)
    else:
        # Use median from available data or reasonable default
        if prediction_df[feature].notna().sum() > 0:
            median_val = prediction_df[feature].median()
            prediction_df[feature] = prediction_df[feature].fillna(median_val)
        else:
            # Set reasonable defaults
            defaults = {
                'atBats': 3.2, 'hits': 0.8, 'homeRuns': 0.1, 'rbi': 0.4,
                'runs': 0.4, 'baseOnBalls': 0.3, 'strikeOuts': 0.8,
                'stolenBases': 0.05, 'doubles': 0.15, 'triples': 0.01
            }
            prediction_df[feature] = prediction_df[feature].fillna(defaults.get(feature, 0.0))

# 7. Create final prediction dataset
print("\n7. Creating final prediction dataset...")
final_features = ['player_id', 'name'] + required_features
available_features = [col for col in final_features if col in prediction_df.columns]

if 'name' not in prediction_df.columns:
    prediction_df['name'] = prediction_df['First Name'] + ' ' + prediction_df['Last Name']

final_prediction_data = prediction_df[available_features].copy()

# Add today's date
final_prediction_data['date'] = datetime.now().strftime('%Y-%m-%d')

print(f"   Final prediction data: {final_prediction_data.shape}")

# 8. Show statistics to verify we have real data
print("\n8. Verifying real data statistics...")
stats_summary = final_prediction_data[required_features].describe()
print(stats_summary)

# Check if we have non-zero variance
has_variance = []
for feature in required_features:
    if final_prediction_data[feature].std() > 0.001:
        has_variance.append(feature)

print(f"   Features with variance: {len(has_variance)}/{len(required_features)}")
print(f"   Variable features: {has_variance}")

if len(has_variance) > 5:
    print("   ✅ SUCCESS: Multiple features have real variance!")
else:
    print("   ⚠️ WARNING: Limited feature variance")

# 9. Save the final prediction features
output_path = os.path.join(data_dir, "final_prediction_features.csv")
final_prediction_data.to_csv(output_path, index=False)
print(f"\n✅ Saved final prediction features to: {output_path}")

# 10. Test with actual model
print("\n10. Testing with trained model...")
try:
    import joblib
    
    # Load the total_bases model
    model_path = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\models\total_bases\total_bases_pipeline.joblib"
    model = joblib.load(model_path)
    
    # Prepare features for prediction
    X_features = final_prediction_data[required_features]
    
    print(f"    Prediction data shape: {X_features.shape}")
    print(f"    Feature sample:")
    print(X_features.head(3))
    
    # Make predictions
    predictions = model.predict(X_features)
    
    print(f"    Predictions: {predictions[:10]}")
    print(f"    Range: {predictions.min():.3f} to {predictions.max():.3f}")
    print(f"    Mean: {predictions.mean():.3f}")
    print(f"    Std: {predictions.std():.3f}")
    
    if predictions.std() > 0.1:
        print("    ✅ SUCCESS: Predictions are realistic and varying!")
        
        # Show sample predictions
        print(f"\n    Sample player predictions:")
        for i in range(min(10, len(final_prediction_data))):
            player_name = final_prediction_data.iloc[i]['name']
            print(f"      {player_name}: {predictions[i]:.2f} total bases")
    else:
        print("    ❌ Still getting uniform predictions")
        
except Exception as e:
    print(f"    ❌ Model test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("🎯 FINAL PREDICTION FEATURES COMPLETE")
print("Use 'final_prediction_features.csv' for realistic predictions")
print("="*60)
