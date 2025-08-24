#!/usr/bin/env python3
"""
SIMPLE LINEUP SCORER
===================
Score existing lineup files against actual results
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def load_actual_results():
    """Load actual results"""
    data_dir = Path(__file__).parent.parent / "data"
    actual_file = data_dir / "actual_results_latest.csv"
    
    if not actual_file.exists():
        print("No actual results found")
        return None
        
    actual_df = pd.read_csv(actual_file)
    
    # Calculate actual FPPG
    actual_df['actual_fppg'] = (
        actual_df.get('hits', 0) * 3 +
        actual_df.get('runs', 0) * 3.2 +
        actual_df.get('rbis', 0) * 3.5 +
        actual_df.get('home_runs', 0) * 12 +
        actual_df.get('stolen_bases', 0) * 6 +
        actual_df.get('walks', 0) * 3 +
        actual_df.get('doubles', 0) * 6 +
        actual_df.get('triples', 0) * 12 +
        actual_df.get('innings_pitched', 0) * 3.5 +
        actual_df.get('wins', 0) * 12 +
        actual_df.get('earned_runs', 0) * -3
    )
    
    if 'fanduel_points' in actual_df.columns:
        actual_df['actual_fppg'] = actual_df['fanduel_points'].fillna(actual_df['actual_fppg'])
    
    return actual_df

def score_lineup_file(lineup_file, actual_df):
    """Score a lineup file"""
    try:
        lineup_df = pd.read_csv(lineup_file)
        
        # For enhanced ML files, get the first lineup only
        if 'lineup_id' in lineup_df.columns:
            first_lineup = lineup_df[lineup_df['lineup_id'] == 1]
        else:
            first_lineup = lineup_df
        
        # Create lookup
        actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
        actual_lookup = dict(zip(actual_df['full_name'], actual_df['actual_fppg']))
        
        total_actual = 0
        total_projected = 0
        total_salary = 0
        scored_players = []
        points_scorers = 0
        
        for _, player in first_lineup.iterrows():
            # Handle different name formats
            if 'name' in player:
                player_name = player['name'].lower().strip()
            elif 'Name' in player:
                player_name = player['Name'].lower().strip()
            elif 'Player' in player:
                player_name = player['Player'].lower().strip()
            else:
                first_name = player.get('First Name', player.get('first_name', ''))
                last_name = player.get('Last Name', player.get('last_name', ''))
                player_name = f"{first_name} {last_name}".lower().strip()
            
            actual_fppg = actual_lookup.get(player_name, 0)
            projected_fppg = player.get('ml_projected_fppg', player.get('ML_FPPG', player.get('FPPG', player.get('fppg', player.get('Projected', 0)))))
            salary = player.get('salary', player.get('Salary', 0))
            position = player.get('position', player.get('Position', player.get('Roster Position', '')))
            
            total_actual += actual_fppg
            total_projected += projected_fppg
            total_salary += salary
            
            if actual_fppg > 0:
                points_scorers += 1
            
            scored_players.append({
                'name': player_name.title(),
                'position': position,
                'salary': salary,
                'projected': projected_fppg,
                'actual': actual_fppg,
                'diff': actual_fppg - projected_fppg
            })
        
        return {
            'file': lineup_file.name,
            'players': scored_players,
            'total_salary': total_salary,
            'total_projected': total_projected,
            'total_actual': total_actual,
            'accuracy': (total_actual / total_projected) * 100 if total_projected > 0 else 0,
            'points_scorers': points_scorers
        }
        
    except Exception as e:
        print(f"Error scoring {lineup_file.name}: {e}")
        return None

def main():
    print("SIMPLE LINEUP SCORER")
    print("Scoring today's generated lineups against actual results")
    print("="*60)
    
    # Load actual results
    actual_df = load_actual_results()
    if actual_df is None:
        return
    
    print(f"Loaded actual results for {len(actual_df)} players")
    print(f"Actual FPPG range: {actual_df['actual_fppg'].min():.1f} - {actual_df['actual_fppg'].max():.1f}")
    
    # Find lineup files
    data_dir = Path(__file__).parent.parent / "data"
    lineup_files = [
        data_dir / "enhanced_ml_dfs_lineups_20250729_095154.csv",
        data_dir / "fanduel_submission_20250729_095154.csv"
    ]
    
    results = []
    for lineup_file in lineup_files:
        if lineup_file.exists():
            print(f"\nScoring {lineup_file.name}...")
            result = score_lineup_file(lineup_file, actual_df)
            if result:
                results.append(result)
    
    # Display results
    for result in results:
        print(f"\n" + "="*60)
        print(f"FILE: {result['file']}")
        print(f"Salary: ${result['total_salary']:,}")
        print(f"Projected: {result['total_projected']:.1f} FPPG")
        print(f"Actual: {result['total_actual']:.1f} FPPG")
        print(f"Accuracy: {result['accuracy']:.1f}%")
        print(f"Players who scored: {result['points_scorers']}/9")
        
        print(f"\nTop 3 performers:")
        top_performers = sorted(result['players'], key=lambda x: x['actual'], reverse=True)[:3]
        for i, player in enumerate(top_performers, 1):
            status = "SCORED" if player['actual'] > 0 else "ZERO"
            print(f"  {i}. {player['name']:20} {player['actual']:5.1f} FPPG ({status})")

if __name__ == "__main__":
    main()
