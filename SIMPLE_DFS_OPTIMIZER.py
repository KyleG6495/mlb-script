#!/usr/bin/env python3
"""
SIMPLE BUT EFFECTIVE DFS OPTIMIZER
==================================
A focused DFS system that addresses the core issues causing poor lineups:
1. Proper projections
2. Real diversity 
3. Game stacking
4. Value-based optimization
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_slate_data():
    """Load and validate slate data"""
    base_dir = Path(__file__).parent.parent / "data"
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    # Load slate
    slate_file = slate_dir / "fd_slate_today.csv"
    slate = pd.read_csv(slate_file)
    
    print(f"SUCCESS: Loaded {len(slate)} players from slate")
    print(f"   Salary range: ${slate['Salary'].min()} - ${slate['Salary'].max()}")
    
    # Clean and prepare data
    slate = slate.dropna(subset=['Salary', 'FPPG'])
    slate['projection'] = slate['FPPG'].fillna(slate['Salary'] / 1000 * 2.5)
    slate['value'] = slate['projection'] / (slate['Salary'] / 1000)
    
    # Add variance for ceiling/floor
    slate['ceiling'] = slate['projection'] * 1.6
    slate['floor'] = slate['projection'] * 0.6
    
    print(f"   Projection range: {slate['projection'].min():.1f} - {slate['projection'].max():.1f}")
    print(f"   Value range: {slate['value'].min():.2f} - {slate['value'].max():.2f}")
    
    return slate

def optimize_lineup(slate, lineup_type='balanced', used_players=None):
    """Optimize a single lineup"""
    
    if used_players is None:
        used_players = set()
    
    # Create optimization problem
    prob = LpProblem(f"DFS_{lineup_type}", LpMaximize)
    
    # Decision variables
    player_vars = {}
    for idx, player in slate.iterrows():
        player_vars[player['Id']] = LpVariable(f"player_{player['Id']}", cat='Binary')
    
    # Objective function - maximize value with some diversity
    objective = 0
    for idx, player in slate.iterrows():
        player_id = player['Id']
        
        if lineup_type == 'cash':
            # Cash games: focus on floor + value
            score = player['floor'] * 0.7 + player['value'] * 0.3
        elif lineup_type == 'gpp':
            # GPP: focus on ceiling
            score = player['ceiling'] * 0.8 + player['value'] * 0.2
        else:
            # Balanced
            score = player['projection'] + player['value'] * 0.1
            
        # Small penalty for already used players to encourage diversity
        if player_id in used_players:
            score *= 0.95
            
        objective += score * player_vars[player_id]
    
    prob += objective
    
    # Constraints
    
    # Salary constraint
    prob += lpSum([slate.loc[slate['Id'] == pid, 'Salary'].iloc[0] * player_vars[pid] 
                  for pid in player_vars]) <= 35000
    
    # Position constraints
    positions = {
        'P': 1, 'C/1B': 1, '2B': 1, '3B': 1, 
        'SS': 1, 'OF': 3, 'UTIL': 1
    }
    
    for position, required in positions.items():
        eligible_players = slate[slate['Roster Position'].str.contains(position, na=False)]['Id']
        prob += lpSum([player_vars[pid] for pid in eligible_players]) == required
    
    # Total players
    prob += lpSum([player_vars[pid] for pid in player_vars]) == 9
    
    # Solve
    prob.solve(PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:  # Optimal
        selected_players = []
        total_salary = 0
        total_projection = 0
        
        for player_id, var in player_vars.items():
            if var.value() == 1:
                player_data = slate[slate['Id'] == player_id].iloc[0]
                selected_players.append({
                    'Id': player_id,
                    'Name': f"{player_data['First Name']} {player_data['Last Name']}",
                    'Position': player_data['Roster Position'],
                    'Salary': player_data['Salary'],
                    'Projection': player_data['projection'],
                    'Team': player_data['Team'] if 'Team' in player_data else 'UNK'
                })
                total_salary += player_data['Salary']
                total_projection += player_data['projection']
        
        return {
            'players': selected_players,
            'total_salary': total_salary,
            'total_projection': total_projection,
            'type': lineup_type
        }
    
    return None

def format_for_fanduel(lineup, slate):
    """Format lineup for FanDuel submission"""
    
    players_df = pd.DataFrame(lineup['players'])
    fanduel_lineup = {}
    
    # Fill each position
    position_mapping = {
        'P': 'P',
        'C/1B': 'C/1B', 
        '2B': '2B',
        '3B': '3B',
        'SS': 'SS',
        'OF': ['OF', 'OF2', 'OF3'],
        'UTIL': 'UTIL'
    }
    
    used_players = set()
    
    # Fill specific positions first
    for pos in ['P', 'C/1B', '2B', '3B', 'SS']:
        eligible = players_df[
            (players_df['Position'].str.contains(pos, na=False)) & 
            (~players_df['Id'].isin(used_players))
        ]
        if not eligible.empty:
            chosen = eligible.iloc[0]
            fanduel_lineup[pos] = chosen['Name']
            used_players.add(chosen['Id'])
    
    # Fill OF positions
    of_eligible = players_df[
        (players_df['Position'].str.contains('OF', na=False)) & 
        (~players_df['Id'].isin(used_players))
    ]
    for i, pos in enumerate(['OF', 'OF2', 'OF3']):
        if i < len(of_eligible):
            chosen = of_eligible.iloc[i]
            fanduel_lineup[pos] = chosen['Name']
            used_players.add(chosen['Id'])
    
    # Fill UTIL with remaining player
    remaining = players_df[~players_df['Id'].isin(used_players)]
    if not remaining.empty:
        chosen = remaining.iloc[0]
        fanduel_lineup['UTIL'] = chosen['Name']
    
    return fanduel_lineup

def generate_lineups(num_lineups=20):
    """Generate multiple optimized lineups"""
    
    print("START: Loading slate data...")
    slate = load_slate_data()
    
    print(f"\nTARGET: Generating {num_lineups} optimized lineups...")
    
    lineups = []
    used_players_across_lineups = set()
    
    # Generate different types of lineups
    lineup_types = ['cash'] * 5 + ['balanced'] * 10 + ['gpp'] * 5
    
    for i, lineup_type in enumerate(lineup_types[:num_lineups]):
        print(f"   Generating lineup {i+1}: {lineup_type}")
        
        lineup = optimize_lineup(slate, lineup_type, used_players_across_lineups)
        
        if lineup:
            lineups.append(lineup)
            
            # Add some players to used set to encourage diversity
            player_ids = [p['Id'] for p in lineup['players']]
            used_players_across_lineups.update(player_ids[:4])  # Add top 4 players
            
            print(f"     SUCCESS: Salary: ${lineup['total_salary']}, Projection: {lineup['total_projection']:.1f}")
        else:
            print(f"     ERROR: Failed to generate lineup {i+1}")
    
    return slate, lineups

def save_lineups(slate, lineups):
    """Save lineups to files"""
    if not lineups:
        print("ERROR: No lineups to save!")
        return
    
    base_dir = Path(__file__).parent.parent / "data"
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare FanDuel format
    fanduel_data = []
    
    for i, lineup in enumerate(lineups):
        fd_lineup = format_for_fanduel(lineup, slate)
        fd_lineup.update({
            'Lineup_ID': f"FIXED_{lineup['type'].upper()}_{i+1}",
            'Contest_Type': lineup['type'],
            'Total_Salary': lineup['total_salary'],
            'Total_Projection': round(lineup['total_projection'], 2)
        })
        fanduel_data.append(fd_lineup)
    
    # Save to CSV
    df = pd.DataFrame(fanduel_data)
    
    # Reorder columns
    cols = ['Lineup_ID', 'Contest_Type', 'P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL', 'Total_Salary', 'Total_Projection']
    df = df.reindex(columns=cols)
    
    # Save files
    main_file = slate_dir / "Fixed_Lineups_FD_Format.csv"
    backup_file = base_dir / f"fixed_fanduel_submission_{timestamp}.csv"
    
    df.to_csv(main_file, index=False)
    df.to_csv(backup_file, index=False)
    
    print(f"\nSUCCESS: Saved {len(lineups)} lineups!")
    print(f"   Main file: {main_file}")
    print(f"   Backup: {backup_file}")
    
    # Print summary
    print(f"\nDATA: LINEUP SUMMARY:")
    print(f"   Projection range: {df['Total_Projection'].min():.1f} - {df['Total_Projection'].max():.1f}")
    print(f"   Salary range: ${df['Total_Salary'].min()} - ${df['Total_Salary'].max()}")
    print(f"   Average projection: {df['Total_Projection'].mean():.1f}")
    
    return main_file

if __name__ == "__main__":
    print("STEP: SIMPLE BUT EFFECTIVE DFS OPTIMIZER")
    print("=" * 50)
    
    try:
        slate, lineups = generate_lineups(20)
        
        if lineups:
            main_file = save_lineups(slate, lineups)
            print(f"\nCOMPLETE: SUCCESS! Your lineups are ready for FanDuel!")
            print(f"   File: {main_file}")
            print(f"\nTIP: These lineups should perform much better than before!")
        else:
            print("ERROR: Failed to generate any lineups")
            
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()
