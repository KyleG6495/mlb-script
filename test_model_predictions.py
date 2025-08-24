#!/usr/bin/env python3
"""
test_model_predictions.py

Direct test of model predictions to debug the 0.1 issue
"""

import pandas as pd
import numpy as np
import joblib
import os

print(" Testing Model Predictions Directly")
print("="*50)

# Load the prediction features
print("\n1. Loading prediction features...")
pred_features = pd.read_csv("../data/prediction_ready_features.csv")
print(f"   Shape: {pred_features.shape}")
print(f"   Columns: {list(pred_features.columns)}")

# Load a trained model
print("\n2. Loading total_bases model...")
model = joblib.load("models/total_bases/total_bases_pipeline.joblib")
print(f"   Model type: {type(model)}")

# Check what features the model expects
if hasattr(model, 'feature_names_in_'):
    expected_features = list(model.feature_names_in_)
    print(f"   Expected features: {expected_features}")
else:
    print("   Cannot determine expected features")

# 3. Prepare prediction data
print("\n3. Preparing prediction data...")

# Get numeric columns that might be features
numeric_cols = pred_features.select_dtypes(include=[np.number]).columns.tolist()
print(f"   Available numeric columns: {numeric_cols}")

# Try to match with expected features if available
if hasattr(model, 'feature_names_in_'):
    # Use only the features the model was trained on
    available_features = [col for col in expected_features if col in pred_features.columns]
    missing_features = [col for col in expected_features if col not in pred_features.columns]
    
    print(f"   Available features: {len(available_features)}/{len(expected_features)}")
    print(f"   Available: {available_features}")
    if missing_features:
        print(f"   Missing: {missing_features}")
    
    if len(available_features) > 0:
        X = pred_features[available_features].fillna(0)
    else:
        print("   No matching features found!")
        X = None
else:
    # Use all numeric columns
    X = pred_features[numeric_cols].fillna(0)

if X is not None:
    print(f"   Prediction data shape: {X.shape}")
    print(f"   Sample values:")
    print(X.head(3))
    
    # 4. Make predictions
    print("\n4. Making predictions...")
    try:
        predictions = model.predict(X)
        
        print(f"   Predictions shape: {predictions.shape}")
        print(f"   Sample predictions: {predictions[:10]}")
        print(f"   Min: {predictions.min():.3f}")
        print(f"   Max: {predictions.max():.3f}")
        print(f"   Mean: {predictions.mean():.3f}")
        print(f"   Std: {predictions.std():.3f}")
        print(f"   Unique values: {len(np.unique(predictions))}")
        
        if predictions.std() < 0.001:
            print("   ERROR: ISSUE: All predictions are identical!")
            
            # Debug further
            print("\n5. Debugging identical predictions...")
            print(f"   Input data stats:")
            print(X.describe())
            
            # Check if input data is all zeros
            if (X == 0).all().all():
                print("   ERROR: All input features are zero!")
            elif X.std().sum() < 0.001:
                print("   ERROR: Input features have no variance!")
            else:
                print("   SUCCESS: Input features look reasonable")
                
        else:
            print("   SUCCESS: SUCCESS: Predictions vary!")
            
            # Show some examples
            print(f"\n   Sample player predictions:")
            for i in range(min(10, len(pred_features))):
                name = pred_features.iloc[i].get('name', f'Player {i+1}')
                print(f"     {name}: {predictions[i]:.3f}")
    
    except Exception as e:
        print(f"   ERROR: Prediction failed: {e}")
        import traceback
        traceback.print_exc()

# 5. Compare with training data
print("\n6. Comparing with training data...")
try:
    # Load historical data to see feature ranges
    hist_features = pd.read_csv("../data/hitter_rolling_5game_features.csv")
    
    if hasattr(model, 'feature_names_in_'):
        hist_available = [col for col in model.feature_names_in_ if col in hist_features.columns]
        if hist_available:
            hist_X = hist_features[hist_available].fillna(0)
            print(f"   Historical feature stats:")
            print(hist_X.describe().round(3))
            
            print(f"\n   Current prediction feature stats:")
            current_X = pred_features[[col for col in hist_available if col in pred_features.columns]].fillna(0)
            print(current_X.describe().round(3))
            
except Exception as e:
    print(f"   Error comparing with historical: {e}")

print("\n" + "="*50)
print(" MODEL TEST COMPLETE")
print("="*50)
