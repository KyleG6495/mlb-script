#!/usr/bin/env python3
"""
FIXED ENHANCED DFS CEILING OPTIMIZER
===================================
Realistic ceiling-focused lineup generator that works even without batting orders.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def generate_ceiling_lineups_fixed():
    """Generate realistic ceiling lineups with proper constraints"""
    print("TARGET: ENHANCED CEILING LINEUP GENERATOR")
    print("=" * 50)
    
    # Load slate
    try:
        slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        print(f"DATA: Loaded {len(slate)} players from slate")
    except Exception as e:
        print(f"ERROR: Error loading slate: {e}")
        return
    
    # Load ceiling weights if available
    try:
        weights = pd.read_csv("../data/ceiling_lineup_weights.csv")
        slate = slate.merge(weights[['Id', 'ceiling_weight']], on='Id', how='left')
        slate['ceiling_weight'] = slate['ceiling_weight'].fillna(1.0)
        print(f"SUCCESS: Applied ceiling weights to {len(weights)} players")
    except:
        slate['ceiling_weight'] = 1.0
        print("WARNING: No ceiling weights found, using defaults")
    
    # Filter to active players (not injured, reasonable salary)
    active_slate = slate[
        (slate['Injury Indicator'].fillna('') == '') &
        (slate['Salary'] >= 2000) &
        (slate['Salary'] <= 15000)
    ].copy()
    
    print(f" Active players: {len(active_slate)}")
    
    # Enhanced ceiling projections (realistic multipliers)
    active_slate['ceiling_fppg'] = active_slate['FPPG'] * active_slate['ceiling_weight'] * 1.10
    active_slate['value'] = active_slate['ceiling_fppg'] / active_slate['Salary'] * 1000
    
    # Position availability check
    positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    position_counts = {}
    
    for pos in positions_needed.keys():
        pos_players = active_slate[active_slate['Position'].str.contains(pos, na=False)]
        position_counts[pos] = len(pos_players)
        print(f" {pos}: {len(pos_players)} available players")
    
    # Check if we can build lineups
    can_build = all(position_counts[pos] >= positions_needed[pos] for pos in positions_needed.keys())
    
    if not can_build:
        print("WARNING: Insufficient players in some positions for full lineups")
        print("TARGET: Creating best possible lineups with available players...")
    
    lineups = []
    
    # Generate 3 ceiling lineups with different strategies
    strategies = [
        ('Ceiling_Value', 'value'),      # Best value plays
        ('Ceiling_High', 'ceiling_fppg'), # Highest ceiling
        ('Ceiling_Balanced', 'FPPG')     # Balanced approach
    ]
    
    for lineup_name, sort_col in strategies:
        lineup = []
        used_players = set()
        remaining_salary = 35000
        
        # Sort players by strategy
        strategy_slate = active_slate.sort_values(sort_col, ascending=False)
        
        # Fill positions
        for pos, count in positions_needed.items():
            filled = 0
            
            for _, player in strategy_slate.iterrows():
                if filled >= count:
                    break
                    
                # Check if player fits position and constraints
                if (pos in str(player['Position']) and 
                    player['Id'] not in used_players and
                    player['Salary'] <= remaining_salary and
                    remaining_salary - player['Salary'] >= 2000):  # Leave room for remaining positions
                    
                    lineup.append({
                        'Name': f"{player['First Name']} {player['Last Name']}",
                        'Position': player['Position'],
                        'Salary': int(player['Salary']),
                        'FPPG': round(player['FPPG'], 2),
                        'Ceiling_FPPG': round(player['ceiling_fppg'], 2),
                        'Value': round(player['value'], 2),
                        'Lineup': lineup_name
                    })
                    
                    used_players.add(player['Id'])
                    remaining_salary -= player['Salary']
                    filled += 1
        
        # Only add complete lineups under salary cap
        if len(lineup) == 9:
            total_salary = sum(p['Salary'] for p in lineup)
            if total_salary <= 35000:
                lineups.extend(lineup)
                print(f"SUCCESS: {lineup_name}: ${total_salary:,} | {sum(p['Ceiling_FPPG'] for p in lineup):.1f} ceiling FPPG")
            else:
                print(f"ERROR: {lineup_name}: Over salary cap (${total_salary:,})")
        else:
            print(f"WARNING: {lineup_name}: Incomplete ({len(lineup)}/9 positions)")
    
    if lineups:
        # Save lineups
        df = pd.DataFrame(lineups)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/enhanced_ceiling_lineups_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n Saved ceiling lineups: {output_file}")
        
        # Summary
        lineup_summary = df.groupby('Lineup').agg({
            'Salary': 'sum',
            'FPPG': 'sum',
            'Ceiling_FPPG': 'sum'
        }).round(1)
        
        print("\nTARGET: CEILING LINEUP SUMMARY:")
        print(lineup_summary)
        
        valid_count = len(lineup_summary[lineup_summary['Salary'] <= 35000])
        print(f"\nDATA: Generated {valid_count} valid ceiling lineups")
        
        if valid_count > 0:
            avg_ceiling = lineup_summary['Ceiling_FPPG'].mean()
            print(f"TARGET: Average ceiling: {avg_ceiling:.1f} FPPG")
            print(f"TARGET: Best ceiling: {lineup_summary['Ceiling_FPPG'].max():.1f} FPPG")
        
        return output_file
    else:
        print("ERROR: Could not generate any valid lineups")
        return None

if __name__ == "__main__":
    generate_ceiling_lineups_fixed()
