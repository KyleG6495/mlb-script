import pandas as pd
import numpy as np
import pulp
from config import FilePaths
import glob

def build_corrected_tournament_optimizer():
    """
    Build tournament optimizer using CORRECTED projections from August 12th learnings
    """
    
    print("=== CORRECTED TOURNAMENT OPTIMIZER ===")
    print("Using CORRECTED projections based on August 12th analysis")
    print()
    
    # Load the corrected slate (most recent)
    corrected_files = glob.glob(str(FilePaths.DATA_DIR / "CORRECTED_slate_*.csv"))
    if not corrected_files:
        print("ERROR: No corrected slate found! Run CRITICAL_PROJECTION_FIXES.py first")
        return
    
    latest_corrected = sorted(corrected_files)[-1]
    filename = latest_corrected.split('\\')[-1]
    print(f"DATA: Loading: {filename}")
    
    slate_df = pd.read_csv(latest_corrected)
    print(f"Players available: {len(slate_df)}")
    
    # Generate multiple tournament strategies
    strategies = [
        ("Smart Value", optimize_smart_value),
        ("Tournament Ceiling", optimize_tournament_ceiling), 
        ("Balanced Corrected", optimize_balanced_corrected),
        ("Anti-Chalk", optimize_anti_chalk),
        ("Pure Upside", optimize_pure_upside)
    ]
    
    lineups = []
    for strategy_name, optimizer_func in strategies:
        print(f"\n=== {strategy_name.upper()} STRATEGY ===")
        lineup = optimizer_func(slate_df)
        if lineup:
            display_lineup(strategy_name, lineup, slate_df)
            lineups.append((strategy_name, lineup))
        else:
            print(f"ERROR: {strategy_name} optimization failed")
    
    # Save all lineups
    if lineups:
        save_tournament_lineups(lineups, slate_df)
    
    return lineups

def optimize_smart_value(data):
    """Smart value approach based on August 12th learnings"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Create smart value score
    available_players['value_score'] = available_players['FPPG'] / (available_players['Salary'] / 1000)
    available_players['smart_score'] = available_players['FPPG'].copy()
    
    # August 12th learnings: Boost $3K-4K range
    value_range = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4000)
    available_players.loc[value_range, 'smart_score'] *= 1.4
    
    # Boost high-value plays
    high_value = available_players['value_score'] >= 4.0
    available_players.loc[high_value, 'smart_score'] *= 1.3
    
    # Avoid expensive busts
    expensive_pitchers = (available_players['Position'] == 'P') & (available_players['Salary'] >= 9500)
    available_players.loc[expensive_pitchers, 'smart_score'] *= 0.6
    
    return optimize_lineup(available_players, 'smart_score', "Smart_Value")

def optimize_tournament_ceiling(data):
    """Focus on pure ceiling/upside for tournaments"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Ceiling score focuses on upside
    available_players['ceiling_score'] = available_players['FPPG'].copy()
    
    # Massive boost for explosive positions (SS/3B)
    explosive_pos = available_players['Position'].str.contains('SS|3B', na=False)
    available_players.loc[explosive_pos, 'ceiling_score'] *= 1.5
    
    # Boost players with high raw projections
    high_proj = available_players['FPPG'] >= 15
    available_players.loc[high_proj, 'ceiling_score'] *= 1.3
    
    # Target mid-range pitchers for value
    mid_pitchers = (available_players['Position'] == 'P') & (available_players['Salary'] >= 7000) & (available_players['Salary'] < 9500)
    available_players.loc[mid_pitchers, 'ceiling_score'] *= 1.2
    
    return optimize_lineup(available_players, 'ceiling_score', "Tournament_Ceiling")

def optimize_balanced_corrected(data):
    """Balanced approach using corrected projections"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Use corrected projections as-is but with slight tweaks
    available_players['balanced_score'] = available_players['FPPG'].copy()
    
    # Slight boost to proven value ranges
    proven_value = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4500)
    available_players.loc[proven_value, 'balanced_score'] *= 1.1
    
    return optimize_lineup(available_players, 'balanced_score', "Balanced_Corrected")

def optimize_anti_chalk(data):
    """Target low-owned players with upside"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Anti-chalk score
    available_players['anti_chalk_score'] = available_players['FPPG'].copy()
    
    # Boost mid-salary players (typically lower owned)
    mid_salary = (available_players['Salary'] >= 2800) & (available_players['Salary'] <= 3800)
    available_players.loc[mid_salary, 'anti_chalk_score'] *= 1.3
    
    # Avoid obvious studs
    expensive_studs = available_players['Salary'] >= 5000
    available_players.loc[expensive_studs, 'anti_chalk_score'] *= 0.8
    
    return optimize_lineup(available_players, 'anti_chalk_score', "Anti_Chalk")

def optimize_pure_upside(data):
    """Maximum upside hunting"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Pure upside score
    available_players['upside_score'] = available_players['FPPG'].copy()
    
    # Huge boost for $3K-4K (where explosions happened)
    explosion_range = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4000)
    available_players.loc[explosion_range, 'upside_score'] *= 2.0
    
    # Target power positions
    power_pos = available_players['Position'].str.contains('SS|3B|OF', na=False)
    available_players.loc[power_pos, 'upside_score'] *= 1.2
    
    return optimize_lineup(available_players, 'upside_score', "Pure_Upside")

def optimize_lineup(available_players, score_column, lineup_name):
    """Generic lineup optimization"""
    
    # Set up optimization
    prob = pulp.LpProblem(lineup_name, pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize score
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, score_column] for i in range(len(available_players))])
    
    # Salary constraints
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) <= 35000
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) >= 34000
    
    # Position constraints
    def can_play_position(player_pos, needed_pos):
        if needed_pos == 'UTIL':
            return any(pos in str(player_pos) for pos in ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH'])
        elif needed_pos == 'C/1B':
            return any(pos in str(player_pos) for pos in ['C', '1B'])
        else:
            return needed_pos in str(player_pos)
    
    # Position requirements
    positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
    
    for pos in positions_needed:
        eligible_indices = [i for i in range(len(available_players)) 
                          if can_play_position(available_players.loc[i, 'Position'], pos)]
        if eligible_indices:
            prob += pulp.lpSum([player_vars[i] for i in eligible_indices]) >= 1
    
    # Total players = 9
    prob += pulp.lpSum(player_vars) == 9
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        selected_players = []
        for i in range(len(available_players)):
            if player_vars[i].value() == 1:
                selected_players.append(available_players.loc[i])
        return selected_players
    return None

def display_lineup(strategy_name, lineup, data):
    """Display lineup results"""
    
    if not lineup:
        print(f"{strategy_name}: Optimization failed!")
        return
    
    print(f"\n{strategy_name.upper()} LINEUP:")
    print("Player | Position | Salary | Corrected Proj | Original Proj")
    print("-" * 65)
    
    total_salary = 0
    total_corrected = 0
    total_original = 0
    
    for player in lineup:
        name = f"{player['First Name']} {player['Last Name']}"
        total_salary += player['Salary']
        total_corrected += player['FPPG']
        total_original += player.get('original_fppg', player['FPPG'])
        
        print(f"{name:20} | {player['Position']:8} | ${player['Salary']:5} | {player['FPPG']:8.1f} | {player.get('original_fppg', player['FPPG']):8.1f}")
    
    print(f"\nTotal: ${total_salary:,} ({total_salary/35000:.1%}) | Corrected: {total_corrected:.1f} | Original: {total_original:.1f}")
    print(f"Improvement: {total_corrected - total_original:+.1f} points from corrections")

def save_tournament_lineups(lineups, slate_df):
    """Save all lineups to files"""
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed lineups
    all_lineups = []
    for strategy_name, lineup in lineups:
        for i, player in enumerate(lineup):
            player_data = player.copy()
            player_data['Strategy'] = strategy_name
            player_data['Lineup_Position'] = i + 1
            all_lineups.append(player_data)
    
    if all_lineups:
        lineup_df = pd.DataFrame(all_lineups)
        output_filename = f"CORRECTED_TOURNAMENT_LINEUPS_{timestamp}.csv"
        output_file = FilePaths.DATA_DIR / output_filename
        lineup_df.to_csv(output_file, index=False)
        print(f"\nSUCCESS: Saved all lineups to: {output_filename}")
    
    print(f"\nSTART: READY FOR TOURNAMENT with {len(lineups)} optimized lineups!")
    print("Each lineup uses CORRECTED projections based on August 12th learnings")

if __name__ == "__main__":
    lineups = build_corrected_tournament_optimizer()
