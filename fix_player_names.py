#!/usr/bin/env python3
"""
Quick fix: Add player names to prediction features
"""

import pandas as pd
import os

print("STEP: Adding player names to prediction features...")

# Load FD slate with names
fd_slate = pd.read_csv("../data/fd_hitter_features_final.csv")
print(f"FD slate: {fd_slate.shape}")

# Load current prediction features
pred_features = pd.read_csv("../data/final_prediction_features.csv")
print(f"Current features: {pred_features.shape}")

# Add names from FD slate
name_mapping = fd_slate[['player_id', 'First Name', 'Last Name']].copy()
name_mapping['name'] = name_mapping['First Name'] + ' ' + name_mapping['Last Name']

# Update prediction features
pred_features_fixed = pred_features.merge(
    name_mapping[['player_id', 'name']], 
    on='player_id', 
    how='left',
    suffixes=('_old', '')
)

# Drop old empty name column and keep new one
if 'name_old' in pred_features_fixed.columns:
    pred_features_fixed = pred_features_fixed.drop('name_old', axis=1)

print(f"Fixed features: {pred_features_fixed.shape}")
print(f"Names added: {pred_features_fixed['name'].notna().sum()}/{len(pred_features_fixed)}")

# Save fixed version
pred_features_fixed.to_csv("../data/final_prediction_features.csv", index=False)
print("SUCCESS: Player names fixed!")

# Show sample
print(f"Sample names: {pred_features_fixed['name'].head().tolist()}")
