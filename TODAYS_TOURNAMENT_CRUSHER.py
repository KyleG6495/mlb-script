#!/usr/bin/env python3
"""
TODAY'S TOURNAMENT CRUSHER
Using aggressive patterns on today's confirmed lineup data
"""

import pandas as pd
import numpy as np
from datetime import datetime

def crush_todays_tournament():
    """Build tournament crushing lineups for today using aggressive patterns"""
    
    print("START: TODAY'S TOURNAMENT CRUSHER - August 14th")
    print("=" * 60)
    print("Applying August 13th winning patterns to today's confirmed lineups...")
    
    try:
        # Load today's aggressive projections (we created this earlier)
        df = pd.read_csv("../data/aggressive_upside_projections_20250814_094533.csv")
        print(f"SUCCESS: Loaded today's aggressive projections: {len(df)} players")
        
        # Filter to confirmed starting players ONLY
        confirmed_pitchers = df[
            (df['Position'] == 'P') & 
            (df['Probable Pitcher'] == 'Yes') &
            (df['Injury Indicator'].isna() | (df['Injury Indicator'] == ''))
        ].copy()
        
        confirmed_hitters = df[
            (df['Position'] != 'P') & 
            (df['Batting Order'] > 0) &
            (df['Injury Indicator'].isna() | (df['Injury Indicator'] == ''))
        ].copy()
        
        print(f"TARGET: Confirmed starters: {len(confirmed_pitchers)} pitchers, {len(confirmed_hitters)} hitters")
        
        # Apply aggressive targeting
        find_todays_gold(confirmed_pitchers, confirmed_hitters)
        
        # Build multiple tournament lineups
        build_tournament_arsenal(confirmed_pitchers, confirmed_hitters)
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

def find_todays_gold(pitchers, hitters):
    """Find today's tournament gold using confirmed data"""
    
    print(f"\n TODAY'S TOURNAMENT GOLD TARGETS")
    print("=" * 40)
    
    # VALUE PITCHER STRATEGY (August 13th pattern)
    print(f"\n VALUE PITCHER TARGETS ($6K-$10K):")
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].copy()
    
    # Fill NaN aggressive projections with enhanced projections
    value_pitchers['aggressive_projection'] = value_pitchers['aggressive_projection'].fillna(
        value_pitchers['enhanced_projection']
    )
    
    value_pitchers = value_pitchers.sort_values('aggressive_projection', ascending=False)
    
    for _, pitcher in value_pitchers.head(5).iterrows():
        proj = pitcher['aggressive_projection']
        pts_per_k = proj / (pitcher['Salary'] / 1000) if proj > 0 else 0
        print(f"  TARGET: {pitcher['Nickname']} {pitcher['Last Name']} ({pitcher['Team']} vs {pitcher['Opponent']})")
        print(f"      ${pitcher['Salary']} - {proj:.1f} pts ({pts_per_k:.1f} pts/$K)")
    
    # NUCLEAR VALUE HITTERS (Jakob Marsee pattern)
    print(f"\nSTART: NUCLEAR VALUE HITTERS (<$3,500):")
    nuclear_candidates = hitters[hitters['Salary'] <= 3500].copy()
    
    # Fill NaN aggressive projections
    nuclear_candidates['aggressive_projection'] = nuclear_candidates['aggressive_projection'].fillna(
        nuclear_candidates['enhanced_projection']
    )
    
    nuclear_candidates['pts_per_k'] = nuclear_candidates['aggressive_projection'] / (nuclear_candidates['Salary'] / 1000)
    nuclear_gold = nuclear_candidates[nuclear_candidates['aggressive_projection'] >= 20].sort_values('pts_per_k', ascending=False)
    
    for _, hitter in nuclear_gold.head(8).iterrows():
        print(f"   {hitter['Nickname']} {hitter['Last Name']} ({hitter['Team']} vs {hitter['Opponent']})")
        print(f"      ${hitter['Salary']} - {hitter['aggressive_projection']:.1f} pts ({hitter['pts_per_k']:.1f} pts/$K)")
        print(f"      Batting Order: {hitter['Batting Order']}")
    
    # GAME STACKING OPPORTUNITIES
    print(f"\n GAME STACKING OPPORTUNITIES:")
    find_stack_targets(hitters)
    
    # CONTRARIAN GEMS
    print(f"\n CONTRARIAN GEMS (Low ownership + upside):")
    contrarian_gems = hitters[
        (hitters['simulated_ownership'] < 8) & 
        (hitters['aggressive_projection'] >= 15)
    ].sort_values('aggressive_projection', ascending=False)
    
    for _, gem in contrarian_gems.head(6).iterrows():
        ownership = gem['simulated_ownership']
        proj = gem['aggressive_projection']
        print(f"   {gem['Nickname']} {gem['Last Name']} ({gem['Team']} vs {gem['Opponent']})")
        print(f"      ${gem['Salary']} - {proj:.1f} pts (~{ownership:.1f}% owned)")

def find_stack_targets(hitters):
    """Find the best stacking opportunities"""
    
    # Calculate team projections
    team_stats = hitters.groupby(['Team', 'Game']).agg({
        'aggressive_projection': ['sum', 'mean', 'count'],
        'Salary': 'mean'
    }).round(1)
    
    team_stats.columns = ['Total_Proj', 'Avg_Proj', 'Player_Count', 'Avg_Salary']
    
    # Only teams with 4+ players (stackable)
    stackable_teams = team_stats[team_stats['Player_Count'] >= 4].sort_values('Avg_Proj', ascending=False)
    
    print(f"  Top Stacking Targets:")
    for (team, game), stats in stackable_teams.head(5).iterrows():
        print(f"    {team} ({game}): {stats['Avg_Proj']:.1f} avg proj, {int(stats['Player_Count'])} players")
    
    # Show top team stack details
    if len(stackable_teams) > 0:
        top_team = stackable_teams.index[0][0]  # Get team name from tuple
        top_team_players = hitters[hitters['Team'] == top_team].sort_values('aggressive_projection', ascending=False)
        
        print(f"\n   {top_team} Stack Options:")
        for _, player in top_team_players.head(5).iterrows():
            print(f"    {player['Nickname']} {player['Last Name']} (${player['Salary']}) - {player['aggressive_projection']:.1f} pts")

def build_tournament_arsenal(pitchers, hitters):
    """Build multiple tournament lineup strategies"""
    
    print(f"\n BUILDING TOURNAMENT LINEUP ARSENAL")
    print("=" * 45)
    
    # Strategy 1: Nuclear Value Lineup
    print(f"\nSTART: STRATEGY 1: NUCLEAR VALUE LINEUP")
    print("-" * 35)
    nuclear_lineup = build_nuclear_value_lineup(pitchers, hitters)
    
    # Strategy 2: Game Stack Lineup  
    print(f"\n STRATEGY 2: GAME STACK LINEUP")
    print("-" * 32)
    stack_lineup = build_stack_lineup(pitchers, hitters)
    
    # Strategy 3: Contrarian Crusher
    print(f"\n STRATEGY 3: CONTRARIAN CRUSHER")
    print("-" * 31)
    contrarian_lineup = build_contrarian_lineup(pitchers, hitters)
    
    # Save all lineups
    save_tournament_lineups([
        ('Nuclear Value', nuclear_lineup),
        ('Game Stack', stack_lineup), 
        ('Contrarian Crusher', contrarian_lineup)
    ])

def build_nuclear_value_lineup(pitchers, hitters):
    """Build nuclear value lineup (Jakob Marsee strategy)"""
    
    # Get best value pitcher
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].copy()
    value_pitchers['aggressive_projection'] = value_pitchers['aggressive_projection'].fillna(value_pitchers['enhanced_projection'])
    value_pitchers = value_pitchers.sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        print("ERROR: No value pitchers available")
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with value pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    print(f"P: {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}) - {pitcher['aggressive_projection']:.1f} pts")
    
    # Fill with nuclear value hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_value_for_position(pos, hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
            proj = best_player.get('aggressive_projection', best_player.get('enhanced_projection', 0))
            print(f"{pos}: {best_player['Nickname']} {best_player['Last Name']} (${best_player['Salary']}) - {proj:.1f} pts")
    
    display_lineup_totals(lineup, "Nuclear Value")
    return lineup

def build_stack_lineup(pitchers, hitters):
    """Build game stack lineup"""
    
    # Find best stacking team
    team_projections = hitters.groupby('Team')['aggressive_projection'].agg(['sum', 'count', 'mean'])
    stackable_teams = team_projections[team_projections['count'] >= 4].sort_values('mean', ascending=False)
    
    if len(stackable_teams) == 0:
        print("ERROR: No stackable teams found")
        return None
    
    best_team = stackable_teams.index[0]
    
    # Get value pitcher (not from stack team)
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000) &
        (pitchers['Team'] != best_team)
    ].copy()
    value_pitchers['aggressive_projection'] = value_pitchers['aggressive_projection'].fillna(value_pitchers['enhanced_projection'])
    value_pitchers = value_pitchers.sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        print("ERROR: No suitable value pitchers for stack")
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    print(f"P: {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}) - {pitcher['aggressive_projection']:.1f} pts")
    print(f"Stacking: {best_team}")
    
    # Fill with stack team players first, then others
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    stack_players = hitters[hitters['Team'] == best_team].sort_values('aggressive_projection', ascending=False)
    
    for pos in positions:
        # Try stack team first
        stack_option = find_player_for_position(pos, stack_players, remaining_salary, used_players)
        if stack_option is not None:
            best_player = stack_option
        else:
            # Fall back to any team
            best_player = find_best_value_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
            proj = best_player.get('aggressive_projection', best_player.get('enhanced_projection', 0))
            team_indicator = "" if best_player['Team'] == best_team else ""
            print(f"{pos}: {best_player['Nickname']} {best_player['Last Name']} {team_indicator} (${best_player['Salary']}) - {proj:.1f} pts")
    
    display_lineup_totals(lineup, "Game Stack")
    return lineup

def build_contrarian_lineup(pitchers, hitters):
    """Build contrarian lineup (low ownership)"""
    
    # Get value pitcher with low ownership
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].copy()
    value_pitchers['aggressive_projection'] = value_pitchers['aggressive_projection'].fillna(value_pitchers['enhanced_projection'])
    value_pitchers = value_pitchers.sort_values(['simulated_ownership', 'aggressive_projection'], ascending=[True, False])
    
    if len(value_pitchers) == 0:
        print("ERROR: No value pitchers available")
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with contrarian pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    ownership = pitcher.get('simulated_ownership', 10)
    print(f"P: {pitcher['Nickname']} {pitcher['Last Name']} (${pitcher['Salary']}, ~{ownership:.1f}% owned) - {pitcher['aggressive_projection']:.1f} pts")
    
    # Fill with contrarian hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_contrarian_for_position(pos, hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
            proj = best_player.get('aggressive_projection', best_player.get('enhanced_projection', 0))
            ownership = best_player.get('simulated_ownership', 10)
            print(f"{pos}: {best_player['Nickname']} {best_player['Last Name']} (${best_player['Salary']}, ~{ownership:.1f}% owned) - {proj:.1f} pts")
    
    display_lineup_totals(lineup, "Contrarian Crusher")
    return lineup

def find_best_value_for_position(position, players, max_salary, used_players):
    """Find best value player for position"""
    
    eligible = get_eligible_players(position, players)
    available = filter_available_players(eligible, max_salary, used_players)
    
    if len(available) == 0:
        return None
    
    # Fill NaN projections
    available['aggressive_projection'] = available['aggressive_projection'].fillna(available['enhanced_projection'])
    
    # Sort by value (projection / salary)
    available['value_score'] = available['aggressive_projection'] / (available['Salary'] / 1000)
    return available.nlargest(1, 'value_score').iloc[0]

def find_best_contrarian_for_position(position, players, max_salary, used_players):
    """Find best contrarian player for position"""
    
    eligible = get_eligible_players(position, players)
    available = filter_available_players(eligible, max_salary, used_players)
    
    if len(available) == 0:
        return None
    
    # Fill NaN projections
    available['aggressive_projection'] = available['aggressive_projection'].fillna(available['enhanced_projection'])
    
    # Sort by low ownership + high projection
    available['contrarian_score'] = available['aggressive_projection'] / (available['simulated_ownership'] + 1)
    return available.nlargest(1, 'contrarian_score').iloc[0]

def find_player_for_position(position, players, max_salary, used_players):
    """Find any player for position from specific player pool"""
    
    eligible = get_eligible_players(position, players)
    available = filter_available_players(eligible, max_salary, used_players)
    
    if len(available) == 0:
        return None
    
    # Fill NaN projections
    available['aggressive_projection'] = available['aggressive_projection'].fillna(available['enhanced_projection'])
    
    return available.nlargest(1, 'aggressive_projection').iloc[0]

def get_eligible_players(position, players):
    """Get players eligible for position"""
    
    if position == 'C':
        return players[players['Position'].str.contains('C', na=False)]
    elif position in ['1B', '2B', '3B', 'SS']:
        return players[players['Position'].str.contains(position, na=False)]
    elif position == 'OF':
        return players[players['Position'].str.contains('OF', na=False)]
    else:
        return players

def filter_available_players(players, max_salary, used_players):
    """Filter players by salary and availability"""
    
    return players[
        (players['Salary'] <= max_salary) &
        (~players['Id'].isin(used_players))
    ]

def display_lineup_totals(lineup, strategy_name):
    """Display lineup totals"""
    
    if not lineup:
        print(f"ERROR: Could not build {strategy_name} lineup")
        return
    
    total_salary = sum(player['Salary'] for _, player in lineup)
    total_projection = 0
    
    for _, player in lineup:
        proj = player.get('aggressive_projection', player.get('enhanced_projection', 0))
        if pd.notna(proj):
            total_projection += proj
    
    print(f"\nMONEY: {strategy_name} Totals:")
    print(f"   Salary: ${total_salary:,} (${35000-total_salary:,} remaining)")
    print(f"   Projection: {total_projection:.1f} points")
    
    if total_projection >= 180:
        print(f"   TARGET: STRONG tournament potential!")
    elif total_projection >= 150:
        print(f"   MONEY: Good cash game potential")
    else:
        print(f"   WARNING:  May need adjustments")

def save_tournament_lineups(lineups):
    """Save tournament lineups to file"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/tournament_crusher_lineups_{timestamp}.csv"
    
    all_lineups = []
    for strategy, lineup in lineups:
        if lineup:
            for i, (pos, player) in enumerate(lineup):
                proj = player.get('aggressive_projection', player.get('enhanced_projection', 0))
                ownership = player.get('simulated_ownership', 10)
                
                all_lineups.append({
                    'Strategy': strategy,
                    'Position': pos,
                    'Player_Id': player['Id'],
                    'Name': f"{player['Nickname']} {player['Last Name']}",
                    'Team': player['Team'],
                    'Opponent': player['Opponent'],
                    'Salary': player['Salary'],
                    'Projection': proj,
                    'Ownership': ownership,
                    'Game': player['Game']
                })
    
    if all_lineups:
        df_output = pd.DataFrame(all_lineups)
        df_output.to_csv(output_file, index=False)
        print(f"\n Saved tournament lineups: {output_file}")
        print(f"   DATA: {len([l for _, l in lineups if l])} complete lineups ready for entry!")

if __name__ == "__main__":
    crush_todays_tournament()
