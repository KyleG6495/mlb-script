#!/usr/bin/env python3
"""
get_real_player_stats.py

Replace default stats with real current season data for all players.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

print("📊 GETTING REAL PLAYER STATS")
print("="*50)

# Paths
data_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data"

# 1. Load current prediction features and FD slate
print("\n1. Loading current data...")
pred_features = pd.read_csv(os.path.join(data_dir, "prediction_features_with_pitchers.csv"))
fd_slate = pd.read_csv(os.path.join(data_dir, "fd_hitter_features_final.csv"))

print(f"   Prediction features: {pred_features.shape}")
print(f"   FD slate: {fd_slate.shape}")

# 2. Load all available real stats sources
print("\n2. Loading real stats sources...")
stats_sources = {}

# Try different aggregated stats files
potential_files = [
    "aggregated_hitter_features_2025.csv",
    "aggregated_hitter_features.csv", 
    "fd_hitter_features_with_context.csv",
    "hitter_rolling_5game_features.csv",
    "hitter_boxscores_full.csv"
]

for file in potential_files:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, parse_dates=['date'] if 'date' in pd.read_csv(path, nrows=1).columns else None)
            stats_sources[file] = df
            print(f"   ✅ {file}: {df.shape}")
            if 'player_id' in df.columns:
                print(f"      Players: {df['player_id'].nunique()}")
            if 'date' in df.columns:
                print(f"      Date range: {df['date'].min()} to {df['date'].max()}")
        except Exception as e:
            print(f"   ❌ Error loading {file}: {e}")

# 3. Create comprehensive player stats database
print("\n3. Creating comprehensive player stats...")

# Start with the most recent/comprehensive source
best_stats = None
best_coverage = 0

for file, df in stats_sources.items():
    if 'player_id' in df.columns:
        coverage = df['player_id'].nunique()
        if coverage > best_coverage:
            best_stats = df.copy()
            best_coverage = coverage
            best_file = file

if best_stats is not None:
    print(f"   Using {best_file} as primary source ({best_coverage} players)")
    
    # Get most recent stats for each player
    if 'date' in best_stats.columns:
        recent_stats = best_stats.sort_values('date').groupby('player_id').tail(1)
    else:
        recent_stats = best_stats.groupby('player_id').mean(numeric_only=True)
        recent_stats['player_id'] = recent_stats.index
    
    print(f"   Recent stats: {recent_stats.shape}")
else:
    print("   ❌ No suitable stats source found")
    recent_stats = pd.DataFrame()

# 4. Merge additional stats from other sources
print("\n4. Merging additional stats sources...")

# Combine stats from multiple sources for better coverage
combined_stats = recent_stats.copy() if not recent_stats.empty else pd.DataFrame()

for file, df in stats_sources.items():
    if file != best_file and 'player_id' in df.columns and not df.empty:
        # Get players not yet covered
        if not combined_stats.empty:
            missing_players = fd_slate[~fd_slate['player_id'].isin(combined_stats['player_id'])]['player_id'].unique()
        else:
            missing_players = fd_slate['player_id'].unique()
        
        if len(missing_players) > 0:
            # Get stats for missing players
            if 'date' in df.columns:
                additional_stats = df[df['player_id'].isin(missing_players)].sort_values('date').groupby('player_id').tail(1)
            else:
                additional_stats = df[df['player_id'].isin(missing_players)].groupby('player_id').mean(numeric_only=True)
                additional_stats['player_id'] = additional_stats.index
            
            if not additional_stats.empty:
                if combined_stats.empty:
                    combined_stats = additional_stats
                else:
                    # Merge on common columns
                    common_cols = list(set(combined_stats.columns) & set(additional_stats.columns))
                    combined_stats = pd.concat([combined_stats, additional_stats[common_cols]], ignore_index=True)
                
                print(f"   Added {len(additional_stats)} players from {file}")

if not combined_stats.empty:
    print(f"   Total combined stats: {combined_stats.shape}")
    print(f"   Total players with real stats: {combined_stats['player_id'].nunique()}")
else:
    print("   ❌ Could not create combined stats")

# 5. Create enhanced prediction features with real stats
print("\n5. Creating enhanced prediction features...")

if not combined_stats.empty:
    # Start with FD slate structure
    enhanced_features = fd_slate[['player_id', 'First Name', 'Last Name', 'Team', 'Opponent']].copy()
    enhanced_features['name'] = enhanced_features['First Name'] + ' ' + enhanced_features['Last Name']
    
    # Merge with real stats
    enhanced_features = enhanced_features.merge(
        combined_stats,
        on='player_id',
        how='left',
        suffixes=('', '_real')
    )
    
    print(f"   Enhanced features shape: {enhanced_features.shape}")
    
    # Fill missing stats with intelligent defaults based on position/league averages
    stat_columns = ['atBats', 'hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 'strikeOuts', 
                   'stolenBases', 'caughtStealing', 'hitByPitch', 'sacFlies', 'doubles', 'triples', 'sacBunts']
    
    # Calculate position-based defaults from available data
    position_defaults = {}
    if 'Position' in enhanced_features.columns:
        for stat in stat_columns:
            if stat in enhanced_features.columns:
                pos_stats = enhanced_features.groupby('Position')[stat].median()
                position_defaults[stat] = pos_stats.to_dict()
    
    # League-wide defaults
    league_defaults = {
        'atBats': 3.2, 'hits': 0.9, 'homeRuns': 0.15, 'rbi': 0.5, 'runs': 0.5,
        'baseOnBalls': 0.35, 'strikeOuts': 0.9, 'stolenBases': 0.1, 'caughtStealing': 0.02,
        'hitByPitch': 0.03, 'sacFlies': 0.02, 'doubles': 0.18, 'triples': 0.015, 'sacBunts': 0.01
    }
    
    # Fill missing values intelligently
    filled_count = 0
    for stat in stat_columns:
        if stat in enhanced_features.columns:
            missing_mask = enhanced_features[stat].isna()
            missing_count = missing_mask.sum()
            
            if missing_count > 0:
                # Try position-based defaults first
                if stat in position_defaults and 'Position' in enhanced_features.columns:
                    enhanced_features.loc[missing_mask, stat] = enhanced_features.loc[missing_mask, 'Position'].map(
                        position_defaults[stat]
                    ).fillna(league_defaults.get(stat, 0))
                else:
                    # Use league defaults
                    enhanced_features.loc[missing_mask, stat] = league_defaults.get(stat, 0)
                
                filled_count += missing_count
    
    print(f"   Filled {filled_count} missing stat values")
    
    # Add team encoding (for model compatibility)
    teams = list(set(list(enhanced_features['Team'].unique()) + list(enhanced_features['Opponent'].unique())))
    team_mapping = {team: i for i, team in enumerate(teams)}
    
    enhanced_features['team'] = enhanced_features['Team'].map(team_mapping).fillna(0)
    enhanced_features['opponent'] = enhanced_features['Opponent'].map(team_mapping).fillna(0)
    
    # Add pitcher features (from previous work)
    pitcher_features_df = pd.read_csv(os.path.join(data_dir, "prediction_features_with_pitchers.csv"))
    pitcher_cols = [col for col in pitcher_features_df.columns if 'pitcher_' in col]
    
    if pitcher_cols:
        pitcher_data = pitcher_features_df[['player_id'] + pitcher_cols]
        enhanced_features = enhanced_features.merge(pitcher_data, on='player_id', how='left')
        print(f"   Added {len(pitcher_cols)} pitcher features")
    
    # Add date and final columns
    enhanced_features['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Ensure all required model features exist
    required_features = ['atBats', 'hits', 'homeRuns', 'rbi', 'runs', 'baseOnBalls', 'strikeOuts', 
                        'stolenBases', 'caughtStealing', 'hitByPitch', 'sacFlies', 'doubles', 'triples', 
                        'team', 'opponent', 'sacBunts']
    
    for feature in required_features:
        if feature not in enhanced_features.columns:
            enhanced_features[feature] = league_defaults.get(feature, 0)
    
    print(f"   Final enhanced features: {enhanced_features.shape}")
    
    # Save enhanced features
    output_path = os.path.join(data_dir, "prediction_features_enhanced_real_stats.csv")
    enhanced_features.to_csv(output_path, index=False)
    print(f"   ✅ Saved enhanced features to: {output_path}")
    
    # 6. Show improvement statistics
    print("\n6. Statistics comparison:")
    
    # Compare with old default-heavy data
    old_features = pred_features[stat_columns].fillna(0)
    new_features = enhanced_features[stat_columns].fillna(0)
    
    print("   Stat variance (higher = more realistic):")
    for stat in stat_columns[:5]:  # Show first 5 stats
        if stat in old_features.columns and stat in new_features.columns:
            old_var = old_features[stat].var()
            new_var = new_features[stat].var()
            improvement = ((new_var - old_var) / old_var * 100) if old_var > 0 else float('inf')
            print(f"     {stat}: {old_var:.4f} → {new_var:.4f} ({improvement:+.1f}%)")
    
    # Show sample real vs default stats
    print(f"\n   Sample real stats (first 3 players):")
    sample_cols = ['name', 'atBats', 'hits', 'homeRuns', 'rbi', 'runs']
    available_sample_cols = [col for col in sample_cols if col in enhanced_features.columns]
    print(enhanced_features[available_sample_cols].head(3).to_string(index=False))
    
else:
    print("   ❌ Could not create enhanced features - no real stats available")

print("\n" + "="*50)
print("📊 REAL PLAYER STATS INTEGRATION COMPLETE")
print("Use 'prediction_features_enhanced_real_stats.csv' for most realistic predictions")
print("="*50)
