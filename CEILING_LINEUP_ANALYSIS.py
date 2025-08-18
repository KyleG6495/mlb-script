#!/usr/bin/env python3
"""
CEILING LINEUP ANALYSIS
=======================
Analyze exactly what went wrong with our ceiling-focused lineup.
"""

import pandas as pd
from pathlib import Path

def analyze_ceiling_lineup():
    print(" ANALYZING CEILING LINEUP FAILURE")
    print("="*50)
    
    # Load our ceiling lineup
    ceiling_file = Path("../fd_current_slate/ceiling_dfs_lineup_20250729_101619.csv")
    ceiling_df = pd.read_csv(ceiling_file)
    
    # Load actual results
    actual_file = Path("../data/actual_results_latest.csv")
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
    
    # Merge with actuals
    ceiling_df['full_name'] = (ceiling_df['First Name'].str.strip() + ' ' + 
                              ceiling_df['Last Name'].str.strip()).str.lower()
    actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
    
    scored = ceiling_df.merge(
        actual_df[['full_name', 'actual_fppg']],
        on='full_name',
        how='left'
    )
    scored['actual_fppg'] = scored['actual_fppg'].fillna(0)
    
    print("TARGET: CEILING LINEUP PERFORMANCE:")
    total_actual = 0
    total_projected = 0
    
    for i, player in scored.iterrows():
        name = f"{player['First Name']} {player['Last Name']}"
        salary = player['Salary']
        projected = player['FPPG']
        actual = player['actual_fppg']
        ceiling = player['Ceiling Score']
        category = player['Ceiling Category']
        
        total_actual += actual
        total_projected += projected
        
        if actual == 0:
            status = "ERROR: ZERO"
        elif actual < projected * 0.5:
            status = " BUST"
        elif actual < projected * 0.8:
            status = "WARNING:  UNDER"
        elif actual >= projected * 1.2:
            status = " BOOM"
        else:
            status = "DATA: OK"
        
        print(f"{i+1}. {status} {name:20} ({category:12}) ${salary:5,} | Proj: {projected:5.1f} | Actual: {actual:5.1f} | Ceil: {ceiling:5.1f}")
    
    print(f"\nDATA: TOTALS:")
    print(f"  Projected: {total_projected:.1f} FPPG")
    print(f"  Actual: {total_actual:.1f} FPPG")
    print(f"  Accuracy: {total_actual/total_projected*100:.1f}%")
    
    # Compare with optimal picks
    print(f"\nLINEUP: OPTIMAL PICKS FROM SAME SLATE:")
    optimal_players = [
        ("Framber Valdez", "P", 55.0),
        ("Josh Naylor", "C/1B", 30.9),
        ("Luis Rengifo", "2B/3B/SS", 28.4),
        ("Austin Riley", "3B", 35.2),
        ("Masyn Winn", "SS", 28.7),
        ("Christian Yelich", "OF", 34.9),
        ("Ronald Acuna Jr.", "OF", 34.4),
        ("Alec Burleson", "OF", 28.4),
        ("DaShawn Keirsey Jr.", "OF", 25.2)
    ]
    
    for i, (name, pos, actual) in enumerate(optimal_players, 1):
        print(f"{i}.  {name:20} ({pos:6}) Actual: {actual:5.1f} FPPG")
    
    print(f"\nTIP: KEY INSIGHTS:")
    print(f"  ERROR: Our ceiling approach picked wrong players")
    print(f"  TARGET: The optimal plays were mid-salary value guys")
    print(f"  MONEY: Not necessarily the highest projected ceiling scores")
    print(f"  STEP: Need to focus on game theory and actual performance patterns")

if __name__ == "__main__":
    analyze_ceiling_lineup()
