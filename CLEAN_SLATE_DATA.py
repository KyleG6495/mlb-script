#!/usr/bin/env python3
"""
CLEAN SLATE DATA - Remove injured players and validate current slate
"""

import pandas as pd
from datetime import datetime
import os

def clean_slate_data():
    """Clean and validate slate data"""
    print("🧹 CLEANING SLATE DATA")
    print("="*40)
    
    # Load current slate
    slate_path = "../fd_current_slate/fd_slate_today.csv"
    slate_df = pd.read_csv(slate_path)
    
    print(f"📊 Original slate: {len(slate_df)} players")
    
    # Check for injury indicators
    injury_cols = ['Injury Indicator', 'Injury Details', 'Injury Status']
    injury_col = None
    for col in injury_cols:
        if col in slate_df.columns:
            injury_col = col
            break
    
    if injury_col:
        print(f"🏥 Checking injury column: {injury_col}")
        
        # Find injured players
        injured_mask = slate_df[injury_col].notna() & (slate_df[injury_col] != '') & (slate_df[injury_col] != 'NONE')
        injured_players = slate_df[injured_mask]
        
        print(f"⚠️ Found {len(injured_players)} injured players:")
        for idx, player in injured_players.iterrows():
            name = player['Nickname']
            team = player['Team']
            injury = player[injury_col]
            print(f"  🚑 {name} ({team}): {injury}")
        
        # Remove injured players
        clean_slate = slate_df[~injured_mask].copy()
        print(f"✅ Clean slate: {len(clean_slate)} players")
        print(f"🗑️ Removed: {len(slate_df) - len(clean_slate)} injured players")
        
        # Save cleaned slate
        backup_path = f"../fd_current_slate/fd_slate_today_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        clean_path = "../fd_current_slate/fd_slate_today_clean.csv"
        
        # Backup original
        slate_df.to_csv(backup_path, index=False)
        print(f"💾 Backup saved: {backup_path}")
        
        # Save clean version
        clean_slate.to_csv(clean_path, index=False)
        print(f"✅ Clean slate saved: {clean_path}")
        
        # Show clean teams
        clean_teams = sorted(clean_slate['Team'].unique())
        print(f"🎯 Clean slate teams ({len(clean_teams)}): {clean_teams}")
        
        # Show clean pitchers
        clean_pitchers = clean_slate[clean_slate['Position'] == 'P']
        print(f"⚾ Clean slate pitchers: {len(clean_pitchers)}")
        
        return clean_slate, injured_players
    else:
        print("⚠️ No injury column found")
        return slate_df, pd.DataFrame()

def validate_slate_teams():
    """Validate which teams are actually playing today"""
    print("\n🎯 VALIDATING TEAMS PLAYING TODAY")
    print("="*40)
    
    # This would normally check against MLB API or schedule
    # For now, let's check game column
    slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    if 'Game' in slate_df.columns:
        games = slate_df['Game'].unique()
        print(f"🏟️ Games found ({len(games)}):")
        for game in sorted(games):
            if pd.notna(game):
                print(f"  {game}")
        
        # Extract teams from games
        teams_in_games = set()
        for game in games:
            if pd.notna(game) and '@' in str(game):
                away, home = str(game).split('@')
                teams_in_games.add(away.strip())
                teams_in_games.add(home.strip())
        
        print(f"🎯 Teams in games: {sorted(teams_in_games)}")
        
        # Compare with teams in slate
        slate_teams = set(slate_df['Team'].unique())
        print(f"📋 Teams in slate: {sorted(slate_teams)}")
        
        # Find mismatches
        extra_teams = slate_teams - teams_in_games
        missing_teams = teams_in_games - slate_teams
        
        if extra_teams:
            print(f"⚠️ Teams in slate but not in games: {sorted(extra_teams)}")
        if missing_teams:
            print(f"⚠️ Teams in games but missing from slate: {sorted(missing_teams)}")
        
        return teams_in_games, slate_teams
    else:
        print("⚠️ No Game column found for validation")
        return set(), set()

if __name__ == "__main__":
    print("🧹 SLATE DATA CLEANER")
    print("="*50)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Clean injured players
    clean_slate, injured = clean_slate_data()
    
    # Validate teams
    game_teams, slate_teams = validate_slate_teams()
    
    print("\n✅ CLEANING COMPLETE!")
    print("="*30)
    print("Next steps:")
    print("1. Review the clean slate file")
    print("2. Update your dashboard to use clean data")
    print("3. Verify team matchups are correct")
