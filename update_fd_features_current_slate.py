#!/usr/bin/env python3
"""
Regenerate FanDuel feature files with current slate Ids
This fixes the Id mismatch between slate and projections
"""
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def update_fd_features_with_current_slate():
    """Update fd_hitter_features_final.csv and fd_pitcher_features_final.csv with current slate Ids"""
    
    print("=== UPDATING FANDUEL FEATURES WITH CURRENT SLATE ===")
    print()
    
    # Load current slate
    current_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    print(f"Loaded current slate: {len(current_slate)} players")
    print(f"Current slate Id format: {current_slate['Id'].iloc[0]}")
    
    # Load aggregated features (these have the real MLB data)
    hitter_agg = pd.read_csv("../data/aggregated_hitter_features_2025.csv")
    pitcher_agg = pd.read_csv("../data/aggregated_pitcher_features_2025.csv")
    
    print(f"Loaded aggregated hitters: {len(hitter_agg)} players")
    print(f"Loaded aggregated pitchers: {len(pitcher_agg)} players")
    
    # Create name-based mapping (since names should match)
    def create_name_key(row):
        """Create a standardized name key for matching"""
        first = str(row.get('First Name', row.get('first_name', ''))).strip().lower()
        last = str(row.get('Last Name', row.get('last_name', ''))).strip().lower()
        nickname = str(row.get('Nickname', row.get('name', ''))).strip().lower()
        
        # Use nickname if available, otherwise first + last
        if nickname and nickname != 'nan':
            return nickname
        else:
            return f"{first} {last}".strip()
    
    # Add name keys
    current_slate['name_key'] = current_slate.apply(create_name_key, axis=1)
    hitter_agg['name_key'] = hitter_agg.apply(create_name_key, axis=1)
    pitcher_agg['name_key'] = pitcher_agg.apply(create_name_key, axis=1)
    
    print()
    print("=== MATCHING HITTERS ===")
    
    # Get hitters from current slate
    slate_hitters = current_slate[current_slate['Position'] != 'P'].copy()
    print(f"Hitters in current slate: {len(slate_hitters)}")
    
    # Merge hitters
    hitter_matched = slate_hitters.merge(
        hitter_agg, 
        on='name_key', 
        how='left', 
        suffixes=('', '_agg')
    )
    
    # Keep only successfully matched hitters with projections
    hitter_final = hitter_matched.dropna(subset=['atBats']).copy()
    
    # Add projection columns if missing
    if 'Projected_FPPG' not in hitter_final.columns:
        # Simple projection based on recent performance
        hitter_final['Projected_FPPG'] = (
            hitter_final['hits'] * 3.0 +  # Singles
            hitter_final['homeRuns'] * 10.0 +  # Home runs  
            hitter_final.get('rbi', 0) * 2.0 +  # RBI
            hitter_final.get('runs', 0) * 2.0 +  # Runs
            hitter_final.get('stolenBases', 0) * 5.0  # Stolen bases
        ) / 10  # Scale down
        
    # Add other projection columns
    hitter_final['ceil_proj'] = hitter_final['Projected_FPPG'] * 1.4
    hitter_final['floor_proj'] = hitter_final['Projected_FPPG'] * 0.7
    hitter_final['ownership_proj'] = 8.0  # Default
    hitter_final['value'] = hitter_final['Projected_FPPG'] / (hitter_final['Salary'] / 1000)
    hitter_final['Batting_Order'] = hitter_final.get('Batting Order', 0)
    hitter_final['Season'] = 2025
    
    print(f"Successfully matched hitters: {len(hitter_final)}")
    
    print()
    print("=== MATCHING PITCHERS ===")
    
    # Get pitchers from current slate  
    slate_pitchers = current_slate[current_slate['Position'] == 'P'].copy()
    print(f"Pitchers in current slate: {len(slate_pitchers)}")
    
    # Merge pitchers
    pitcher_matched = slate_pitchers.merge(
        pitcher_agg,
        on='name_key',
        how='left',
        suffixes=('', '_agg')
    )
    
    # Keep only successfully matched pitchers
    pitcher_final = pitcher_matched.dropna(subset=['strikeOuts']).copy()
    
    # Add player_id column for pitchers (extracted from Id)
    pitcher_final['player_id'] = pitcher_final['Id'].astype(str).str.split('-').str[1]
    
    print(f"Successfully matched pitchers: {len(pitcher_final)}")
    
    # Save updated files
    print()
    print("=== SAVING UPDATED FILES ===")
    
    hitter_output = "../data/fd_hitter_features_final.csv"
    hitter_final.to_csv(hitter_output, index=False)
    print(f"✅ Saved updated hitters: {hitter_output} ({len(hitter_final)} players)")
    
    pitcher_output = "../data/fd_pitcher_features_final.csv"  
    pitcher_final.to_csv(pitcher_output, index=False)
    print(f"✅ Saved updated pitchers: {pitcher_output} ({len(pitcher_final)} players)")
    
    print()
    print("=== VERIFICATION ===")
    print(f"Current slate Id format: {current_slate['Id'].iloc[0]}")
    print(f"Updated hitter Id format: {hitter_final['Id'].iloc[0] if len(hitter_final) > 0 else 'No hitters'}")
    print(f"Updated pitcher Id format: {pitcher_final['Id'].iloc[0] if len(pitcher_final) > 0 else 'No pitchers'}")
    
    return len(hitter_final), len(pitcher_final)

if __name__ == "__main__":
    hitter_count, pitcher_count = update_fd_features_with_current_slate()
    print()
    print("=== COMPLETE ===")
    print(f"✅ FanDuel feature files updated with current slate Ids")
    print(f"📊 {hitter_count} hitters, {pitcher_count} pitchers ready for Unified DFS System")
