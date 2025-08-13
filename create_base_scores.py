#!/usr/bin/env python3
"""
create_base_scores.py
Create base_hitter_scores.csv and base_pitcher_scores.csv from available DFS data
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_base_hitter_scores():
    """Create base_hitter_scores.csv from FD slate and features"""
    
    print("📊 Creating base_hitter_scores.csv...")
    
    # Load FanDuel slate
    fd_slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
    
    # Filter to hitters only
    hitters = fd_slate[fd_slate['Position'] != 'P'].copy()
    
    # Extract player_id from the Id column (format: 118937-16960)
    hitters['player_id'] = hitters['Id'].str.split('-').str[1].astype(int)
    
    # Use FPPG as base_score (fantasy points per game)
    hitters['base_score'] = hitters['FPPG'].fillna(8.0)  # Default to 8.0 if missing
    
    # Add today's date
    hitters['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Select required columns
    base_hitters = hitters[['player_id', 'date', 'base_score']].copy()
    
    print(f"✅ Created {len(base_hitters)} hitter base scores")
    
    # Save to data directory
    output_path = '../data/base_hitter_scores.csv'
    base_hitters.to_csv(output_path, index=False)
    print(f"💾 Saved to {output_path}")
    
    return base_hitters

def create_base_pitcher_scores():
    """Create base_pitcher_scores.csv from FD slate"""
    
    print("⚾ Creating base_pitcher_scores.csv...")
    
    # Load FanDuel slate
    fd_slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
    
    # Filter to pitchers only
    pitchers = fd_slate[fd_slate['Position'] == 'P'].copy()
    
    # Extract player_id from the Id column
    pitchers['player_id'] = pitchers['Id'].str.split('-').str[1].astype(int)
    
    # Use FPPG as base_score
    pitchers['base_score'] = pitchers['FPPG'].fillna(25.0)  # Default to 25.0 for pitchers
    
    # Add today's date
    pitchers['date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Select required columns
    base_pitchers = pitchers[['player_id', 'date', 'base_score']].copy()
    
    print(f"✅ Created {len(base_pitchers)} pitcher base scores")
    
    # Save to data directory
    output_path = '../data/base_pitcher_scores.csv'
    base_pitchers.to_csv(output_path, index=False)
    print(f"💾 Saved to {output_path}")
    
    return base_pitchers

if __name__ == "__main__":
    print("🚀 Creating base score files from FanDuel slate...")
    
    try:
        hitters = create_base_hitter_scores()
        pitchers = create_base_pitcher_scores()
        
        print("\n✅ SUCCESS!")
        print(f"📊 Created base scores for {len(hitters)} hitters and {len(pitchers)} pitchers")
        print("🎯 These files are now available for prop betting analysis")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
