#!/usr/bin/env python3
"""
Check Enhanced System Output from August 13th
"""

import pandas as pd

def check_enhanced_system_output():
    """Check what the enhanced system actually generated on August 13th"""
    
    print(" ENHANCED SYSTEM OUTPUT CHECK (August 13th)")
    print("=" * 60)
    
    try:
        # Load the enhanced system output with names
        df = pd.read_csv("../data/FANDUEL_LINEUPS_WITH_NAMES_20250813_182557.csv")
        print(f"SUCCESS: Enhanced system generated: {len(df)} lineups")
        print(f"Columns: {df.columns.tolist()}")
        
        # Check for Miami players
        miami_count = 0
        miami_lineups = []
        
        for idx, row in df.iterrows():
            lineup_id = row.get('Lineup_ID', f'Lineup_{idx+1}')
            lineup_miami_count = 0
            
            for col in df.columns:
                if col != 'Lineup_ID' and pd.notna(row[col]):
                    if 'MIA' in str(row[col]):
                        miami_count += 1
                        lineup_miami_count += 1
            
            if lineup_miami_count > 0:
                miami_lineups.append((lineup_id, lineup_miami_count))
        
        print(f"\nDATA: MIAMI ANALYSIS:")
        print(f"   Total Miami player selections: {miami_count}")
        print(f"   Lineups with Miami players: {len(miami_lineups)}")
        
        if len(miami_lineups) > 0:
            print(f"\n MIAMI LINEUPS:")
            for lineup_id, count in miami_lineups:
                print(f"   {lineup_id}: {count} Miami players")
        else:
            print(f"\nERROR: NO MIAMI PLAYERS IN ENHANCED SYSTEM OUTPUT!")
        
        # Show sample lineups
        print(f"\nINFO: SAMPLE LINEUPS:")
        for i in range(min(3, len(df))):
            print(f"\nLineup {i+1}:")
            row = df.iloc[i]
            for col in df.columns:
                if col != 'Lineup_ID' and pd.notna(row[col]):
                    print(f"   {col}: {row[col]}")
        
        # Check team distribution
        print(f"\nPROGRESS: TEAM USAGE ANALYSIS:")
        team_usage = {}
        
        for _, row in df.iterrows():
            for col in df.columns:
                if col != 'Lineup_ID' and pd.notna(row[col]):
                    player_str = str(row[col])
                    if '@' in player_str:
                        # Extract team (format might be "Player Name @ Team")
                        team = player_str.split('@')[-1].strip()
                        team_usage[team] = team_usage.get(team, 0) + 1
                    elif ' (' in player_str and player_str.endswith(')'):
                        # Extract team from format "Player Name (TEAM)"
                        team = player_str.split('(')[-1].replace(')', '').strip()
                        team_usage[team] = team_usage.get(team, 0) + 1
        
        # Sort teams by usage
        sorted_teams = sorted(team_usage.items(), key=lambda x: x[1], reverse=True)
        
        print(f"Top teams used:")
        for team, count in sorted_teams[:10]:
            print(f"   {team}: {count} selections")
            
        # Check if Miami is in the list
        miami_usage = team_usage.get('MIA', 0)
        print(f"\nTARGET: MIAMI USAGE: {miami_usage} selections")
        
        if miami_usage == 0:
            print(f" CONFIRMED: Enhanced system did NOT use Miami players!")
            print(f"   This explains why we missed the 202.9-point opportunity")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_enhanced_system_output()
