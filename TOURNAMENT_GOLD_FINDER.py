#!/usr/bin/env python3
"""
TOURNAMENT CRUSHER - August 13th Pattern Application
Applies proven winning patterns to today's slate
"""

import pandas as pd
import numpy as np
from datetime import datetime

def find_tournament_gold():
    """Find today's tournament gold using August 13th patterns"""
    
    print("LINEUP: TOURNAMENT CRUSHER - August 13th Pattern Application")
    print("=" * 60)
    
    # Load aggressive projections
    df = pd.read_csv("../data/aggressive_upside_projections_20250814_094533.csv")
    print(f"SUCCESS: Loaded {len(df)} players with aggressive projections")
    
    # Filter to probable starters only
    probable_pitchers = df[
        (df['Position'] == 'P') & 
        (df['Probable Pitcher'] == 'Yes')
    ].copy()
    
    starting_hitters = df[
        (df['Position'] != 'P') & 
        (df['Batting Order'] > 0)
    ].copy()
    
    print(f"TARGET: Filtered to {len(probable_pitchers)} probable pitchers, {len(starting_hitters)} starting hitters")
    
    # Apply August 13th learnings
    apply_august_13_patterns(probable_pitchers, starting_hitters)

def apply_august_13_patterns(pitchers, hitters):
    """Apply the specific patterns that worked on August 13th"""
    
    print("\n APPLYING AUGUST 13TH WINNING PATTERNS")
    print("=" * 50)
    
    # PATTERN 1: VALUE PITCHER STRATEGY ($6K-$10K range)
    print("\n VALUE PITCHER TARGETS:")
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].sort_values('enhanced_projection', ascending=False)
    
    top_value_pitchers = value_pitchers.head(5)
    for _, pitcher in top_value_pitchers.iterrows():
        proj = pitcher['enhanced_projection']
        pts_per_k = proj / (pitcher['Salary'] / 1000) if proj > 0 else 0
        print(f"  {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}) - "
              f"{proj:.1f} pts ({pts_per_k:.1f} pts/$K)")
    
    # PATTERN 2: NUCLEAR VALUE HITTERS (Under $3,500)
    print("\nSTART: NUCLEAR VALUE HITTERS:")
    value_hitters = hitters[hitters['Salary'] <= 3500].copy()
    value_hitters['pts_per_k'] = value_hitters['aggressive_projection'] / (value_hitters['Salary'] / 1000)
    nuclear_values = value_hitters.nlargest(10, 'pts_per_k')
    
    for _, hitter in nuclear_values.iterrows():
        if hitter['aggressive_projection'] > 20:  # High upside threshold
            print(f"   {hitter['Nickname']} {hitter['Last Name']} (${hitter['Salary']}) - "
                  f"{hitter['aggressive_projection']:.1f} pts ({hitter['pts_per_k']:.1f} pts/$K)")
    
    # PATTERN 3: GAME STACKING OPPORTUNITIES
    print("\n GAME STACKING OPPORTUNITIES:")
    find_stack_opportunities(hitters)
    
    # PATTERN 4: CONTRARIAN GEMS (Low ownership, high upside)
    print("\n CONTRARIAN GEMS:")
    contrarian_gems = hitters[
        (hitters['simulated_ownership'] < 8) & 
        (hitters['aggressive_projection'] > 18)
    ].sort_values('aggressive_projection', ascending=False)
    
    for _, gem in contrarian_gems.head(8).iterrows():
        print(f"   {gem['Nickname']} {gem['Last Name']} (${gem['Salary']}) - "
              f"{gem['aggressive_projection']:.1f} pts (~{gem['simulated_ownership']:.1f}% owned)")
    
    # BUILD SAMPLE LINEUPS
    print("\n BUILDING SAMPLE TOURNAMENT LINEUPS")
    print("=" * 40)
    
    build_nuclear_lineup(top_value_pitchers.iloc[0], nuclear_values, hitters)
    build_contrarian_lineup(top_value_pitchers.iloc[1], contrarian_gems, hitters)

def find_stack_opportunities(hitters):
    """Find the best stacking opportunities by team"""
    
    # Calculate team offensive projections
    team_projections = hitters.groupby('Team').agg({
        'aggressive_projection': ['sum', 'mean', 'count'],
        'Salary': 'mean'
    }).round(1)
    
    team_projections.columns = ['Total_Proj', 'Avg_Proj', 'Player_Count', 'Avg_Salary']
    team_projections = team_projections[team_projections['Player_Count'] >= 4]  # Stackable teams
    team_projections = team_projections.sort_values('Avg_Proj', ascending=False)
    
    print("  Top Team Stacking Targets:")
    for team, stats in team_projections.head(5).iterrows():
        print(f"    {team}: {stats['Avg_Proj']:.1f} avg proj, {int(stats['Player_Count'])} players, "
              f"${int(stats['Avg_Salary'])} avg salary")
    
    # Show specific stack options for top team
    top_team = team_projections.index[0]
    team_players = hitters[hitters['Team'] == top_team].sort_values('aggressive_projection', ascending=False)
    
    print(f"\n   {top_team} Stack Options:")
    for _, player in team_players.head(5).iterrows():
        print(f"    {player['Nickname']} {player['Last Name']} (${player['Salary']}) - "
              f"{player['aggressive_projection']:.1f} pts")

def build_nuclear_lineup(pitcher, nuclear_hitters, all_hitters):
    """Build a nuclear value lineup"""
    
    print(f"\nSTART: NUCLEAR VALUE LINEUP")
    print(f"Strategy: Value pitcher + nuclear value hitters")
    print("-" * 40)
    
    lineup = []
    remaining_salary = 35000
    
    # Start with value pitcher
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    print(f"P: {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}) - {pitcher['enhanced_projection']:.1f} pts")
    
    # Fill positions with best available
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    used_players = {pitcher['Id']}
    
    for pos in positions:
        best_player = find_best_for_position(pos, all_hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
            print(f"{pos}: {best_player['Nickname']} {best_player['Last Name']} "
                  f"(${best_player['Salary']}) - {best_player['aggressive_projection']:.1f} pts")
    
    total_salary = sum(player['Salary'] for _, player in lineup)
    total_proj = sum(player.get('aggressive_projection', player.get('enhanced_projection', 0)) for _, player in lineup)
    
    print(f"\nTotal Projection: {total_proj:.1f} points")
    print(f"Total Salary: ${total_salary:,}")
    print(f"Remaining: ${35000 - total_salary:,}")
    
    return lineup

def build_contrarian_lineup(pitcher, contrarian_gems, all_hitters):
    """Build a contrarian lineup"""
    
    print(f"\n CONTRARIAN CRUSHER LINEUP")
    print(f"Strategy: Value pitcher + low-owned gems")
    print("-" * 40)
    
    lineup = []
    remaining_salary = 35000
    
    # Start with value pitcher
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    print(f"P: {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}) - {pitcher['enhanced_projection']:.1f} pts")
    
    # Prioritize contrarian gems
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    used_players = {pitcher['Id']}
    
    for pos in positions:
        # First try contrarian gems for this position
        pos_contrarian = contrarian_gems[
            (contrarian_gems['Position'].str.contains(pos)) &
            (contrarian_gems['Salary'] <= remaining_salary) &
            (~contrarian_gems['Id'].isin(used_players))
        ]
        
        if len(pos_contrarian) > 0:
            best_player = pos_contrarian.iloc[0]
        else:
            # Fall back to best available
            best_player = find_best_for_position(pos, all_hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
            ownership = best_player.get('simulated_ownership', 10)
            print(f"{pos}: {best_player['Nickname']} {best_player['Last Name']} "
                  f"(${best_player['Salary']}, ~{ownership:.1f}% owned) - {best_player['aggressive_projection']:.1f} pts")
    
    total_salary = sum(player['Salary'] for _, player in lineup)
    total_proj = sum(player.get('aggressive_projection', player.get('enhanced_projection', 0)) for _, player in lineup)
    
    print(f"\nTotal Projection: {total_proj:.1f} points")
    print(f"Total Salary: ${total_salary:,}")
    print(f"Remaining: ${35000 - total_salary:,}")
    
    return lineup

def find_best_for_position(position, players, max_salary, used_players):
    """Find the best available player for a position"""
    
    if position == 'C':
        eligible = players[players['Position'].str.contains('C')]
    elif position in ['1B', '2B', '3B', 'SS']:
        eligible = players[players['Position'].str.contains(position)]
    elif position == 'OF':
        eligible = players[players['Position'].str.contains('OF')]
    else:
        eligible = players
    
    # Filter by salary and availability
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    # Return highest projected player
    return available.nlargest(1, 'aggressive_projection').iloc[0]

if __name__ == "__main__":
    find_tournament_gold()
