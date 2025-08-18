#!/usr/bin/env python3
"""
FILTERED AUGUST 12TH OPTIMIZER - 25 LINEUPS VERSION
Generate 25 diverse lineups using proper filtering to see maximum potential
"""

import pandas as pd
import numpy as np
import random
from itertools import combinations
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_slate_data():
    """Load the FanDuel slate data"""
    try:
        slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        logger.info(f"SUCCESS: Loaded slate: {len(df)} players")
        return df
    except Exception as e:
        logger.error(f"ERROR: Error loading slate: {e}")
        return None

def apply_filtering(df):
    """Apply proper filtering to remove unplayable players"""
    logger.info("STEP 1: FILTERING OUT INJURED PLAYERS")
    
    # Filter out injured players
    injury_indicators = ['IL', 'DTD', 'O']
    injured_mask = df['Injury Indicator'].isin(injury_indicators)
    injured_count = injured_mask.sum()
    
    healthy_df = df[~injured_mask].copy()
    logger.info(f"Players with injury indicators: {injured_count}")
    logger.info(f"Healthy players remaining: {len(healthy_df)}")
    
    logger.info("STEP 2: FILTERING PITCHERS TO PROBABLE ONLY")
    
    # For pitchers, keep only probable ones
    pitcher_mask = healthy_df['Position'].str.contains('P', na=False)
    healthy_pitchers = healthy_df[pitcher_mask]
    probable_pitchers = healthy_pitchers[healthy_pitchers['Probable Pitcher'] == 'Yes']
    
    # For non-pitchers, keep all healthy ones
    non_pitchers = healthy_df[~pitcher_mask]
    
    # Combine probable pitchers with all healthy non-pitchers
    filtered_df = pd.concat([probable_pitchers, non_pitchers], ignore_index=True)
    
    logger.info(f"Healthy pitchers: {len(healthy_pitchers)}")
    logger.info(f"Probable pitchers: {len(probable_pitchers)}")
    logger.info(f"FINAL FILTERED SLATE: {len(filtered_df)} players")
    logger.info(f"REMOVED: {len(df) - len(filtered_df)} unplayable players ({((len(df) - len(filtered_df))/len(df)*100):.1f}%)")
    
    return filtered_df

def load_actual_results():
    """Load actual results for scoring"""
    try:
        results_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250812.csv"
        results_df = pd.read_csv(results_file)
        logger.info(f"Using 2025 date, found {len(results_df)} results")
        return results_df
    except Exception as e:
        logger.error(f"ERROR: Error loading results: {e}")
        return None

def merge_with_actual_results(filtered_df, results_df):
    """Merge filtered slate with actual results"""
    # Create full name from First Name and Last Name
    filtered_df['Full_Name'] = filtered_df['First Name'] + ' ' + filtered_df['Last Name']
    
    merged_df = filtered_df.merge(
        results_df[['name', 'fanduel_points']], 
        left_on='Full_Name', 
        right_on='name', 
        how='left'
    )
    
    # Fill missing actual points with 0
    merged_df['Actual_Points'] = merged_df['fanduel_points'].fillna(0)
    
    matched_players = merged_df['Actual_Points'].notna().sum()
    logger.info(f"Matched players with actual results: {matched_players}")
    
    return merged_df

def create_lineup_strategies():
    """Create 25 different lineup strategies"""
    strategies = []
    
    # Original 5 strategies
    strategies.extend([
        {'name': 'Filtered Base', 'pitcher_max': 10000, 'value_bonus': 1.0, 'chalk_penalty': 0},
        {'name': 'Filtered Value Focus', 'pitcher_max': 8000, 'value_bonus': 1.5, 'chalk_penalty': 0},
        {'name': 'Filtered Anti-Chalk', 'pitcher_max': 12000, 'value_bonus': 1.0, 'chalk_penalty': 0.1},
        {'name': 'Filtered Upside', 'pitcher_max': 11000, 'value_bonus': 1.3, 'chalk_penalty': 0},
        {'name': 'Filtered Balanced', 'pitcher_max': 9000, 'value_bonus': 1.1, 'chalk_penalty': 0.05}
    ])
    
    # Add 20 more diverse strategies
    random.seed(42)  # For reproducible results
    for i in range(20):
        strategies.append({
            'name': f'Strategy_{i+6:02d}',
            'pitcher_max': random.choice([7000, 8000, 9000, 10000, 11000, 12000]),
            'value_bonus': round(random.uniform(1.0, 2.0), 2),
            'chalk_penalty': round(random.uniform(0, 0.2), 3),
            'position_boost': random.choice(['C', '1B', '2B', '3B', 'SS', 'OF', None]),
            'salary_focus': random.choice(['low', 'mid', 'high', 'mixed'])
        })
    
    return strategies

def optimize_lineup(merged_df, strategy, iterations=5000):
    """Optimize a single lineup using the strategy"""
    best_score = 0
    best_lineup = None
    
    # Get position groups
    catchers = merged_df[merged_df['Position'].str.contains('C', na=False)]
    first_base = merged_df[merged_df['Position'].str.contains('1B', na=False)]
    second_base = merged_df[merged_df['Position'].str.contains('2B', na=False)]
    third_base = merged_df[merged_df['Position'].str.contains('3B', na=False)]
    shortstop = merged_df[merged_df['Position'].str.contains('SS', na=False)]
    outfield = merged_df[merged_df['Position'].str.contains('OF', na=False)]
    pitchers = merged_df[merged_df['Position'].str.contains('P', na=False)]
    
    # Apply strategy filters
    if 'pitcher_max' in strategy:
        pitchers = pitchers[pitchers['Salary'] <= strategy['pitcher_max']]
    
    for attempt in range(iterations):
        try:
            lineup = []
            total_salary = 0
            
            # Select players for each position
            positions = [
                (catchers, 1, 'C'),
                (first_base, 1, '1B'),
                (second_base, 1, '2B'),
                (third_base, 1, '3B'),
                (shortstop, 1, 'SS'),
                (outfield, 3, 'OF'),
                (pitchers, 1, 'P')
            ]
            
            for pos_df, count, pos_name in positions:
                if len(pos_df) == 0:
                    break
                    
                # Apply strategy-specific selection
                weights = pos_df['Actual_Points'].copy()
                
                # Value bonus
                if 'value_bonus' in strategy:
                    value_mask = (pos_df['Salary'] >= 2500) & (pos_df['Salary'] <= 4000)
                    weights[value_mask] *= strategy['value_bonus']
                
                # Position boost
                if strategy.get('position_boost') == pos_name:
                    weights *= 1.2
                
                # Salary focus
                if strategy.get('salary_focus') == 'low':
                    low_sal_mask = pos_df['Salary'] <= 3500
                    weights[low_sal_mask] *= 1.3
                elif strategy.get('salary_focus') == 'high':
                    high_sal_mask = pos_df['Salary'] >= 4500
                    weights[high_sal_mask] *= 1.2
                
                # Select players
                available_salary = 35000 - total_salary
                affordable = pos_df[pos_df['Salary'] <= available_salary - (8-len(lineup))*2200]
                
                if len(affordable) == 0:
                    break
                    
                if count == 1:
                    # Single position selection
                    probs = weights[affordable.index] / weights[affordable.index].sum()
                    selected_idx = np.random.choice(affordable.index, p=probs)
                    selected = affordable.loc[selected_idx]
                    lineup.append(selected)
                    total_salary += selected['Salary']
                else:
                    # Multiple selections (OF)
                    for _ in range(count):
                        remaining_salary = 35000 - total_salary
                        still_affordable = affordable[affordable['Salary'] <= remaining_salary - (8-len(lineup))*2200]
                        
                        if len(still_affordable) == 0:
                            break
                            
                        probs = weights[still_affordable.index] / weights[still_affordable.index].sum()
                        selected_idx = np.random.choice(still_affordable.index, p=probs)
                        selected = still_affordable.loc[selected_idx]
                        lineup.append(selected)
                        total_salary += selected['Salary']
                        
                        # Remove selected player from available pool
                        affordable = affordable.drop(selected_idx)
            
            # Check if we have a complete lineup
            if len(lineup) == 9 and total_salary <= 35000:
                total_score = sum(player['Actual_Points'] for player in lineup)
                
                if total_score > best_score:
                    best_score = total_score
                    best_lineup = lineup.copy()
                    
        except Exception as e:
            continue
    
    return best_score, best_lineup

def main():
    logger.info("LINEUP: FILTERED AUGUST 12TH OPTIMIZER - 25 LINEUPS")
    logger.info("=" * 60)
    
    # Load and filter data
    df = load_slate_data()
    if df is None:
        return
        
    logger.info(f"Original slate size: {len(df)} players")
    filtered_df = apply_filtering(df)
    
    # Load actual results
    results_df = load_actual_results()
    if results_df is None:
        return
        
    # Merge with actual results
    merged_df = merge_with_actual_results(filtered_df, results_df)
    
    # Generate 25 strategies
    strategies = create_lineup_strategies()
    
    logger.info(f"TARGET: OPTIMIZING 25 DIFFERENT STRATEGIES")
    logger.info("=" * 60)
    
    all_results = []
    
    for i, strategy in enumerate(strategies, 1):
        logger.info(f"Optimizing strategy {i}/25: {strategy['name']}")
        best_score, best_lineup = optimize_lineup(merged_df, strategy)
        
        if best_lineup:
            all_results.append({
                'Strategy': strategy['name'],
                'Score': best_score,
                'Lineup': best_lineup
            })
            logger.info(f"  -> {best_score:.1f} points")
    
    # Sort by score
    all_results.sort(key=lambda x: x['Score'], reverse=True)
    
    print("\n" + "=" * 60)
    print("LINEUP: TOP 10 LINEUPS FROM 25 STRATEGIES")
    print("=" * 60)
    
    for i, result in enumerate(all_results[:10], 1):
        total_salary = sum(player['Salary'] for player in result['Lineup'])
        print(f"{i:2}. {result['Strategy']:20} - {result['Score']:6.1f} pts (${total_salary:,})")
    
    # Show best lineup details
    if all_results:
        best_result = all_results[0]
        print(f"\n BEST LINEUP: {best_result['Strategy']} - {best_result['Score']:.1f} POINTS")
        print("-" * 60)
        
        total_salary = 0
        for player in best_result['Lineup']:
            pos = player['Position'].split('/')[0]  # Take first position
            name = player['First Name'] + ' ' + player['Last Name']
            print(f"  {pos:2}: {name:20} ${player['Salary']:,} -> {player['Actual_Points']:5.1f} pts")
            total_salary += player['Salary']
        
        print(f"\nTOTAL: {best_result['Score']:.1f} points | ${total_salary:,} used | ${35000-total_salary:,} remaining")
        
        print("\n" + "=" * 60)
        print("DATA: COMPARISON")
        print("=" * 60)
        print(f" Tournament Winner:     306.0 points")
        print(f"TARGET: Best 25-Lineup Pool:   {best_result['Score']:.1f} points")
        print(f"TARGET: Best 5-Lineup Pool:    268.7 points")
        print(f"DATA: Original Best:         139.9 points")
        
        improvement_vs_5 = best_result['Score'] - 268.7
        print(f"\nPROGRESS: 25-lineup improvement over 5-lineup: {improvement_vs_5:+.1f} points")
        
        if best_result['Score'] > 306.0:
            print(f"LINEUP: WOULD HAVE WON THE TOURNAMENT!")
        else:
            shortage = 306.0 - best_result['Score']
            print(f" Short of tournament winner by {shortage:.1f} points")

if __name__ == "__main__":
    main()
