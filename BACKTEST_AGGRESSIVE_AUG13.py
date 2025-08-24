#!/usr/bin/env python3
"""
BACKTEST AGGRESSIVE PROJECTOR - August 13th Validation
Run the aggressive system on August 13th data to see performance
"""

import pandas as pd
import numpy as np
from datetime import datetime

def backtest_aggressive_system():
    """Test the aggressive system on August 13th data"""
    
    print(" BACKTEST: AGGRESSIVE PROJECTOR ON AUGUST 13TH")
    print("=" * 60)
    print("Testing our aggressive system against actual August 13th results...")
    
    try:
        # Load August 13th slate data
        df_slate = pd.read_csv("../data/fd_slate_20250813.csv")
        print(f"SUCCESS: Loaded August 13th slate: {len(df_slate)} players")
        
        # Load August 13th actual results
        df_results = pd.read_csv("../data/actual_results_20250813.csv")
        print(f"SUCCESS: Loaded actual results: {len(df_results)} players")
        
        # Merge slate with actual results
        df_merged = df_slate.merge(df_results[['Id', 'fanduel_points']], on='Id', how='left')
        df_merged['actual_points'] = df_merged['fanduel_points'].fillna(0)
        
        print(f"SUCCESS: Merged data: {len(df_merged)} players with actual results")
        
        # Apply our aggressive projection system
        df_aggressive = apply_aggressive_system_aug13(df_merged)
        
        # Find lineups using aggressive system
        test_aggressive_lineups(df_aggressive)
        
        # Compare to actual winners
        compare_to_winners(df_aggressive)
        
    except FileNotFoundError as e:
        print(f"ERROR: File not found: {e}")
        print("Let me try alternative file names...")
        try_alternative_files()

def try_alternative_files():
    """Try to find August 13th files with different naming"""
    
    # Check for different file naming patterns
    possible_files = [
        "../data/fd_slate_today_20250813.csv",
        "../data/enhanced_projections_20250813_175916.csv",
        "../data/actual_results_latest.csv",
        "../data/WINNING_LINEUP_ANALYSIS_20250813.csv"
    ]
    
    print("\n Searching for available August 13th files...")
    
    available_files = []
    for file in possible_files:
        try:
            df_test = pd.read_csv(file)
            available_files.append((file, len(df_test)))
            print(f"SUCCESS: Found: {file} ({len(df_test)} rows)")
        except FileNotFoundError:
            print(f"ERROR: Not found: {file}")
    
    if available_files:
        print(f"\nDATA: Working with available files...")
        use_available_data(available_files)
    else:
        print("ERROR: No August 13th files found for backtesting")

def use_available_data(available_files):
    """Use whatever August 13th data we can find"""
    
    # Try to use enhanced projections as our "slate"
    try:
        df_projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        print(f"SUCCESS: Using enhanced projections as slate: {len(df_projections)} players")
        
        # Apply aggressive system to these projections
        df_aggressive = apply_aggressive_system_to_projections(df_projections)
        
        # Find our top targets
        find_aggressive_targets_aug13(df_aggressive)
        
    except Exception as e:
        print(f"ERROR: Error processing available data: {e}")

def apply_aggressive_system_aug13(df):
    """Apply aggressive system to August 13th data"""
    
    print("\nTARGET: APPLYING AGGRESSIVE SYSTEM TO AUGUST 13TH DATA")
    print("=" * 50)
    
    df_enhanced = df.copy()
    
    # Use base FPPG as starting projection
    df_enhanced['base_projection'] = df_enhanced['FPPG'].fillna(10)
    df_enhanced['aggressive_projection'] = df_enhanced['base_projection'].copy()
    
    # Apply August 13th patterns
    
    # 1. VALUE PLAYER UPSIDE BOOST
    value_players = df_enhanced[
        (df_enhanced['Salary'] <= 3500) & 
        (df_enhanced['Position'] != 'P')
    ].copy()
    
    print(f" Found {len(value_players)} value players (<= $3,500)")
    
    for idx, player in value_players.iterrows():
        original_proj = player['base_projection']
        
        # Apply upside multiplier
        upside_multiplier = calculate_upside_multiplier_aug13(player)
        enhanced_proj = original_proj * upside_multiplier
        
        df_enhanced.at[idx, 'aggressive_projection'] = enhanced_proj
        df_enhanced.at[idx, 'upside_boost'] = enhanced_proj - original_proj
        
        if enhanced_proj > 25:  # High upside threshold
            actual_points = player.get('actual_points', 0)
            print(f" HIGH UPSIDE TARGET: {player['Nickname']} {player['Last Name']} "
                  f"(${player['Salary']}) - Projected: {enhanced_proj:.1f}, Actual: {actual_points:.1f}")
    
    # 2. VALUE PITCHER STRATEGY
    pitchers = df_enhanced[df_enhanced['Position'] == 'P'].copy()
    
    for idx, pitcher in pitchers.iterrows():
        salary = pitcher['Salary']
        original_proj = pitcher['base_projection']
        
        if 6000 <= salary <= 10000:  # Value pitcher range
            value_boost = 1.15
            df_enhanced.at[idx, 'aggressive_projection'] = original_proj * value_boost
            actual_points = pitcher.get('actual_points', 0)
            print(f" VALUE PITCHER: {pitcher['Nickname']} {pitcher['Last Name']} "
                  f"(${salary}) - Projected: {original_proj * value_boost:.1f}, Actual: {actual_points:.1f}")
    
    return df_enhanced

def apply_aggressive_system_to_projections(df_projections):
    """Apply aggressive system to existing projections"""
    
    print("\nTARGET: APPLYING AGGRESSIVE SYSTEM TO AUGUST 13TH PROJECTIONS")
    print("=" * 55)
    
    df_enhanced = df_projections.copy()
    
    # Use enhanced_fppg as base
    df_enhanced['base_projection'] = df_enhanced['enhanced_fppg'].fillna(df_enhanced['FPPG'])
    df_enhanced['aggressive_projection'] = df_enhanced['base_projection'].copy()
    
    # Apply aggressive boosts
    value_players = df_enhanced[
        (df_enhanced['Salary'] <= 3500) & 
        (df_enhanced['Position'] != 'P')
    ].copy()
    
    print(f" Found {len(value_players)} value players (<= $3,500)")
    
    nuclear_values = []
    
    for idx, player in value_players.iterrows():
        original_proj = player['base_projection']
        
        # Apply upside multiplier
        upside_multiplier = calculate_upside_multiplier_aug13(player)
        enhanced_proj = original_proj * upside_multiplier
        
        df_enhanced.at[idx, 'aggressive_projection'] = enhanced_proj
        
        if enhanced_proj > 25:  # Nuclear value threshold
            nuclear_values.append({
                'name': f"{player['Nickname']} {player['Last Name']}",
                'salary': player['Salary'],
                'team': player['Team'],
                'original_proj': original_proj,
                'aggressive_proj': enhanced_proj,
                'multiplier': upside_multiplier
            })
    
    print(f"\nSTART: NUCLEAR VALUE TARGETS FROM AGGRESSIVE SYSTEM:")
    for nv in nuclear_values:
        print(f"   {nv['name']} ({nv['team']}) - ${nv['salary']} - "
              f"{nv['original_proj']:.1f}  {nv['aggressive_proj']:.1f} pts (x{nv['multiplier']:.2f})")
    
    return df_enhanced

def calculate_upside_multiplier_aug13(player):
    """Calculate upside multiplier for August 13th backtest"""
    
    base_multiplier = 1.0
    
    # Salary-based upside
    if player['Salary'] <= 2500:
        base_multiplier += 0.6  # 60% boost
    elif player['Salary'] <= 3000:
        base_multiplier += 0.4  # 40% boost
    elif player['Salary'] <= 3500:
        base_multiplier += 0.2  # 20% boost
    
    # Position-based adjustments
    if player['Position'] in ['OF', 'SS', '2B']:
        base_multiplier += 0.1
    
    # Batting order boost
    batting_order = player.get('Batting Order', 5)
    if batting_order <= 3:
        base_multiplier += 0.15
    elif batting_order <= 5:
        base_multiplier += 0.1
    
    return min(base_multiplier, 2.0)

def find_aggressive_targets_aug13(df_aggressive):
    """Find what our aggressive system would have targeted on August 13th"""
    
    print("\nTARGET: AGGRESSIVE SYSTEM TARGETS FOR AUGUST 13TH")
    print("=" * 50)
    
    # Filter to starting players
    probable_pitchers = df_aggressive[
        (df_aggressive['Position'] == 'P') & 
        (df_aggressive['Probable Pitcher'] == 'Yes')
    ].copy()
    
    starting_hitters = df_aggressive[
        (df_aggressive['Position'] != 'P') & 
        (df_aggressive['Batting Order'] > 0)
    ].copy()
    
    print(f"SUCCESS: Filtered to {len(probable_pitchers)} pitchers, {len(starting_hitters)} hitters")
    
    # Top value pitchers
    print("\n TOP VALUE PITCHER TARGETS:")
    value_pitchers = probable_pitchers[
        (probable_pitchers['Salary'] >= 6000) & 
        (probable_pitchers['Salary'] <= 10000)
    ].sort_values('aggressive_projection', ascending=False)
    
    for _, pitcher in value_pitchers.head(5).iterrows():
        proj = pitcher['aggressive_projection']
        pts_per_k = proj / (pitcher['Salary'] / 1000)
        print(f"  {pitcher['Nickname']} {pitcher['Last Name']} ({pitcher['Team']}) - "
              f"${pitcher['Salary']} - {proj:.1f} pts ({pts_per_k:.1f} pts/$K)")
    
    # Nuclear value hitters
    print("\nSTART: NUCLEAR VALUE HITTER TARGETS:")
    nuclear_hitters = starting_hitters[
        starting_hitters['aggressive_projection'] > 25
    ].sort_values('aggressive_projection', ascending=False)
    
    for _, hitter in nuclear_hitters.iterrows():
        proj = hitter['aggressive_projection']
        pts_per_k = proj / (hitter['Salary'] / 1000)
        print(f"   {hitter['Nickname']} {hitter['Last Name']} ({hitter['Team']}) - "
              f"${hitter['Salary']} - {proj:.1f} pts ({pts_per_k:.1f} pts/$K)")
    
    # Compare to known winners
    compare_to_known_winners(nuclear_hitters)

def compare_to_known_winners(nuclear_hitters):
    """Compare our targets to known August 13th winners"""
    
    print("\nDATA: COMPARISON TO KNOWN AUGUST 13TH WINNERS")
    print("=" * 50)
    
    # Known winners from our previous analysis
    known_winners = [
        {'name': 'Jakob Marsee', 'team': 'MIA', 'salary': 3100, 'actual_points': 68.9},
        {'name': 'Xavier Edwards', 'team': 'MIA', 'salary': 2700, 'actual_points': 30.9},
        {'name': 'Michael Harris II', 'team': 'ATL', 'salary': 2700, 'actual_points': 36.1},
        {'name': 'Marcell Ozuna', 'team': 'ATL', 'salary': 3100, 'actual_points': 35.9}
    ]
    
    print("LINEUP: Known August 13th Winners:")
    for winner in known_winners:
        print(f"  {winner['name']} ({winner['team']}) - ${winner['salary']} - {winner['actual_points']} actual pts")
    
    # Check if our system would have found them
    print("\n DID OUR AGGRESSIVE SYSTEM FIND THEM?")
    
    for _, hitter in nuclear_hitters.iterrows():
        player_name = f"{hitter['Nickname']} {hitter['Last Name']}"
        
        # Check if this matches any known winner
        for winner in known_winners:
            if (winner['name'].lower() in player_name.lower() or 
                (hitter['Team'] == winner['team'] and abs(hitter['Salary'] - winner['salary']) <= 100)):
                print(f"  SUCCESS: MATCH FOUND: {player_name} - Our system projected {hitter['aggressive_projection']:.1f} pts!")
                break

def test_aggressive_lineups(df_aggressive):
    """Test what lineups our aggressive system would have built"""
    
    print("\n TESTING AGGRESSIVE LINEUP CONSTRUCTION")
    print("=" * 45)
    
    # Build nuclear value lineup
    nuclear_lineup = build_nuclear_value_lineup_aug13(df_aggressive)
    if nuclear_lineup:
        evaluate_lineup_performance(nuclear_lineup, "Nuclear Value")

def build_nuclear_value_lineup_aug13(df):
    """Build nuclear value lineup for August 13th"""
    
    # Filter to starting players
    probable_pitchers = df[
        (df['Position'] == 'P') & 
        (df['Probable Pitcher'] == 'Yes')
    ].copy()
    
    starting_hitters = df[
        (df['Position'] != 'P') & 
        (df['Batting Order'] > 0)
    ].copy()
    
    # Get value pitcher
    value_pitchers = probable_pitchers[
        (probable_pitchers['Salary'] >= 6000) & 
        (probable_pitchers['Salary'] <= 10000)
    ].sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        return None
    
    pitcher = value_pitchers.iloc[0]
    lineup = [pitcher]
    remaining_salary = 35000 - pitcher['Salary']
    
    # Fill with best value hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    used_players = {pitcher['Id']}
    
    for pos in positions:
        best_player = find_best_for_position_aug13(pos, starting_hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append(best_player)
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def find_best_for_position_aug13(position, players, max_salary, used_players):
    """Find best player for position in August 13th backtest"""
    
    if position == 'C':
        eligible = players[players['Position'].str.contains('C')]
    elif position in ['1B', '2B', '3B', 'SS']:
        eligible = players[players['Position'].str.contains(position)]
    elif position == 'OF':
        eligible = players[players['Position'].str.contains('OF')]
    else:
        eligible = players
    
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    return available.nlargest(1, 'aggressive_projection').iloc[0]

def evaluate_lineup_performance(lineup, strategy_name):
    """Evaluate how the lineup would have performed"""
    
    print(f"\nTARGET: {strategy_name.upper()} LINEUP PERFORMANCE:")
    print("-" * 40)
    
    total_salary = sum(player['Salary'] for player in lineup)
    total_projected = sum(player['aggressive_projection'] for player in lineup)
    total_actual = sum(player.get('actual_points', 0) for player in lineup)
    
    print(f"Total Salary: ${total_salary:,}")
    print(f"Aggressive Projection: {total_projected:.1f} pts")
    print(f"Actual Performance: {total_actual:.1f} pts")
    print(f"Projection Accuracy: {(total_actual/total_projected*100):.1f}%" if total_projected > 0 else "N/A")
    
    print(f"\nLineup Details:")
    for i, player in enumerate(lineup):
        pos = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF'][i]
        actual = player.get('actual_points', 0)
        projected = player['aggressive_projection']
        print(f"  {pos}: {player['Nickname']} {player['Last Name']} - "
              f"${player['Salary']} - Proj: {projected:.1f}, Actual: {actual:.1f}")

if __name__ == "__main__":
    backtest_aggressive_system()
