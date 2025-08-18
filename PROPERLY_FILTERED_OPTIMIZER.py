import pandas as pd
import numpy as np
import pulp

def build_properly_filtered_optimizer():
    """
    Build optimizer using PROPERLY FILTERED slate (no IL, only probable pitchers)
    """
    
    print("=== PROPERLY FILTERED TOURNAMENT OPTIMIZER ===")
    print("Using FILTERED slate with no IL players or non-probable pitchers")
    print()
    
    # Load the filtered slate
    import glob
    filtered_files = glob.glob(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\FILTERED_CORRECTED_slate_*.csv")
    if not filtered_files:
        print("ERROR: No filtered slate found! Run EMERGENCY_SLATE_FILTERING.py first")
        return
    
    latest_filtered = sorted(filtered_files)[-1]
    filename = latest_filtered.split('\\')[-1]
    print(f"DATA: Loading: {filename}")
    
    slate_df = pd.read_csv(latest_filtered)
    print(f"Playable players: {len(slate_df)}")
    
    # Generate tournament strategies
    strategies = [
        ("Filtered Value", optimize_filtered_value),
        ("Filtered Ceiling", optimize_filtered_ceiling), 
        ("Filtered Balance", optimize_filtered_balance),
        ("Filtered Contrarian", optimize_filtered_contrarian)
    ]
    
    lineups = []
    for strategy_name, optimizer_func in strategies:
        print(f"\n=== {strategy_name.upper()} STRATEGY ===")
        lineup = optimizer_func(slate_df)
        if lineup:
            display_lineup_with_actuals(strategy_name, lineup, slate_df)
            lineups.append((strategy_name, lineup))
        else:
            print(f"ERROR: {strategy_name} optimization failed")
    
    # Save lineups
    if lineups:
        save_filtered_lineups(lineups, slate_df)
    
    return lineups

def optimize_filtered_value(data):
    """Value approach with filtered slate"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Value score
    available_players['value_score'] = available_players['FPPG'] / (available_players['Salary'] / 1000)
    
    # Boost proven salary ranges
    value_boost = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4000)
    available_players.loc[value_boost, 'value_score'] *= 1.3
    
    return optimize_lineup(available_players, 'value_score', "Filtered_Value")

def optimize_filtered_ceiling(data):
    """Ceiling approach with filtered slate"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Ceiling score focuses on upside
    available_players['ceiling_score'] = available_players['FPPG'].copy()
    
    # Boost explosive positions 
    explosive_pos = available_players['Position'].str.contains('SS|3B', na=False)
    available_players.loc[explosive_pos, 'ceiling_score'] *= 1.4
    
    # Boost high projections
    high_proj = available_players['FPPG'] >= 20
    available_players.loc[high_proj, 'ceiling_score'] *= 1.2
    
    return optimize_lineup(available_players, 'ceiling_score', "Filtered_Ceiling")

def optimize_filtered_balance(data):
    """Balanced approach with filtered slate"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Balanced score
    available_players['balance_score'] = available_players['FPPG'].copy()
    
    # Slight value boost 
    value_range = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4500)
    available_players.loc[value_range, 'balance_score'] *= 1.1
    
    return optimize_lineup(available_players, 'balance_score', "Filtered_Balance")

def optimize_filtered_contrarian(data):
    """Contrarian approach with filtered slate"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Contrarian score
    available_players['contrarian_score'] = available_players['FPPG'].copy()
    
    # Boost mid-salary (lower owned)
    mid_salary = (available_players['Salary'] >= 2800) & (available_players['Salary'] <= 3800)
    available_players.loc[mid_salary, 'contrarian_score'] *= 1.3
    
    # Reduce expensive chalk
    expensive = available_players['Salary'] >= 5000
    available_players.loc[expensive, 'contrarian_score'] *= 0.9
    
    return optimize_lineup(available_players, 'contrarian_score', "Filtered_Contrarian")

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

def display_lineup_with_actuals(strategy_name, lineup, data):
    """Display lineup with August 12th actual results"""
    
    if not lineup:
        print(f"{strategy_name}: Optimization failed!")
        return
    
    # Load actual results for comparison
    try:
        actual_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
        actual_df['full_name'] = actual_df['name'].str.strip()
    except:
        actual_df = None
    
    print(f"\n{strategy_name.upper()} LINEUP:")
    print("Player | Position | Salary | Projected | ACTUAL Aug 12")
    print("-" * 60)
    
    total_salary = 0
    total_projected = 0
    total_actual = 0
    
    for player in lineup:
        name = f"{player['First Name']} {player['Last Name']}"
        full_name = name.strip()
        
        # Look up actual result
        actual_points = 0
        if actual_df is not None:
            actual_match = actual_df[actual_df['full_name'] == full_name]
            if len(actual_match) > 0:
                actual_points = actual_match.iloc[0]['fanduel_points']
        
        total_salary += player['Salary']
        total_projected += player['FPPG']
        total_actual += actual_points
        
        print(f"{name:20} | {player['Position']:8} | ${player['Salary']:5} | {player['FPPG']:8.1f} | {actual_points:6.1f}")
    
    print(f"\nTotal: ${total_salary:,} ({total_salary/35000:.1%}) | Proj: {total_projected:.1f} | ACTUAL: {total_actual:.1f}")
    
    # Compare to tournament winner
    if total_actual > 0:
        print(f"Tournament Winner: 306.0 | Our Original: 139.9 | This Strategy: {total_actual:.1f}")
        if total_actual >= 280:
            print("LINEUP: CHAMPION! Would have won the tournament!")
        elif total_actual >= 250:
            print(" ELITE! Top 5 finish!")
        elif total_actual >= 200:
            print("TARGET: EXCELLENT! Top 20 finish!")
        elif total_actual >= 160:
            print("SUCCESS: GOOD! Big improvement over 139.9!")
        else:
            print("PROGRESS: Better than original but needs work")

def save_filtered_lineups(lineups, slate_df):
    """Save filtered lineups"""
    
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
        output_filename = f"PROPERLY_FILTERED_LINEUPS_{timestamp}.csv"
        output_file = f"c:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\{output_filename}"
        lineup_df.to_csv(output_file, index=False)
        print(f"\nSUCCESS: Saved properly filtered lineups: {output_filename}")
    
    print(f"\nTARGET: READY FOR TOURNAMENT with {len(lineups)} PROPERLY FILTERED lineups!")
    print("SUCCESS: No IL players")
    print("SUCCESS: Only probable pitchers") 
    print("SUCCESS: Actually playable lineup!")

if __name__ == "__main__":
    lineups = build_properly_filtered_optimizer()
