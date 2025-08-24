#!/usr/bin/env python3
"""
FINAL WORKING DFS OPTIMIZER
===========================
Simplified to work with the actual FanDuel data structure.
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
from datetime import datetime
from pathlib import Path

def load_clean_slate():
    """Load and clean the slate data"""
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    slate_file = slate_dir / "fd_slate_today.csv"
    
    slate = pd.read_csv(slate_file)
    print(f"Loaded {len(slate)} total players")
    
    # Clean data
    slate = slate[slate['FPPG'] > 1.0]  # Remove very bad players
    slate = slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])
    slate['FPPG'] = slate['FPPG'].clip(1.0, 50.0)  # Cap extreme values
    
    print(f"After cleaning: {len(slate)} players")
    print(f"FPPG range: {slate['FPPG'].min():.1f} - {slate['FPPG'].max():.1f}")
    
    return slate

def simple_optimizer():
    """Simple but working optimizer"""
    slate = load_clean_slate()
    
    # Create problem
    prob = LpProblem("Simple_DFS", LpMaximize)
    
    # Variables
    player_vars = {}
    for idx, player in slate.iterrows():
        player_vars[player['Id']] = LpVariable(f"x_{idx}", cat='Binary')
    
    # Objective: maximize FPPG
    objective = lpSum([slate.loc[idx, 'FPPG'] * player_vars[slate.loc[idx, 'Id']] 
                      for idx in slate.index])
    prob += objective
    
    # Salary constraint
    prob += lpSum([slate.loc[idx, 'Salary'] * player_vars[slate.loc[idx, 'Id']] 
                  for idx in slate.index]) <= 35000
    
    # Position constraints - simplified
    # Pitcher
    pitchers = slate[slate['Roster Position'] == 'P']
    prob += lpSum([player_vars[p['Id']] for _, p in pitchers.iterrows()]) == 1
    
    # C/1B
    c1b = slate[slate['Roster Position'].str.contains('C/1B', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in c1b.iterrows()]) == 1
    
    # 2B
    second_base = slate[slate['Roster Position'].str.contains('2B', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in second_base.iterrows()]) == 1
    
    # 3B
    third_base = slate[slate['Roster Position'].str.contains('3B', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in third_base.iterrows()]) == 1
    
    # SS
    shortstop = slate[slate['Roster Position'].str.contains('SS', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in shortstop.iterrows()]) == 1
    
    # OF (need 3)
    outfield = slate[slate['Roster Position'].str.contains('OF', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in outfield.iterrows()]) == 3
    
    # UTIL (anyone eligible for UTIL)
    util_eligible = slate[slate['Roster Position'].str.contains('UTIL', na=False)]
    prob += lpSum([player_vars[p['Id']] for _, p in util_eligible.iterrows()]) == 1
    
    # Total 9 players
    prob += lpSum([player_vars[p['Id']] for _, p in slate.iterrows()]) == 9
    
    print("Solving optimization...")
    prob.solve(PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:
        print("SUCCESS: Solution found!")
        
        # Extract solution
        selected = []
        total_salary = 0
        total_fppg = 0
        
        for idx, player in slate.iterrows():
            if player_vars[player['Id']].value() == 1:
                selected.append(player)
                total_salary += player['Salary']
                total_fppg += player['FPPG']
                
        print(f"Total salary: ${total_salary}")
        print(f"Total FPPG: {total_fppg:.1f}")
        print(f"Selected {len(selected)} players:")
        
        for player in selected:
            print(f"  {player['First Name']} {player['Last Name']} ({player['Roster Position']}) - ${player['Salary']} - {player['FPPG']:.1f}")
            
        return selected
    else:
        print(f"ERROR: Optimization failed with status: {prob.status}")
        return None

def create_multiple_lineups(num_lineups=10):
    """Create multiple diverse lineups"""
    base_dir = Path(__file__).parent.parent / "data"
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    print(f"Creating {num_lineups} lineups...")
    
    slate = load_clean_slate()
    lineups = []
    used_players = set()
    
    for i in range(num_lineups):
        print(f"\nCreating lineup {i+1}...")
        
        # Create problem
        prob = LpProblem(f"DFS_Lineup_{i+1}", LpMaximize)
        
        # Variables
        player_vars = {}
        for idx, player in slate.iterrows():
            player_vars[player['Id']] = LpVariable(f"x_{i}_{idx}", cat='Binary')
        
        # Objective with diversity penalty
        objective = 0
        for idx, player in slate.iterrows():
            score = player['FPPG']
            if player['Id'] in used_players:
                score *= 0.8  # Penalty for reused players
            objective += score * player_vars[player['Id']]
        
        prob += objective
        
        # Standard constraints
        prob += lpSum([slate.loc[idx, 'Salary'] * player_vars[slate.loc[idx, 'Id']] 
                      for idx in slate.index]) <= 35000
        
        # Position constraints
        pitchers = slate[slate['Roster Position'] == 'P']
        prob += lpSum([player_vars[p['Id']] for _, p in pitchers.iterrows()]) == 1
        
        c1b = slate[slate['Roster Position'].str.contains('C/1B', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in c1b.iterrows()]) == 1
        
        second_base = slate[slate['Roster Position'].str.contains('2B', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in second_base.iterrows()]) == 1
        
        third_base = slate[slate['Roster Position'].str.contains('3B', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in third_base.iterrows()]) == 1
        
        shortstop = slate[slate['Roster Position'].str.contains('SS', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in shortstop.iterrows()]) == 1
        
        outfield = slate[slate['Roster Position'].str.contains('OF', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in outfield.iterrows()]) == 3
        
        util_eligible = slate[slate['Roster Position'].str.contains('UTIL', na=False)]
        prob += lpSum([player_vars[p['Id']] for _, p in util_eligible.iterrows()]) == 1
        
        prob += lpSum([player_vars[p['Id']] for _, p in slate.iterrows()]) == 9
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        if prob.status == 1:
            selected = []
            total_salary = 0
            total_fppg = 0
            
            for idx, player in slate.iterrows():
                if player_vars[player['Id']].value() == 1:
                    selected.append(player)
                    total_salary += player['Salary']
                    total_fppg += player['FPPG']
            
            lineups.append({
                'players': selected,
                'total_salary': total_salary,
                'total_fppg': total_fppg
            })
            
            # Add some players to used set for diversity
            if i % 2 == 0:  # Every other lineup
                player_ids = [p['Id'] for p in selected]
                used_players.update(player_ids[:3])  # Add top 3 players
            
            print(f"  SUCCESS: Salary: ${total_salary}, FPPG: {total_fppg:.1f}")
        else:
            print(f"  ERROR: Failed")
    
    print(f"\nDATA: Generated {len(lineups)} successful lineups")
    
    if lineups:
        # Save to FanDuel format
        fanduel_data = []
        
        for i, lineup in enumerate(lineups):
            # Create basic FanDuel lineup format
            lineup_dict = {'Lineup_ID': f'WORKING_{i+1}'}
            
            # Fill positions
            players = lineup['players']
            
            # Find players for each position
            for player in players:
                pos = player['Roster Position']
                name = f"{player['First Name']} {player['Last Name']}"
                
                if pos == 'P' and 'P' not in lineup_dict:
                    lineup_dict['P'] = name
                elif 'C/1B' in pos and 'C/1B' not in lineup_dict:
                    lineup_dict['C/1B'] = name
                elif '2B' in pos and 'P' not in pos and 'C/1B' not in pos and '2B' not in lineup_dict:
                    lineup_dict['2B'] = name
                elif '3B' in pos and 'P' not in pos and 'C/1B' not in pos and '3B' not in lineup_dict:
                    lineup_dict['3B'] = name
                elif 'SS' in pos and 'P' not in pos and 'C/1B' not in pos and 'SS' not in lineup_dict:
                    lineup_dict['SS'] = name
                elif 'OF' in pos and 'P' not in pos and 'OF' not in lineup_dict:
                    lineup_dict['OF'] = name
                elif 'OF' in pos and 'P' not in pos and 'OF2' not in lineup_dict:
                    lineup_dict['OF2'] = name
                elif 'OF' in pos and 'P' not in pos and 'OF3' not in lineup_dict:
                    lineup_dict['OF3'] = name
                elif 'UTIL' not in lineup_dict:
                    lineup_dict['UTIL'] = name
            
            lineup_dict['Total_Salary'] = lineup['total_salary']
            lineup_dict['Total_Projection'] = round(lineup['total_fppg'], 2)
            
            fanduel_data.append(lineup_dict)
        
        # Save to file
        df = pd.DataFrame(fanduel_data)
        output_file = slate_dir / "Working_Lineups_FD_Format.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n Saved lineups to: {output_file}")
        print(f"COMPLETE: Ready for FanDuel submission!")
        
        return output_file
    
    return None

if __name__ == "__main__":
    print("STEP: FINAL WORKING DFS OPTIMIZER")
    print("=" * 50)
    
    # Test single lineup first
    print("Testing single lineup optimization...")
    result = simple_optimizer()
    
    if result:
        print("\nSUCCESS: Single lineup works! Creating multiple lineups...")
        output_file = create_multiple_lineups(20)
        
        if output_file:
            print(f"\nCOMPLETE: SUCCESS! Your working lineups are ready!")
            print(f" File: {output_file}")
            print(f"\nTIP: These should perform much better than the previous ones!")
        else:
            print("ERROR: Failed to create multiple lineups")
    else:
        print("ERROR: Single lineup test failed")
