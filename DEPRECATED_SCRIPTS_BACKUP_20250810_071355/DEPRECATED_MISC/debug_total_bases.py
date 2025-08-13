#!/usr/bin/env python3
"""
debug_total_bases.py

Debug script to specifically test total_bases model training
"""

import pandas as pd
import numpy as np

# Load the data files
print("🔍 Debugging total_bases model training...")

# Load hitter boxscores
print("\n1. Loading hitter boxscores...")
log = pd.read_csv("../data/hitter_boxscores_full.csv", parse_dates=['date'])
print(f"   Shape: {log.shape}")
print(f"   Columns: {log.columns.tolist()}")
print(f"   Date range: {log['date'].min()} to {log['date'].max()}")

# Check for required columns
required_cols = ['hits', 'doubles', 'triples', 'homeRuns']
missing_cols = [col for col in required_cols if col not in log.columns]
if missing_cols:
    print(f"   ❌ Missing columns: {missing_cols}")
else:
    print(f"   ✅ All required columns present: {required_cols}")

# Load hitter features
print("\n2. Loading hitter features...")
feat = pd.read_csv("../data/hitter_rolling_5game_features.csv", parse_dates=['date'])
print(f"   Shape: {feat.shape}")
print(f"   Date range: {feat['date'].min()} to {feat['date'].max()}")

# Calculate total bases manually
print("\n3. Calculating total bases...")
log['totalBases'] = (
    log.get('hits', 0) + 
    log.get('doubles', 0) * 2 + 
    log.get('triples', 0) * 3 + 
    log.get('homeRuns', 0) * 4
)

print(f"   Total bases stats:")
print(f"   Mean: {log['totalBases'].mean():.2f}")
print(f"   Std: {log['totalBases'].std():.2f}")
print(f"   Min: {log['totalBases'].min()}")
print(f"   Max: {log['totalBases'].max()}")
print(f"   Null values: {log['totalBases'].isnull().sum()}")

# Show distribution
print(f"\n   Total bases distribution:")
print(log['totalBases'].value_counts().sort_index())

# Merge datasets
print("\n4. Merging datasets...")
df = pd.merge(
    log[['player_id', 'name', 'date', 'totalBases']],
    feat,
    on=['player_id', 'date'], 
    how='inner'
)
print(f"   Merged shape: {df.shape}")
print(f"   Merged columns: {df.columns.tolist()}")
print(f"   Total bases after merge - Mean: {df['totalBases'].mean():.2f}")

# Check for data issues
print("\n5. Data quality checks...")
print(f"   Players with data: {df['player_id'].nunique()}")
print(f"   Date range after merge: {df['date'].min()} to {df['date'].max()}")
print(f"   Rows with null totalBases: {df['totalBases'].isnull().sum()}")

# Sample some records
print("\n6. Sample records:")
if 'name' in df.columns:
    print(df[['name', 'date', 'totalBases']].head(10))
else:
    print("No 'name' column after merge - showing available columns:")
    print(df[['player_id', 'date', 'totalBases']].head(10))

# Try a simple model training
print("\n7. Testing model training...")
try:
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error
    
    # Prepare data (handle column naming issues after merge)
    cols_to_drop = ['player_id', 'date', 'totalBases']
    if 'name' in df.columns:
        cols_to_drop.append('name')
    elif 'name_x' in df.columns:
        cols_to_drop.append('name_x')
    elif 'name_y' in df.columns:
        cols_to_drop.append('name_y')
    
    X = df.drop(columns=cols_to_drop).select_dtypes(include=[np.number])
    y = df['totalBases'].astype(float)
    
    print(f"   Features shape: {X.shape}")
    print(f"   Target shape: {y.shape}")
    print(f"   Target stats - Mean: {y.mean():.2f}, Std: {y.std():.2f}")
    
    # Split and train
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = GradientBoostingRegressor(random_state=42, n_estimators=50)
    model.fit(X_train, y_train)
    
    # Predict and evaluate
    preds = model.predict(X_val)
    mae = mean_absolute_error(y_val, preds)
    
    print(f"   ✅ Model trained successfully!")
    print(f"   Validation MAE: {mae:.3f}")
    print(f"   Sample predictions vs actual:")
    for i in range(5):
        print(f"     Pred: {preds[i]:.2f} | Actual: {y_val.iloc[i]:.2f}")
        
except Exception as e:
    print(f"   ❌ Model training failed: {e}")
    import traceback
    traceback.print_exc()

print("\n8. Testing with actual training script...")
try:
    import subprocess
    import sys
    
    # Try running the actual training script for total_bases
    cmd = [
        sys.executable,
        "train_prop_model.py",
        "--category", "total_bases",
        "--game-log", "../data/hitter_boxscores_full.csv", 
        "--features", "../data/hitter_rolling_5game_features.csv",
        "--output-dir", "./test_models/total_bases"
    ]
    
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    
    print(f"   Exit code: {result.returncode}")
    if result.stdout:
        print(f"   STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"   STDERR:\n{result.stderr}")
        
except Exception as e:
    print(f"   ❌ Training script test failed: {e}")

print("\n✅ Debug complete!")
