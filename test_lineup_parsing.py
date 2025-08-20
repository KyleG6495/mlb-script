#!/usr/bin/env python3
"""
Test script to verify lineup confirmation parsing
"""

import pandas as pd
import os

def test_lineup_parsing():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    starting_lineups_path = os.path.join(script_dir, '..', 'data', 'starting_lineups.csv')
    fd_slate_path = os.path.join(script_dir, '..', 'fd_current_slate', 'fd_slate_today.csv')
    
    confirmed_lineups = {}
    expected_lineups = {}
    
    print("🔍 Testing lineup confirmation parsing...")
    
    # Load confirmed lineups
    if os.path.exists(starting_lineups_path):
        confirmed_df = pd.read_csv(starting_lineups_path)
        print(f"✅ Loaded {len(confirmed_df)} confirmed starters")
        
        if 'team' in confirmed_df.columns:
            for team in confirmed_df['team'].unique():
                if pd.notna(team):
                    team_players = confirmed_df[confirmed_df['team'] == team.upper()]
                    # Only get hitters (not pitchers)
                    hitters = team_players[team_players['position'] != 'P']
                    # Sort by batting order if available
                    if 'batting_order' in hitters.columns:
                        hitters = hitters.sort_values('batting_order', na_position='last')
                    
                    if 'player_name' in hitters.columns and len(hitters) > 0:
                        confirmed_lineups[team.upper()] = list(hitters['player_name'].head(8))
                        print(f"🔍 {team.upper()}: Found {len(hitters)} confirmed hitters: {list(hitters['player_name'].head(3))}")
    
    # Load expected lineups from FD slate
    if os.path.exists(fd_slate_path):
        fd_df = pd.read_csv(fd_slate_path)
        print(f"✅ Loaded {len(fd_df)} players from FD slate")
        
        if 'Team' in fd_df.columns:
            name_col = 'Name' if 'Name' in fd_df.columns else ('Nickname' if 'Nickname' in fd_df.columns else 'Player')
            
            for team in fd_df['Team'].unique():
                if pd.notna(team):
                    team_players = fd_df[fd_df['Team'] == team]
                    hitters = team_players[team_players['Position'] != 'P']
                    if len(hitters) > 0:
                        expected_lineups[team] = list(hitters[name_col].head(8))
                        print(f"🔍 {team}: Found {len(hitters)} expected hitters: {list(hitters[name_col].head(3))}")
    
    # Test comparison logic
    all_teams = set(list(confirmed_lineups.keys()) + list(expected_lineups.keys()))
    print(f"\n📊 LINEUP COMPARISON RESULTS:")
    print(f"Teams with confirmed lineups: {len(confirmed_lineups)}")
    print(f"Teams with expected lineups: {len(expected_lineups)}")
    print(f"Total teams: {len(all_teams)}")
    
    confirmed_count = 0
    pending_count = 0
    alert_count = 0
    
    for team in sorted(all_teams)[:12]:
        confirmed_players = confirmed_lineups.get(team, [])
        expected_players = expected_lineups.get(team, [])
        
        if confirmed_players and len(confirmed_players) >= 3:
            status = 'Confirmed'
            confirmed_count += 1
            confirmed_text = ', '.join(confirmed_players[:3]) + "..."
        elif expected_players:
            status = 'Pending'
            pending_count += 1
            confirmed_text = "Awaiting confirmation"
        else:
            status = 'Alert'
            alert_count += 1
            confirmed_text = "No data"
        
        expected_text = ', '.join(expected_players[:3]) + "..." if expected_players else "None"
        print(f"  {team}: {status} | Confirmed: {confirmed_text} | Expected: {expected_text}")
    
    print(f"\n🎯 FINAL METRICS:")
    print(f"  Confirmed: {confirmed_count}")
    print(f"  Pending: {pending_count}")
    print(f"  Alerts: {alert_count}")

if __name__ == "__main__":
    test_lineup_parsing()
