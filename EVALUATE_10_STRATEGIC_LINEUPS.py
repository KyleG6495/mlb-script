#!/usr/bin/env python3
"""
EVALUATE 10 STRATEGIC LINEUPS - See what the 10 strategic lineups actually scored
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
                'Actual_Points': actual_points,
                'Projected': player_row['FPPG']
            })
        else:
            logger.warning(f"WARNING: Player not found in actual results: {player_name}")
            total_score += 0
            total_salary += player_salary
            lineup_details.append({
                'Position': position,
                'Name': player_name,
                'Salary': player_salary,
                'Actual_Points': 0,
                'Projected': player_row['FPPG']
            })
    
    return total_score, total_salary, lineup_details

def main():
    logger.info("LINEUP: EVALUATING 10 STRATEGIC LINEUPS AGAINST ACTUAL RESULTS")
    logger.info("=" * 70)
    
    # Load data
    actual_df = load_actual_results()
    lineup_file = "10_STRATEGIC_LINEUPS_AUG12_20250813_130948.csv"
    
    try:
        lineup_df = pd.read_csv(lineup_file)
        logger.info(f"SUCCESS: Loaded 10 strategic lineups: {len(lineup_df)} rows")
    except Exception as e:
        logger.error(f"ERROR: Error loading lineups: {e}")
        return
    
    if actual_df is None:
        return
    
    # Evaluate each strategy
    results = []
    
    strategies = lineup_df['Strategy'].unique()
    logger.info(f"DATA: Evaluating {len(strategies)} strategic lineups against actual results")
    
    for strategy in strategies:
        strategy_df = lineup_df[lineup_df['Strategy'] == strategy]
        total_score, total_salary, lineup_details = calculate_lineup_score(strategy_df, actual_df)
        
        projected_total = strategy_df['FPPG'].sum()
        
        results.append({
            'Strategy': strategy,
            'Actual_Score': total_score,
            'Projected_Score': projected_total,
            'Difference': total_score - projected_total,
            'Total_Salary': total_salary,
            'Remaining_Salary': 35000 - total_salary
        })
    
    # Sort by actual score
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Actual_Score', ascending=False)
    
    print("\n" + "=" * 70)
    print("DATA: 10 STRATEGIC LINEUPS - ACTUAL PERFORMANCE RANKING")
    print("=" * 70)
    print(f"{'Rank':4} {'Strategy':20} {'Actual':8} {'Projected':10} {'Diff':8} {'Salary':8}")
    print("-" * 70)
    
    for i, (_, result) in enumerate(results_df.iterrows(), 1):
        strategy = result['Strategy']
        actual = result['Actual_Score']
        projected = result['Projected_Score']
        diff = result['Difference']
        salary = result['Total_Salary']
        
        print(f"{i:3}. {strategy:18} {actual:7.1f} {projected:9.1f} {diff:+7.1f} ${salary:7,}")
    
    # Show top 3 lineups in detail
    print("\n" + "=" * 70)
    print("LINEUP: TOP 3 STRATEGIC LINEUPS - DETAILED BREAKDOWN")
    print("=" * 70)
    
    for i in range(min(3, len(results_df))):
        result = results_df.iloc[i]
        strategy = result['Strategy']
        strategy_df = lineup_df[lineup_df['Strategy'] == strategy]
        
        print(f"\n #{i+1}: {strategy} - {result['Actual_Score']:.1f} POINTS")
        print(f"Projected: {result['Projected_Score']:.1f} | Difference: {result['Difference']:+.1f}")
        print(f"Salary: ${result['Total_Salary']:,} | Remaining: ${result['Remaining_Salary']:,}")
        print("-" * 50)
        
        total_score, _, lineup_details = calculate_lineup_score(strategy_df, actual_df)
        
        for detail in lineup_details:
            projected = detail['Projected']
            actual = detail['Actual_Points']
            diff = actual - projected
            print(f"  {detail['Position']:2}: {detail['Name']:20} ${detail['Salary']:,} | {actual:5.1f} pts ({projected:4.1f} proj, {diff:+5.1f})")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("PROGRESS: STRATEGIC LINEUP PERFORMANCE SUMMARY")
    print("=" * 70)
    
    best_score = results_df.iloc[0]['Actual_Score']
    worst_score = results_df.iloc[-1]['Actual_Score']
    avg_score = results_df['Actual_Score'].mean()
    
    print(f"LINEUP: Best 10-strategic score:   {best_score:.1f} points")
    print(f"DATA: Average of 10 strategic:  {avg_score:.1f} points")
    print(f" Worst 10-strategic score: {worst_score:.1f} points")
    print(f" Score range:              {best_score - worst_score:.1f} points")
    print()
    print("COMPARISON TO OTHER APPROACHES:")
    print(f"TARGET: Tournament winner:        306.0 points")
    print(f" Best 5-lineup score:      268.7 points (Filtered Upside)")
    print(f"START: Best 25-lineup score:     166.7 points")
    print(f" Best 10-strategic score:  {best_score:.1f} points")
    print()
    
    # Compare to previous approaches
    improvement_vs_5 = best_score - 268.7
    improvement_vs_25 = best_score - 166.7
    improvement_vs_winner = best_score - 306.0
    
    print("PERFORMANCE ANALYSIS:")
    if improvement_vs_5 > 0:
        print(f"SUCCESS: 10-strategic IMPROVED by {improvement_vs_5:.1f} points over best 5-lineup!")
    else:
        print(f"ERROR: 10-strategic fell short by {abs(improvement_vs_5):.1f} points vs best 5-lineup")
    
    if improvement_vs_25 > 0:
        print(f"SUCCESS: 10-strategic beat 25-lineup approach by {improvement_vs_25:.1f} points")
    
    if improvement_vs_winner > 0:
        print(f"LINEUP: 10-STRATEGIC WINNER BEATS TOURNAMENT WINNER BY {improvement_vs_winner:.1f} POINTS!")
    else:
        print(f" Best 10-strategic falls short of tournament winner by {abs(improvement_vs_winner):.1f} points")
    
    # Quality assessment
    top_3_avg = results_df.head(3)['Actual_Score'].mean()
    print(f"\nTARGET: Top 3 average: {top_3_avg:.1f} points")
    print(f"DATA: Consistency: {len(results_df[results_df['Actual_Score'] >= 200])}/10 lineups scored 200+")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"10_STRATEGIC_EVALUATION_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    logger.info(f" Results saved: {results_file}")

if __name__ == "__main__":
    main()
