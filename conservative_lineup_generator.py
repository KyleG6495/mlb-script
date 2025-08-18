#!/usr/bin/env python3
"""
conservative_lineup_generator.py
Generates diversified lineups using conservative projections
"""

import pandas as pd
import numpy as np
from itertools import combinations
import random

def generate_conservative_lineups(num_lineups=10):
    """Generate diversified lineups with conservative projections"""
    
    # Load slate with conservative projections
    slate_file = "../data/fd_slate_conservative_projections.csv"
    df = pd.read_csv(slate_file)
    
    print(f"Generating {num_lineups} conservative lineups...")
    
    lineups = []
    
    for i in range(num_lineups):
        lineup = generate_single_lineup(df, i)
        if lineup:
            lineups.append(lineup)
    
    return lineups

def generate_single_lineup(df, lineup_id):
    """Generate a single lineup with salary constraints"""
    
    # Position requirements for FanDuel
    positions_needed = {
        'P': 1,
        'C': 1, 
        '1B': 1,
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3
    }
    
    lineup_players = []
    total_salary = 0
    total_fppg = 0
    salary_cap = 35000
    
    # Select players by position with some randomization
    for pos, count in positions_needed.items():
        if pos == 'OF':
            # Handle outfielders specially
            of_players = df[df['Position'].isin(['OF', 'LF', 'CF', 'RF'])].copy()
        else:
            of_players = df[df['Position'] == pos].copy()
        
        if len(of_players) == 0:
            continue
            
        # Add some randomization based on lineup_id
        random.seed(42 + lineup_id * 7)  # Deterministic but different per lineup
        
        # Select top players with some variation
        if count == 1:
            # Single position - pick from top tier with randomization
            top_players = of_players.nlargest(min(5, len(of_players)), 'Conservative_FPPG')
            selected = top_players.sample(1).iloc[0]
            
            lineup_players.append({
                'player_name': f"{selected['First Name']} {selected['Last Name']}",
                'position': selected['Position'],
                'salary': selected['Salary'],
                'projected_fppg': selected['Conservative_FPPG'],
                'team': selected.get('Team', 'UNK')
            })
            
            total_salary += selected['Salary']
            total_fppg += selected['Conservative_FPPG']
        
        else:
            # Multiple positions (OF) - diversify
            top_players = of_players.nlargest(min(8, len(of_players)), 'Conservative_FPPG')
            selected_players = top_players.sample(min(count, len(top_players)))
            
            for _, selected in selected_players.iterrows():
                lineup_players.append({
                    'player_name': f"{selected['First Name']} {selected['Last Name']}",
                    'position': selected['Position'],
                    'salary': selected['Salary'],
                    'projected_fppg': selected['Conservative_FPPG'],
                    'team': selected.get('Team', 'UNK')
                })
                
                total_salary += selected['Salary']
                total_fppg += selected['Conservative_FPPG']
    
    # Validate lineup
    if len(lineup_players) == 9 and total_salary <= salary_cap:
        return {
            'lineup_id': f'lineup_{lineup_id + 1}',
            'players': lineup_players,
            'total_salary': total_salary,
            'projected_fppg': total_fppg
        }
    
    return None

def save_lineups(lineups):
    """Save lineups in the expected format"""
    
    # Create lineup details
    details_data = []
    summary_data = []
    
    for lineup in lineups:
        lineup_id = lineup['lineup_id']
        
        for player in lineup['players']:
            details_data.append({
                'lineup_id': lineup_id,
                'player_name': player['player_name'],
                'position': player['position'],
                'team': player['team'],
                'salary': player['salary'],
                'projected_fppg': player['projected_fppg'],
                'ownership': 15.0  # Default ownership estimate
            })
        
        summary_data.append({
            'lineup_id': lineup_id,
            'projected_fppg': lineup['projected_fppg'],
            'total_salary': lineup['total_salary']
        })
    
    # Save files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    details_df = pd.DataFrame(details_data)
    details_file = f"../data/conservative_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    summary_df = pd.DataFrame(summary_data)
    summary_file = f"../data/conservative_lineup_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    
    print(f"SUCCESS: Saved lineup details: {details_file}")
    print(f"SUCCESS: Saved lineup summary: {summary_file}")
    
    return details_file, summary_file

if __name__ == "__main__":
    from datetime import datetime
    import pandas as pd
    
    lineups = generate_conservative_lineups(10)
    
    if lineups:
        print(f"\nLINEUP: GENERATED {len(lineups)} CONSERVATIVE LINEUPS")
        print("=" * 50)
        
        for lineup in lineups:
            print(f"{lineup['lineup_id']}: ${lineup['total_salary']:,} salary, {lineup['projected_fppg']:.1f} FPPG")
        
        save_lineups(lineups)
    else:
        print("ERROR: Failed to generate lineups")
