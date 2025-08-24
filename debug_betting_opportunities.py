#!/usr/bin/env python3
"""
debug_betting_opportunities.py

Debug script to see what's happening with line matching
"""

import pandas as pd
import numpy as np
from scipy import stats

# Load PrizePicks data
pp_file = "../data/PP_mlb_picks_20250719_175116.xlsx"
df = pd.read_excel(pp_file)
print("PrizePicks data shape:", df.shape)
print("\nColumns:", df.columns.tolist())
print("\nFirst few rows:")
print(df.head())

# Convert to long format
df_long = pd.melt(df, id_vars=['player_name'], value_name='line').dropna(subset=['line'])
print(f"\nLong format shape: {df_long.shape}")
print("\nVariable values:")
print(df_long['variable'].value_counts())

# Look at hits specifically
hits_props = df_long[df_long['variable'] == 'Hits']
print(f"\nHits props: {len(hits_props)}")
print(hits_props.head())

# Load model predictions for hits
hitter_features = pd.read_csv("../data/fd_hitter_features_final.csv")
print(f"\nHitter features shape: {hitter_features.shape}")
if 'name' in hitter_features.columns:
    print("\nFirst few hitter names:")
    print(hitter_features['name'].head(10))

# Try to match a specific player
if len(hits_props) > 0:
    sample_player = hits_props.iloc[0]['player_name']
    print(f"\nSample player from PrizePicks: '{sample_player}'")
    
    # Look for matches in hitter features
    matches = hitter_features[hitter_features['name'].str.contains(sample_player.split()[0], case=False, na=False)]
    print(f"Matches found: {len(matches)}")
    if len(matches) > 0:
        print("Matched names:", matches['name'].tolist())

# Load a trained model and make a sample prediction
import joblib
hits_model = joblib.load("./models/hits/hits_model.pkl")
print(f"\nHits model loaded: {type(hits_model)}")

# Try prediction on first player
if 'name' in hitter_features.columns and len(hitter_features) > 0:
    sample_row = hitter_features.iloc[0:1]
    print(f"\nSample player: {sample_row['name'].iloc[0]}")
    
    # Prepare features
    X = sample_row.select_dtypes(include=[np.number])
    expected_features = list(hits_model.feature_names_in_)
    
    # Add missing features
    for col in expected_features:
        if col not in X.columns:
            X[col] = 0
    
    # Reorder columns
    X = X.reindex(columns=expected_features, fill_value=0)
    
    # Predict
    prediction = hits_model.predict(X)[0]
    print(f"Predicted hits: {prediction:.2f}")
    
    # Calculate probability for line 1.5 hits
    prob_over_15 = 1 - stats.norm.cdf(1.5, loc=prediction, scale=1.24)
    print(f"Probability over 1.5 hits: {prob_over_15:.2%}")
    
    # Look for this player in PrizePicks
    player_name = sample_row['name'].iloc[0]
    first_name = player_name.split()[0]
    
    pp_matches = hits_props[hits_props['player_name'].str.contains(first_name, case=False, na=False)]
    print(f"\nPrizePicks matches for '{first_name}': {len(pp_matches)}")
    if len(pp_matches) > 0:
        print("PrizePicks lines:")
        for _, row in pp_matches.iterrows():
            print(f"  {row['player_name']}: {row['line']}")
            
            # Calculate expected value
            line = row['line']
            model_prob_over = 1 - stats.norm.cdf(line, loc=prediction, scale=1.24)
            implied_prob = 0.5  # Assume 50/50 for now
            
            # Simple EV calculation assuming -110 odds
            ev_over = (model_prob_over * 0.909) - ((1 - model_prob_over) * 1)
            ev_under = ((1 - model_prob_over) * 0.909) - (model_prob_over * 1)
            
            print(f"    Line: {line} | Model Prob Over: {model_prob_over:.2%}")
            print(f"    EV Over: {ev_over:+.3f} | EV Under: {ev_under:+.3f}")
            print(f"    Best bet: {'OVER' if ev_over > ev_under else 'UNDER'}")
