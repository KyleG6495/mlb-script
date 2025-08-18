#!/usr/bin/env python3
"""
player_fantasy_points_analyzer.py
Shows individual player fantasy points vs projections
"""

import pandas as pd
import glob
import os

def analyze_player_fantasy_points():
    """Analyze individual player fantasy points vs projections"""
    print("\nLINEUP: PLAYER FANTASY POINTS ANALYSIS")
    print("=" * 60)
    
    # Find latest backtest files
    summary_files = glob.glob('../data/clean_backtest_summary_*.csv')
    detail_files = glob.glob('../data/clean_lineup_details_*.csv')
    
    if not summary_files or not detail_files:
        print("ERROR: No backtest files found")
        return
    
    latest_summary = max(summary_files)
    latest_details = max(detail_files)
    
    summary_df = pd.read_csv(latest_summary)
    details_df = pd.read_csv(latest_details)
    
    print(f" Analyzing: {os.path.basename(latest_details)}")
    
    # Summary statistics
    avg_projected = summary_df['projected_fppg'].mean()
    avg_actual = summary_df['actual_fppg'].mean()
    avg_accuracy = summary_df['accuracy_pct'].mean()
    avg_players_found = summary_df['players_found'].mean()
    
    print(f"\nDATA: LINEUP SUMMARY:")
    print(f"Average Projected FPPG: {avg_projected:.1f}")
    print(f"Average Actual FPPG: {avg_actual:.1f}")
    print(f"Average Accuracy: {avg_accuracy:.1f}%")
    print(f"Average Players Found: {avg_players_found:.1f}/9")
    
    # Load actual results for individual player analysis
    results_files = glob.glob('../data/actual_results_*.csv')
    if not results_files:
        print("ERROR: No actual results found for individual player analysis")
        return
    
    latest_results = max(results_files)
    results_df = pd.read_csv(latest_results)
    
    print(f"\nDATA: INDIVIDUAL PLAYER FANTASY POINTS:")
    print("=" * 60)
    print(f"{'Player':<25} | {'Proj':>6} | {'Actual':>6} | {'Diff':>7} | {'Team':>4}")
    print("-" * 60)
    
    unique_players = details_df['player_name'].unique()
    total_proj = 0
    total_actual = 0
    players_found = 0
    
    for player in unique_players:
        # Find player in results
        player_results = results_df[results_df['name'].str.contains(player.split()[0], na=False, case=False)]
        
        if len(player_results) > 0:
            actual_fp = player_results.iloc[0]['fanduel_points']
            projected_fp = details_df[details_df['player_name'] == player]['projected_fppg'].iloc[0]
            team = player_results.iloc[0].get('team', 'UNK')
            diff = actual_fp - projected_fp
            
            print(f"{player:<25} | {projected_fp:6.1f} | {actual_fp:6.1f} | {diff:+7.1f} | {team:>4}")
            
            total_proj += projected_fp
            total_actual += actual_fp
            players_found += 1
        else:
            projected_fp = details_df[details_df['player_name'] == player]['projected_fppg'].iloc[0]
            print(f"{player:<25} | {projected_fp:6.1f} | {'N/A':>6} | {'N/A':>7} | {'N/A':>4}")
    
    print("-" * 60)
    print(f"{'TOTALS':<25} | {total_proj:6.1f} | {total_actual:6.1f} | {total_actual-total_proj:+7.1f} | {players_found}/9")
    
    # Analysis
    print(f"\n ANALYSIS:")
    if avg_accuracy < 50:
        print("ERROR: CRITICAL: Projections are severely overestimated")
    elif avg_accuracy < 70:
        print("WARNING: WARNING: Projections are significantly overestimated")
    else:
        print("SUCCESS: Projections are reasonably accurate")
    
    if avg_players_found < 7:
        print("ERROR: CRITICAL: Poor player matching - many players not found")
    elif avg_players_found < 8:
        print("WARNING: WARNING: Some players not found in results")
    else:
        print("SUCCESS: Good player matching")

if __name__ == "__main__":
    analyze_player_fantasy_points()
