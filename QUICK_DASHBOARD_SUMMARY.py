#!/usr/bin/env python3
"""
QUICK DASHBOARD SUMMARY
Prints dashboard data directly to terminal for easy copy/paste
"""

import pandas as pd
from file_finder_utils import get_data_files, safe_read_csv

def show_dashboard_summary():
    """Print dashboard data to terminal"""
    
    print("🏆 ELITE TOURNAMENT DASHBOARD SUMMARY")
    print("=" * 60)
    
    data_files = get_data_files()
    
    # Show elite lineups
    if 'elite_lineups' in data_files:
        df = safe_read_csv(data_files['elite_lineups'])
        if df is not None:
            print("\n📊 TOP 5 ELITE LINEUPS:")
            print("-" * 40)
            for i, row in df.head(5).iterrows():
                print(f"\nLineup #{i+1} - {row.get('Stack_Team', 'Unknown')} Strategy:")
                print(f"  💰 Salary: ${row.get('Total_Salary', 0):,}")
                print(f"  📈 Projection: {row.get('Projected_Points', 0):.1f}")
                print(f"  👥 Ownership: {row.get('Avg_Ownership', 0):.1%}")
                print(f"  🎯 Tournament Score: {row.get('Tournament_Score', 0):.1f}")
                
                # Explain strategy type
                stack_team = row.get('Stack_Team', 'Unknown')
                if stack_team == 'Contrarian Play':
                    print(f"  💡 Strategy: Mix of low-ownership individual players")
                elif stack_team and len(stack_team) <= 5:
                    print(f"  💡 Strategy: Team stack with multiple {stack_team} players")
    
    # Show ownership highlights
    if 'ownership' in data_files:
        df = safe_read_csv(data_files['ownership'])
        if df is not None:
            print("\n📈 OWNERSHIP HIGHLIGHTS:")
            print("-" * 40)
            
            # Top chalk plays
            chalk = df[df['ownership'] > 0.25].sort_values('ownership', ascending=False)
            print("\n🔥 TOP CHALK PLAYS:")
            for _, player in chalk.head(5).iterrows():
                print(f"  {player['player_name']} - {player['ownership']:.1%}")
            
            # Top contrarian plays
            contrarian = df[df['ownership'] < 0.08].sort_values('leverage_score', ascending=False)
            print("\n🎯 TOP CONTRARIAN PLAYS:")
            for _, player in contrarian.head(5).iterrows():
                print(f"  {player['player_name']} - {player['ownership']:.1%} (Leverage: {player['leverage_score']:.2f})")
    
    # Show slate overview
    if 'slate' in data_files:
        df = safe_read_csv(data_files['slate'])
        if df is not None:
            # Filter active players
            if 'Injury Indicator' in df.columns:
                active_df = df[df['Injury Indicator'].isna()]
            else:
                active_df = df
                
            print("\n⚾ TODAY'S SLATE:")
            print("-" * 40)
            
            # Top pitchers
            pitchers = active_df[
                (active_df['Position'] == 'P') & 
                (active_df.get('Probable Pitcher', '') == 'Yes')
            ].sort_values('FPPG', ascending=False)
            
            print("\n🥎 TOP PITCHERS:")
            for _, pitcher in pitchers.head(5).iterrows():
                print(f"  {pitcher['Nickname']} ({pitcher['Team']}) - ${pitcher['Salary']} | {pitcher['FPPG']:.1f} vs {pitcher['Opponent']}")
            
            # Top hitters
            hitters = active_df[
                (active_df['Position'] != 'P') & 
                (active_df.get('Batting Order', 0) > 0)
            ].sort_values('FPPG', ascending=False)
            
            print("\n🏏 TOP HITTERS:")
            for _, hitter in hitters.head(8).iterrows():
                print(f"  {hitter['Nickname']} ({hitter['Position']}, {hitter['Team']}) - ${hitter['Salary']} | {hitter['FPPG']:.1f}")
    
    print("\n" + "=" * 60)
    print("📋 This output can be copied/pasted for analysis!")

if __name__ == "__main__":
    show_dashboard_summary()
