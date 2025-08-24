#!/usr/bin/env python3
"""
Trace exactly where Unified DFS System loses all players
"""
import pandas as pd
import numpy as np

print("=== UNIFIED DFS FILTERING TRACE ===")
print()

# Step 1: Load slate data (exactly like Unified system)
slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
print(f"1. Initial slate: {len(slate)} players")

# Step 2: Filter inactive players (exactly like Unified system)
slate_filtered = slate[
    (slate['Tier'] != 'Late Swap') &
    (slate['Injury Indicator'].isna() | (slate['Injury Indicator'] == ''))
].copy()
print(f"2. After filtering inactive: {len(slate_filtered)} players")

# Filter for starting pitchers and active non-pitchers
pitchers = slate_filtered[slate_filtered['Position'] == 'P']
non_pitchers = slate_filtered[slate_filtered['Position'] != 'P']

# Keep only probable starting pitchers 
starting_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
print(f"3. Starting pitchers: {len(starting_pitchers)}")
print(f"   Non-pitchers: {len(non_pitchers)}")

# Combine for final active players
final_slate = pd.concat([starting_pitchers, non_pitchers], ignore_index=True)
print(f"4. Final active players: {len(final_slate)} players")

# Step 3: Load projections (exactly like Unified system)
hitters = pd.read_csv("../data/fd_hitter_features_final.csv")
pitchers = pd.read_csv("../data/fd_pitcher_features_final.csv")
projections = pd.concat([hitters, pitchers], ignore_index=True)
print(f"5. Loaded projections: {len(projections)} players")

# Step 4: Merge (exactly like Unified system)
df = final_slate.merge(projections, on='Id', how='left', suffixes=('', '_proj'))
print(f"6. After merge: {len(df)} players")

# Step 5: Check projection column priority
proj_cols = ['Projected_FPPG', 'projected_fppg', 'FPPG', 'fppg', 'projection']
proj_col = None
for col in proj_cols:
    if col in df.columns:
        proj_col = col
        print(f"7. Using projection column: {proj_col}")
        break

# Step 6: Create base_fppg (exactly like Unified system)
df['base_fppg'] = df[proj_col].fillna(0)
print(f"8. Created base_fppg column")

# Step 7: Check filtering stages
print()
print("FILTERING BREAKDOWN:")
print(f"  Total players: {len(df)}")
print(f"  With non-null {proj_col}: {df[proj_col].notna().sum()}")
print(f"  With base_fppg > 0: {(df['base_fppg'] > 0).sum()}")
print(f"  With base_fppg = 0: {(df['base_fppg'] == 0).sum()}")

# Step 8: Apply the filtering that Unified system does
zero_projection_filter = df['base_fppg'] > 0
players_after_filter = df[zero_projection_filter].copy()
print(f"9. After filtering base_fppg > 0: {len(players_after_filter)} players")

if len(players_after_filter) > 0:
    print()
    print("SUCCESS! We have players remaining. The issue might be later in the process.")
    print("Sample remaining players:")
    sample = players_after_filter[['Id', 'Nickname', 'Position', 'Salary', proj_col, 'base_fppg']].head(5)
    print(sample.to_string())
    
    # Check position distribution
    print()
    print("Position breakdown:")
    pos_counts = players_after_filter['Position'].value_counts()
    print(pos_counts.to_string())
    
else:
    print()
    print("❌ PROBLEM FOUND: No players pass the base_fppg > 0 filter")
    print()
    print("Debugging the projection values:")
    print(f"  {proj_col} column type: {df[proj_col].dtype}")
    print(f"  Sample {proj_col} values (first 10):")
    sample_values = df[proj_col].head(10).tolist()
    for i, val in enumerate(sample_values):
        print(f"    Row {i}: {val} (type: {type(val).__name__})")
    
    print(f"  Sample base_fppg values (first 10):")
    sample_base = df['base_fppg'].head(10).tolist()
    for i, val in enumerate(sample_base):
        print(f"    Row {i}: {val} (type: {type(val).__name__})")
    
    print()
    print("Check for data type issues or NaN handling problems")
