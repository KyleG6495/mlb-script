#!/usr/bin/env python3
"""
WORKING ENHANCED DFS CEILING OPTIMIZER
=====================================
Realistic ceiling-focused lineup generator with proper multi-position handling.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def generate_working_ceiling_lineups():
    """Generate realistic ceiling lineups that actually work"""
    print("TARGET: WORKING CEILING LINEUP GENERATOR")
    print("=" * 50)
    
    # Load slate
    slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    print(f"DATA: Loaded {len(slate)} players from slate")
    
    # Load ceiling weights if available
    try:
        weights = pd.read_csv("../data/ceiling_lineup_weights.csv")
        slate = slate.merge(weights[['Id', 'ceiling_weight']], on='Id', how='left')
        slate['ceiling_weight'] = slate['ceiling_weight'].fillna(1.0)
    except:
        slate['ceiling_weight'] = 1.0
    
    # Filter active players
    active_slate = slate[
        (slate['Injury Indicator'].fillna('') == '') &
        (slate['Salary'] >= 2000) &
        (slate['Salary'] <= 15000)
    ].copy()
    
    print(f" Active players: {len(active_slate)}")
    
    # Enhanced ceiling projections (realistic 10% boost)
    active_slate['ceiling_fppg'] = active_slate['FPPG'] * active_slate['ceiling_weight'] * 1.10
    
    # Simple position mapping - handle multi-position players
    def get_primary_position(pos_str):
        if pd.isna(pos_str):
            return 'UNKNOWN'
        pos_str = str(pos_str)
        if 'P' in pos_str:
            return 'P'
        elif 'C' in pos_str:
            return 'C'
        elif '1B' in pos_str:
            return '1B'
        elif '2B' in pos_str:
            return '2B'
        elif '3B' in pos_str:
            return '3B'
        elif 'SS' in pos_str:
            return 'SS'
        elif 'OF' in pos_str:
            return 'OF'
        else:
            return 'UNKNOWN'
    
    active_slate['primary_position'] = active_slate['Position'].apply(get_primary_position)
    
    # Check position availability
    pos_counts = active_slate['primary_position'].value_counts()
    print(" Position Availability:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        count = pos_counts.get(pos, 0)
        print(f"   {pos}: {count} players")
    
    # Generate 3 ceiling lineups
    lineups = []
    
    for i in range(1, 4):
        lineup = []
        used_players = set()
        remaining_salary = 35000
        
        # Add some randomness for diversity
        np.random.seed(i * 42)
        active_slate['random_boost'] = np.random.normal(1, 0.02, len(active_slate))
        active_slate['adjusted_ceiling'] = active_slate['ceiling_fppg'] * active_slate['random_boost']
        
        # Fill positions in order
        positions_to_fill = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        
        for position in positions_to_fill:
            # Get available players for this position
            available = active_slate[
                (active_slate['primary_position'] == position) &
                (~active_slate['Id'].isin(used_players)) &
                (active_slate['Salary'] <= remaining_salary - 1000)  # Leave less room, more flexible
            ].copy()
            
            if len(available) > 0:
                # Calculate value (ceiling per dollar)
                available['value'] = available['adjusted_ceiling'] / available['Salary'] * 1000
                
                # Select best value player
                best_player = available.nlargest(1, 'value').iloc[0]
                
                lineup.append({
                    'Name': f"{best_player['First Name']} {best_player['Last Name']}",
                    'Position': best_player['Position'],
                    'Salary': int(best_player['Salary']),
                    'FPPG': round(best_player['FPPG'], 2),
                    'Ceiling_FPPG': round(best_player['ceiling_fppg'], 2),
                    'Lineup': f"Ceiling_{i}"
                })
                
                used_players.add(best_player['Id'])
                remaining_salary -= best_player['Salary']
            else:
                print(f"WARNING: No available {position} players for lineup {i}")
                break
        
        # Add complete lineups only
        if len(lineup) == 9:
            total_salary = sum(p['Salary'] for p in lineup)
            total_ceiling = sum(p['Ceiling_FPPG'] for p in lineup)
            
            if total_salary <= 35000:
                lineups.extend(lineup)
                print(f"SUCCESS: Ceiling_{i}: ${total_salary:,} salary | {total_ceiling:.1f} ceiling FPPG")
            else:
                print(f"ERROR: Ceiling_{i}: Over salary cap (${total_salary:,})")
        else:
            print(f"WARNING: Ceiling_{i}: Incomplete lineup ({len(lineup)}/9 positions)")
    
    if lineups:
        # Save lineups
        df = pd.DataFrame(lineups)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/enhanced_ceiling_lineups_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n Ceiling lineups saved: {output_file}")
        
        # Summary by lineup
        summary = df.groupby('Lineup').agg({
            'Salary': 'sum',
            'FPPG': 'sum',
            'Ceiling_FPPG': 'sum'
        }).round(1)
        
        print("\nTARGET: CEILING LINEUP SUMMARY:")
        print(summary)
        
        print(f"\nDATA: Generated {len(summary)} valid ceiling lineups")
        print(f"TARGET: Average ceiling: {summary['Ceiling_FPPG'].mean():.1f} FPPG")
        print(f"TARGET: Best ceiling: {summary['Ceiling_FPPG'].max():.1f} FPPG")
        
        return output_file
    else:
        print("ERROR: Could not generate any valid lineups")
        return None

if __name__ == "__main__":
    generate_working_ceiling_lineups()
