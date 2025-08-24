#!/usr/bin/env python3
"""
FILTERED AUGUST 12 OPTIMIZER
=============================
Properly filtered DFS optimizer that excludes:
1. All IL players  
2. All non-probable pitchers
3. DTD/O players
4. Players with any injury indicators

This is what our optimizer should have been doing all along!
"""

import pandas as pd
import numpy as np
from itertools import combinations
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

print("=== FILTERED AUGUST 12TH OPTIMIZER ===")
print("Applying PROPER filtering before optimization")

# Load the slate
slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
slate_df = pd.read_csv(slate_file)
print(f"Original slate size: {len(slate_df)} players")

# Create Name column by combining First Name and Last Name
slate_df['Name'] = slate_df['First Name'] + ' ' + slate_df['Last Name']

# STEP 1: Remove ALL injured players
print("\nSTEP 1: FILTERING OUT INJURED PLAYERS")
injured_before = len(slate_df[slate_df['Injury Indicator'].notna()])
print(f"Players with injury indicators: {injured_before}")

# Keep only healthy players (no injury indicator)
clean_slate = slate_df[slate_df['Injury Indicator'].isna()].copy()
print(f"Healthy players remaining: {len(clean_slate)}")

# STEP 2: Filter pitchers to ONLY probable ones
print("\nSTEP 2: FILTERING PITCHERS TO PROBABLE ONLY")
pitchers = clean_slate[clean_slate['Position'] == 'P']
non_pitchers = clean_slate[clean_slate['Position'] != 'P']

print(f"Healthy pitchers: {len(pitchers)}")
probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
print(f"Probable pitchers: {len(probable_pitchers)}")

# Combine probable pitchers with all healthy position players
filtered_slate = pd.concat([probable_pitchers, non_pitchers], ignore_index=True)
print(f"\nFINAL FILTERED SLATE: {len(filtered_slate)} players")

# STEP 3: Show what we removed
removed_count = len(slate_df) - len(filtered_slate)
print(f"REMOVED: {removed_count} unplayable players ({removed_count/len(slate_df)*100:.1f}%)")

print(f"\nFILTERED BREAKDOWN:")
print(filtered_slate['Position'].value_counts())

# Load actual results for scoring
actual_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv"
actual_df = pd.read_csv(actual_file)
# The actual results file uses 'name' (lowercase) and has 2025 dates (should be 2024)
actual_aug12 = actual_df[actual_df['date'] == '2024-08-12'].copy()
if len(actual_aug12) == 0:
    # Try 2025 if 2024 doesn't work
    actual_aug12 = actual_df[actual_df['date'] == '2025-08-12'].copy()
    print(f"Using 2025 date, found {len(actual_aug12)} results")

# Merge with filtered slate (using 'name' from actual results)
merged_df = filtered_slate.merge(
    actual_aug12[['name', 'fanduel_points']], 
    left_on='Name', 
    right_on='name', 
    how='inner'
)
# Rename for consistency
merged_df['FPTS'] = merged_df['fanduel_points']

print(f"\nMatched players with actual results: {len(merged_df)}")

def optimize_lineup_filtered(df, strategy_name, position_weights=None, salary_cap=35000):
    """Optimize lineup using only FILTERED (playable) players"""
    
    if position_weights is None:
        position_weights = {}
    
    # Apply position-based adjustments to FPTS
    df = df.copy()
    for pos, weight in position_weights.items():
        mask = df['Position'].str.contains(pos, case=False, na=False)
        df.loc[mask, 'FPTS'] = df.loc[mask, 'FPTS'] * weight
    
    # Position requirements
    requirements = {
        'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 
        'OF': 3, 'P': 1
    }
    
    best_lineup = None
    best_score = 0
    
    # Get players by position (with multi-position handling)
    position_players = {}
    for pos in requirements.keys():
        if pos == 'OF':
            mask = df['Position'].str.contains('OF', case=False, na=False)
        else:
            mask = df['Position'].str.contains(pos, case=False, na=False)
        position_players[pos] = df[mask].sort_values('FPTS', ascending=False).head(50)
    
    attempts = 0
    max_attempts = 5000
    
    print(f"  Optimizing {strategy_name} with filtered players...")
    
    while attempts < max_attempts:
        lineup = {}
        total_salary = 0
        
        # Select players for each position
        valid_lineup = True
        for pos, count in requirements.items():
            available = position_players[pos]
            
            if len(available) < count:
                valid_lineup = False
                break
                
            if count == 1:
                # Single position
                player = available.sample(1).iloc[0]
                lineup[pos] = [player]
                total_salary += player['Salary']
            else:
                # Multiple players (OF)
                if len(available) < count:
                    valid_lineup = False
                    break
                players = available.sample(count)
                lineup[pos] = players.to_dict('records')
                total_salary += players['Salary'].sum()
        
        if not valid_lineup or total_salary > salary_cap:
            attempts += 1
            continue
            
        # Calculate total score
        total_score = 0
        for pos_players in lineup.values():
            if isinstance(pos_players, list):
                total_score += sum(p['FPTS'] for p in pos_players)
            else:
                total_score += pos_players['FPTS']
        
        if total_score > best_score:
            best_score = total_score
            best_lineup = lineup
            
        attempts += 1
        
        if attempts % 1000 == 0:
            print(f"    {attempts} attempts, best: {best_score:.1f}")
    
    return best_lineup, best_score

# OPTIMIZATION STRATEGIES for filtered players
strategies = {
    'Filtered Base': {},
    'Filtered Value Focus': {'P': 0.7, 'OF': 1.2, 'SS': 1.15, '3B': 1.15},
    'Filtered Anti-Chalk': {'P': 0.8, 'C': 1.3, '1B': 1.1, '2B': 1.2},
    'Filtered Upside': {'OF': 1.4, 'SS': 1.3, '3B': 1.3, 'P': 0.6},
    'Filtered Balanced': {'P': 0.9, 'OF': 1.1, 'SS': 1.1, '3B': 1.1, 'C': 1.1}
}

print("\n" + "="*60)
print("OPTIMIZING WITH PROPERLY FILTERED PLAYERS")
print("="*60)

filtered_results = []

for strategy_name, weights in strategies.items():
    print(f"\n--- {strategy_name.upper()} STRATEGY ---")
    
    lineup, score = optimize_lineup_filtered(merged_df, strategy_name, weights)
    
    if lineup:
        print(f"TOTAL SCORE: {score:.1f} points")
        print(f"LINEUP:")
        
        total_salary = 0
        lineup_data = []
        
        for pos, players in lineup.items():
            if isinstance(players, list):
                for i, player in enumerate(players):
                    print(f"  {pos}{i+1 if len(players) > 1 else ''}: {player['Name']} (${player['Salary']:,}) - {player['FPTS']:.1f} pts")
                    total_salary += player['Salary']
                    lineup_data.append({
                        'Strategy': strategy_name,
                        'Position': pos,
                        'Name': player['Name'],
                        'Salary': player['Salary'],
                        'FPTS': player['FPTS']
                    })
            else:
                print(f"  {pos}: {players['Name']} (${players['Salary']:,}) - {players['FPTS']:.1f} pts")
                total_salary += players['Salary']
                lineup_data.append({
                    'Strategy': strategy_name,
                    'Position': pos,
                    'Name': players['Name'],
                    'Salary': players['Salary'],
                    'FPTS': players['FPTS']
                })
        
        print(f"  TOTAL SALARY: ${total_salary:,}")
        print(f"  REMAINING: ${35000 - total_salary:,}")
        
        filtered_results.extend(lineup_data)
    else:
        print("Failed to generate valid lineup")

# Save filtered results
if filtered_results:
    results_df = pd.DataFrame(filtered_results)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FILTERED_LINEUPS_AUG12_{timestamp}.csv"
    results_df.to_csv(filename, index=False)
    print(f"\nFiltered lineups saved to: {filename}")

print("\n" + "="*60)
print("FILTERING ANALYSIS COMPLETE")
print("="*60)
print("\nKEY INSIGHTS:")
print("1. Removed ALL injured players (IL, DTD, O)")  
print("2. Kept ONLY probable pitchers")
print("3. This is how the optimizer should work!")
print("4. No more Shane Bieber selections!")
print("5. Only playable players in optimization pool")

# Show the contrast
print(f"\nCONTRAST:")
print(f"Original slate: {len(slate_df)} players")
print(f"Filtered slate: {len(filtered_slate)} players") 
print(f"Improvement: Using only {len(filtered_slate)/len(slate_df)*100:.1f}% of original slate")
print(f"Removed: {len(slate_df) - len(filtered_slate)} unplayable players")
