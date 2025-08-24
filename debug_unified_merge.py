#!/usr/bin/env python3
"""
Quick debug script to find the merge issue in Unified DFS System
"""
import pandas as pd
import os

print("=== UNIFIED DFS MERGE DEBUG ===")
print()

# Load slate data (same as Unified system)
slate_path = "../fd_current_slate/fd_slate_today.csv"
print(f"Loading slate: {slate_path}")
slate = pd.read_csv(slate_path)
print(f"Slate shape: {slate.shape}")
print(f"Slate columns: {slate.columns.tolist()}")
print(f"Sample slate Id values: {slate['Id'].head(3).tolist()}")
print()

# Filter slate (same as Unified system)
slate_filtered = slate[
    (slate['Tier'] != 'Late Swap') &
    (slate['Injury Indicator'].isna() | (slate['Injury Indicator'] == ''))
].copy()
print(f"After filtering: {len(slate_filtered)} players (removed {len(slate) - len(slate_filtered)})")
print()

# Load projection data (same as Unified system)
HITTER_FEATURES = "../data/fd_hitter_features_final.csv"
PITCHER_FEATURES = "../data/fd_pitcher_features_final.csv"

print(f"Loading hitters: {HITTER_FEATURES}")
hitters = pd.read_csv(HITTER_FEATURES)
print(f"Hitters shape: {hitters.shape}")
print(f"Hitters columns: {hitters.columns.tolist()}")
if 'Id' in hitters.columns:
    print(f"Sample hitter Id values: {hitters['Id'].head(3).tolist()}")
elif 'player_id' in hitters.columns:
    print(f"Sample hitter player_id values: {hitters['player_id'].head(3).tolist()}")
print()

print(f"Loading pitchers: {PITCHER_FEATURES}")
pitchers = pd.read_csv(PITCHER_FEATURES)
print(f"Pitchers shape: {pitchers.shape}")
print(f"Pitchers columns: {pitchers.columns.tolist()}")
if 'Id' in pitchers.columns:
    print(f"Sample pitcher Id values: {pitchers['Id'].head(3).tolist()}")
elif 'player_id' in pitchers.columns:
    print(f"Sample pitcher player_id values: {pitchers['player_id'].head(3).tolist()}")
print()

# Combine projections (same as Unified system)
if len(hitters) > 0 and len(pitchers) > 0:
    projections = pd.concat([hitters, pitchers], ignore_index=True)
elif len(hitters) > 0:
    projections = hitters
elif len(pitchers) > 0:
    projections = pitchers
else:
    print("ERROR: No projection files found")
    exit(1)

print(f"Combined projections shape: {projections.shape}")
print()

# Test merge with both Id and player_id columns
print("=== TESTING MERGE SCENARIOS ===")

# Scenario 1: Merge on Id
if 'Id' in projections.columns:
    print("Testing merge on 'Id' column...")
    merge_test1 = slate_filtered.merge(projections, on='Id', how='left', suffixes=('', '_proj'))
    non_null_proj = merge_test1[merge_test1['FPPG_proj'].notna() | merge_test1['Projected_FPPG'].notna()]
    print(f"Successful merges on Id: {len(non_null_proj)}/{len(merge_test1)}")
    
    if len(non_null_proj) > 0:
        print("SUCCESS: Id-based merge works!")
        print("Sample successful merge:")
        sample = non_null_proj.iloc[0]
        print(f"  Slate Id: {sample['Id']}")
        print(f"  FPPG: {sample.get('FPPG_proj', sample.get('Projected_FPPG', 'N/A'))}")
    else:
        print("FAILED: No successful merges on Id")
        print("Sample slate Ids:", slate_filtered['Id'].head(3).tolist())
        print("Sample projection Ids:", projections['Id'].head(3).tolist() if 'Id' in projections.columns else "No Id column")

# Scenario 2: Check if we need to extract player_id from slate Id
print()
print("Testing Id format extraction...")
sample_slate_ids = slate_filtered['Id'].head(3).tolist()
for slate_id in sample_slate_ids:
    if '-' in str(slate_id):
        extracted = str(slate_id).split('-')[1]
        print(f"  {slate_id} -> {extracted}")
        
        # Check if this extracted ID matches projections
        if 'player_id' in projections.columns:
            matches = projections[projections['player_id'].astype(str) == extracted]
            print(f"    Matches in projections: {len(matches)}")

print()
print("=== RECOMMENDATION ===")
if 'Id' in projections.columns:
    print("✅ Use direct Id merge - projections already have Id column")
else:
    print("⚠️ Need to extract player_id from slate Id and match with projections")
