import pandas as pd
import numpy as np
import pulp

def build_perfect_august_12_optimizer():
    """
    Build the PERFECT optimizer for August 12th's slate using actual results
    This will show us exactly what strategy would have won
    """
    
    print("=== PERFECT AUGUST 12TH OPTIMIZER ===")
    print("Building the winning strategy for August 12th's slate...")
    print()
    
    # Load August 12th slate
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv"
    slate_df = pd.read_csv(slate_file)
    
    # Load actual results
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    # Merge slate with actual results
    actual_results['full_name'] = actual_results['name'].str.strip()
    slate_df['full_name'] = (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.strip()
    
    merged_data = slate_df.merge(
        actual_results[['full_name', 'fanduel_points']], 
        on='full_name', 
        how='left'
    )
    merged_data['actual_fppg'] = merged_data['fanduel_points'].fillna(0)
    
    print(f"Loaded {len(slate_df)} players from August 12th slate")
    print(f"Matched {len(merged_data[merged_data['actual_fppg'] > 0])} players with actual results")
    
    # Now build multiple optimization strategies using actual results
    
    # Strategy 1: Pure actual results (the "answer key")
    print("\n=== STRATEGY 1: PERFECT HINDSIGHT ===")
    perfect_lineup = optimize_with_actual_results(merged_data, use_actual=True)
    display_lineup("PERFECT HINDSIGHT", perfect_lineup, merged_data)
    
    # Strategy 2: Hybrid approach using projections but learning from patterns
    print("\n=== STRATEGY 2: HYBRID SMART ===")
    hybrid_lineup = optimize_with_hybrid_approach(merged_data)
    display_lineup("HYBRID SMART", hybrid_lineup, merged_data)
    
    # Strategy 3: Value-focused with ceiling boost
    print("\n=== STRATEGY 3: VALUE + CEILING ===")
    value_lineup = optimize_value_ceiling(merged_data)
    display_lineup("VALUE + CEILING", value_lineup, merged_data)
    
    # Strategy 4: Target the actual winners
    print("\n=== STRATEGY 4: TARGET WINNERS ===")
    winner_lineup = optimize_targeting_winners(merged_data)
    display_lineup("TARGET WINNERS", winner_lineup, merged_data)

def optimize_with_actual_results(data, use_actual=True):
    """Optimize using actual results as the objective"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    
    # Clean data first
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Set up optimization
    prob = pulp.LpProblem("Perfect_Hindsight", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize actual points
    if use_actual:
        prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'actual_fppg'] for i in range(len(available_players))])
    else:
        prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'FPPG'] for i in range(len(available_players))])
    
    # Add constraints
    add_standard_constraints(prob, player_vars, available_players)
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        return get_selected_players(player_vars, available_players)
    return None

def optimize_with_hybrid_approach(data):
    """Optimize using lessons learned from actual results"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    
    # Clean data first
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Create hybrid score based on patterns we discovered
    available_players['hybrid_score'] = available_players['FPPG'].copy()
    
    # Boost players in the $3000-4000 range (where most top performers were)
    mid_range = (available_players['Salary'] >= 3000) & (available_players['Salary'] <= 4000)
    available_players.loc[mid_range, 'hybrid_score'] *= 1.3
    
    # Boost SS and 3B positions (where explosions happened)
    explosive_pos = available_players['Position'].isin(['SS', '3B'])
    available_players.loc[explosive_pos, 'hybrid_score'] *= 1.2
    
    # Boost mid-range pitchers ($7000-9000) and penalize expensive ones
    mid_pitchers = (available_players['Position'] == 'P') & (available_players['Salary'] >= 7000) & (available_players['Salary'] <= 9000)
    expensive_pitchers = (available_players['Position'] == 'P') & (available_players['Salary'] >= 10500)
    
    available_players.loc[mid_pitchers, 'hybrid_score'] *= 1.4
    available_players.loc[expensive_pitchers, 'hybrid_score'] *= 0.7
    
    # Set up optimization
    prob = pulp.LpProblem("Hybrid_Smart", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize hybrid score
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'hybrid_score'] for i in range(len(available_players))])
    
    # Add constraints
    add_standard_constraints(prob, player_vars, available_players)
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        return get_selected_players(player_vars, available_players)
    return None

def optimize_value_ceiling(data):
    """Focus on value plays with ceiling upside"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    
    # Clean data first
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Create value-ceiling score
    available_players['value_score'] = available_players['FPPG'] / (available_players['Salary'] / 1000)
    available_players['ceiling_score'] = available_players['FPPG'].copy()
    
    # Boost high-value low-salary plays
    high_value = available_players['value_score'] >= 4
    available_players.loc[high_value, 'ceiling_score'] *= 1.3
    
    # Boost players with high projections
    high_proj = available_players['FPPG'] >= 20
    available_players.loc[high_proj, 'ceiling_score'] *= 1.2
    
    # Set up optimization
    prob = pulp.LpProblem("Value_Ceiling", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize ceiling score
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'ceiling_score'] for i in range(len(available_players))])
    
    # Add constraints
    add_standard_constraints(prob, player_vars, available_players)
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        return get_selected_players(player_vars, available_players)
    return None

def optimize_targeting_winners(data):
    """Target the actual top performers specifically"""
    
    available_players = data[data['Salary'] > 0].copy().reset_index(drop=True)
    
    # Clean data first
    available_players['FPPG'] = pd.to_numeric(available_players['FPPG'], errors='coerce').fillna(0)
    available_players = available_players[available_players['FPPG'] > 0].reset_index(drop=True)
    
    # Identify the actual top performers
    top_performers = ['Zach Neto', 'Will Warren', 'Yu Darvish', 'Junior Caminero', 'Max Muncy', 
                     'Salvador Perez', 'Roman Anthony', 'Brandon Lowe', 'Brice Turang']
    
    available_players['target_score'] = available_players['FPPG'].copy()
    
    # Massive boost for known winners
    for performer in top_performers:
        mask = available_players['full_name'].str.contains(performer, case=False, na=False)
        available_players.loc[mask, 'target_score'] *= 3.0
    
    # Set up optimization
    prob = pulp.LpProblem("Target_Winners", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize target score
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'target_score'] for i in range(len(available_players))])
    
    # Add constraints
    add_standard_constraints(prob, player_vars, available_players)
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        return get_selected_players(player_vars, available_players)
    return None

def add_standard_constraints(prob, player_vars, available_players):
    """Add standard FanDuel constraints"""
    
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

def get_selected_players(player_vars, available_players):
    """Extract selected players from optimization result"""
    
    selected_players = []
    for i in range(len(available_players)):
        if player_vars[i].value() == 1:
            selected_players.append(available_players.loc[i])
    return selected_players

def display_lineup(strategy_name, lineup, data):
    """Display lineup results"""
    
    if not lineup:
        print(f"{strategy_name}: Optimization failed!")
        return
    
    print(f"\n{strategy_name} LINEUP:")
    print("Player | Position | Salary | Projected | ACTUAL")
    print("-" * 55)
    
    total_salary = 0
    total_projected = 0
    total_actual = 0
    
    for player in lineup:
        name = f"{player['First Name']} {player['Last Name']}"
        total_salary += player['Salary']
        total_projected += player['FPPG']
        total_actual += player['actual_fppg']
        
        print(f"{name:20} | {player['Position']:8} | ${player['Salary']:5} | {player['FPPG']:8.1f} | {player['actual_fppg']:6.1f}")
    
    print(f"\nTotal: ${total_salary:,} ({total_salary/35000:.1%}) | Proj: {total_projected:.1f} | ACTUAL: {total_actual:.1f}")
    
    # Compare to tournament results
    print(f"Tournament Winner: 306.0 | Our Original: 139.9 | This Strategy: {total_actual:.1f}")
    print(f"Improvement: +{total_actual - 139.9:.1f} | Gap to Winner: {306.0 - total_actual:.1f}")
    
    if total_actual >= 280:
        print("🏆 CHAMPION! Would have won!")
    elif total_actual >= 250:
        print("🥇 ELITE! Top 5 finish!")
    elif total_actual >= 200:
        print("🎯 EXCELLENT! Top 20 finish!")
    elif total_actual >= 160:
        print("✅ GOOD! Significant improvement!")
    else:
        print("📈 BETTER but still needs work")

if __name__ == "__main__":
    build_perfect_august_12_optimizer()
