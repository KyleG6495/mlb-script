#!/usr/bin/env python3
"""
 IL FILTER SYSTEM
Remove all IL players from the FanDuel slate
"""

import pandas as pd
import os
from datetime import datetime

def filter_il_players():
    """Remove IL players from slate and create healthy-only version"""
    
    print(" IL FILTERING SYSTEM")
    print("=" * 50)
    
    # Read the current slate
    slate_path = '../fd_current_slate/fd_slate_today.csv'
    if not os.path.exists(slate_path):
        print(f"ERROR: Slate file not found: {slate_path}")
        return False
    
    try:
        df = pd.read_csv(slate_path)
        print(f"DATA: Original slate: {len(df)} players")
        
        # Check for IL players
        if 'Injury Indicator' not in df.columns:
            print("WARNING:  No 'Injury Indicator' column found")
            return False
        
        # Count IL players
        il_players = df[df['Injury Indicator'] == 'IL']
        il_count = len(il_players)
        
        if il_count > 0:
            print(f" Found {il_count} IL players:")
            for _, player in il_players.iterrows():
                name = f"{player.get('First Name', '')} {player.get('Last Name', '')}"
                injury = player.get('Injury Details', 'Unknown')
                team = player.get('Team', '')
                position = player.get('Position', '')
                print(f"   ERROR: {name} ({position}-{team}) - {injury}")
        
        # Create healthy-only slate
        healthy_df = df[df['Injury Indicator'] != 'IL'].copy()
        
        # Save IL-free slate
        output_path = '../data/fd_slate_NO_IL_PLAYERS.csv'
        healthy_df.to_csv(output_path, index=False)
        
        print(f"")
        print(f"SUCCESS: HEALTHY SLATE CREATED:")
        print(f"   DATA: Original players: {len(df)}")
        print(f"   ERROR: IL players removed: {il_count}")
        print(f"   SUCCESS: Healthy players: {len(healthy_df)}")
        print(f"    Saved to: {output_path}")
        
        # Also create confirmed starters if possible
        if 'Probable Pitcher' in df.columns:
            confirmed_pitchers = healthy_df[
                (healthy_df['Position'] == 'P') & 
                (healthy_df['Probable Pitcher'] == 'Yes')
            ]
            confirmed_hitters = healthy_df[healthy_df['Position'] != 'P']
            
            if len(confirmed_pitchers) > 0:
                confirmed_df = pd.concat([confirmed_pitchers, confirmed_hitters], ignore_index=True)
                confirmed_path = '../data/fd_slate_confirmed_starters_only.csv'
                confirmed_df.to_csv(confirmed_path, index=False)
                
                print(f"")
                print(f"TARGET: CONFIRMED STARTERS SLATE:")
                print(f"   SUCCESS: Confirmed pitchers: {len(confirmed_pitchers)}")
                print(f"   SUCCESS: All hitters: {len(confirmed_hitters)}")
                print(f"   SUCCESS: Total confirmed: {len(confirmed_df)}")
                print(f"    Saved to: {confirmed_path}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Error filtering IL players: {e}")
        return False

if __name__ == "__main__":
    success = filter_il_players()
    if success:
        print("\nSTART: IL filtering complete - use healthy slate for lineups!")
    else:
        print("\nERROR: IL filtering failed - check errors above")
