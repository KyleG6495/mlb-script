#!/usr/bin/env python3
"""
EVALUATE FILTERED LINEUPS - Calculate actual scores for filtered August 12th lineups
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_actual_results():
    """Load the actual results from August 12th"""
    try:
        actual_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250812.csv"
        actual_df = pd.read_csv(actual_file)
        logger.info(f"SUCCESS: Loaded actual results: {len(actual_df)} players")
        return actual_df
    except Exception as e:
        logger.error(f"ERROR: Error loading actual results: {e}")
        return None

def load_filtered_lineups():
    """Load the filtered lineups we just generated"""
    try:
        # Find the most recent filtered lineups file
        lineup_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\FILTERED_LINEUPS_AUG12_20250813_112908.csv"
        lineup_df = pd.read_csv(lineup_file)
        logger.info(f"SUCCESS: Loaded filtered lineups: {len(lineup_df)} lineups")
        return lineup_df
    except Exception as e:
        logger.error(f"ERROR: Error loading filtered lineups: {e}")
        return None

def calculate_lineup_score(strategy_df, actual_df):
    """Calculate the actual score for a lineup strategy"""
    total_score = 0
    total_salary = 0
    lineup_details = []
    
    for _, player_row in strategy_df.iterrows():
        player_name = player_row['Name']
        player_salary = player_row['Salary']
        position = player_row['Position']
        
        # Find player in actual results
        player_match = actual_df[actual_df['name'] == player_name]
        
        if not player_match.empty:
            actual_points = player_match.iloc[0]['fanduel_points']
            total_score += actual_points
            total_salary += player_salary
            lineup_details.append({
                'Position': position,
                'Name': player_name,
                'Salary': player_salary,
                'Actual_Points': actual_points
            })
        else:
            logger.warning(f"WARNING: Player not found in actual results: {player_name}")
            lineup_details.append({
                'Position': position,
                'Name': player_name,
                'Salary': player_salary,
                'Actual_Points': 0
            })
    
    return total_score, total_salary, lineup_details

def main():
    logger.info("LINEUP: EVALUATING FILTERED AUGUST 12TH LINEUPS")
    logger.info("=" * 60)
    
    # Load data
    actual_df = load_actual_results()
    lineup_df = load_filtered_lineups()
    
    if actual_df is None or lineup_df is None:
        logger.error("ERROR: Failed to load required data")
        return
    
    logger.info(f"DATA: Evaluating {len(lineup_df['Strategy'].unique())} filtered strategies against actual results")
    print()
    
    # Evaluate each strategy
    results = []
    
    for strategy in lineup_df['Strategy'].unique():
        strategy_df = lineup_df[lineup_df['Strategy'] == strategy]
        total_score, total_salary, lineup_details = calculate_lineup_score(strategy_df, actual_df)
        
        results.append({
            'Strategy': strategy,
            'Actual_Score': total_score,
            'Total_Salary': total_salary,
            'Remaining_Salary': 35000 - total_salary
        })
        
        logger.info(f"TARGET: {strategy}: {total_score:.1f} points (${total_salary:,})")
        
        # Show lineup details
        print(f"\n--- {strategy.upper()} LINEUP ---")
        for detail in lineup_details:
            print(f"  {detail['Position']}: {detail['Name']} (${detail['Salary']:,}) - {detail['Actual_Points']:.1f} pts")
        print(f"  TOTAL: {total_score:.1f} points | ${total_salary:,} used | ${35000-total_salary:,} remaining")
        print()
    
    # Sort by actual score
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Actual_Score', ascending=False)
    
    print("=" * 60)
    print("DATA: FILTERED LINEUP PERFORMANCE SUMMARY")
    print("=" * 60)
    
    for _, result in results_df.iterrows():
        print(f"{result['Strategy']:25}: {result['Actual_Score']:6.1f} points")
    
    print()
    logger.info(f"LINEUP: BEST FILTERED LINEUP: {results_df.iloc[0]['Strategy']} with {results_df.iloc[0]['Actual_Score']:.1f} points")
    
    # Compare to original performance
    print("=" * 60)
    print("PROGRESS: PERFORMANCE COMPARISON")
    print("=" * 60)
    print(f" Tournament Winner:          306.0 points")
    print(f"TARGET: Best Filtered Lineup:      {results_df.iloc[0]['Actual_Score']:.1f} points")
    print(f"DATA: Your Original Best:        139.9 points")
    print()
    
    improvement_vs_winner = results_df.iloc[0]['Actual_Score'] - 306.0
    improvement_vs_original = results_df.iloc[0]['Actual_Score'] - 139.9
    
    if improvement_vs_winner > 0:
        print(f"LINEUP: FILTERED LINEUP BEATS TOURNAMENT WINNER BY {improvement_vs_winner:.1f} POINTS!")
    else:
        print(f" Filtered lineup falls short of winner by {abs(improvement_vs_winner):.1f} points")
    
    print(f"PROGRESS: Improvement over original: +{improvement_vs_original:.1f} points ({improvement_vs_original/139.9*100:.1f}% gain)")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"FILTERED_LINEUP_EVALUATION_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    logger.info(f" Results saved: {results_file}")

if __name__ == "__main__":
    main()
