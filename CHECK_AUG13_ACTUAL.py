#!/usr/bin/env python3
"""
Check what was actually generated on August 13th
"""

import pandas as pd

def check_august_13_lineups():
    """Check what lineups were actually generated on August 13th"""
    
    print(" AUGUST 13TH ACTUAL GENERATION CHECK")
    print("=" * 50)
    
    try:
        # Load the actual submission file from August 13th
        df = pd.read_csv("../data/fanduel_submission_20250813_175857.csv")
        print(f"SUCCESS: Loaded actual submissions: {len(df)} lineups")
        
        # Check for Miami players
        miami_lineups = []
        all_players = set()
        
        for idx, row in df.iterrows():
            lineup_players = [row['P'], row['C'], row['1B'], row['2B'], row['3B'], row['SS'], row['OF'], row['OF2'], row['OF3']]
            
            # Add to all players set
            for player in lineup_players:
                if pd.notna(player):
                    all_players.add(str(player))
            
            # Check for Miami
            miami_count = sum(1 for player in lineup_players if pd.notna(player) and ('MIA' in str(player)))
            if miami_count > 0:
                miami_lineups.append({
                    'lineup_id': row['Lineup_ID'],
                    'miami_count': miami_count,
                    'total_projection': row['Total_Projection'],
                    'players': lineup_players
                })
        
        print(f"DATA: Found {len(miami_lineups)} lineups with Miami players out of {len(df)} total")
        
        if len(miami_lineups) > 0:
            print(f"\n MIAMI LINEUPS GENERATED:")
            for lineup in miami_lineups[:5]:
                print(f"  {lineup['lineup_id']}: {lineup['miami_count']} MIA players, {lineup['total_projection']:.1f} projected")
        else:
            print(f"\nERROR: NO MIAMI LINEUPS WERE GENERATED!")
            print(f"   This explains why we missed the 202.9-point opportunity")
        
        # Check what teams were actually used
        team_usage = {}
        for player in all_players:
            if '@' in player:  # Extract team from player string
                try:
                    team = player.split('@')[0].split(' ')[-1]
                    team_usage[team] = team_usage.get(team, 0) + 1
                except:
                    pass
        
        print(f"\nPROGRESS: TEAM USAGE IN GENERATED LINEUPS:")
        sorted_teams = sorted(team_usage.items(), key=lambda x: x[1], reverse=True)
        for team, count in sorted_teams[:10]:
            print(f"  {team}: {count} player selections")
        
        # Check if Miami was used at all
        miami_usage = team_usage.get('MIA', 0)
        if miami_usage == 0:
            print(f"\n PROBLEM IDENTIFIED:")
            print(f"   MIA was used {miami_usage} times in {len(df)} lineups")
            print(f"   This explains why we missed the winning team!")
        
        # Check top projected lineups
        print(f"\nLINEUP: TOP PROJECTED LINEUPS (that were actually generated):")
        top_lineups = df.nlargest(3, 'Total_Projection')
        for idx, lineup in top_lineups.iterrows():
            print(f"  {lineup['Lineup_ID']}: {lineup['Total_Projection']:.1f} projected")
            players = [lineup['P'], lineup['C'], lineup['1B'], lineup['2B'], lineup['3B'], lineup['SS'], lineup['OF'], lineup['OF2'], lineup['OF3']]
            teams = []
            for player in players:
                if pd.notna(player) and '@' in str(player):
                    try:
                        team = str(player).split('@')[0].split(' ')[-1]
                        teams.append(team)
                    except:
                        pass
            team_counts = {}
            for team in teams:
                team_counts[team] = team_counts.get(team, 0) + 1
            stacks = [f"{team}({count})" for team, count in team_counts.items() if count >= 2]
            print(f"    Stacks: {', '.join(stacks) if stacks else 'No stacks'}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_august_13_lineups()
