#!/usr/bin/env python3
"""
Team Stack Performance Analysis
Compares our projected team stacks vs actual performance from yesterday
"""

import pandas as pd
import glob
from datetime import datetime, timedelta

def analyze_team_stack_performance():
    print("=== TEAM STACK PERFORMANCE ANALYSIS ===")
    print("Comparing our projected stacks vs actual results from yesterday\n")
    
    # Load yesterday's actual results
    actual_file = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_20250820.csv'
    actual_df = pd.read_csv(actual_file)
    
    # Load yesterday's projections
    proj_files = glob.glob(r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\advanced_ownership_projections_20250820_*.csv')
    if proj_files:
        proj_file = max(proj_files)
        filename = proj_file.split('\\')[-1]
        proj_df = pd.read_csv(proj_file)
        print(f"Using projections from: {filename}")
    else:
        print("No projection file found for yesterday")
        return
    
    # Create team stacks from actual results (top 4 hitters per team)
    print(f"\nActual results: {len(actual_df)} players")
    
    # Filter hitters only
    hitters_actual = actual_df[actual_df['position'] != 'P'].copy()
    hitters_proj = proj_df[proj_df['position'] != 'P'].copy() if 'position' in proj_df.columns else proj_df.copy()
    
    print(f"Hitters only: {len(hitters_actual)} actual, {len(hitters_proj)} projected")
    
    # Group by team and get top 4 performers
    actual_stacks = []
    for team in hitters_actual['team'].unique():
        team_players = hitters_actual[hitters_actual['team'] == team].nlargest(4, 'fanduel_points')
        if len(team_players) >= 4:
            stack_total = team_players['fanduel_points'].sum()
            actual_stacks.append({
                'team': team,
                'actual_total': stack_total,
                'actual_avg': stack_total / 4,
                'players': ', '.join(team_players['name'].tolist()[:4]),
                'scores': ', '.join([f"{name}: {score:.1f}" for name, score in zip(team_players['name'].tolist()[:4], team_players['fanduel_points'].tolist()[:4])])
            })
    
    # Group projected by team and get top 4 projected performers
    proj_stacks = []
    for team in hitters_proj['team'].unique():
        team_players = hitters_proj[hitters_proj['team'] == team].nlargest(4, 'projection')
        if len(team_players) >= 4:
            stack_total = team_players['projection'].sum()
            proj_stacks.append({
                'team': team,
                'projected_total': stack_total,
                'projected_avg': stack_total / 4,
                'players': ', '.join(team_players['player_name'].tolist()[:4])
            })
    
    # Convert to DataFrames
    actual_stacks_df = pd.DataFrame(actual_stacks).sort_values('actual_total', ascending=False)
    proj_stacks_df = pd.DataFrame(proj_stacks).sort_values('projected_total', ascending=False)
    
    print("\n=== TOP 10 ACTUAL PERFORMING TEAM STACKS (Yesterday) ===")
    for i, row in actual_stacks_df.head(10).iterrows():
        print(f"{row['team']:3} - {row['actual_total']:5.1f} total ({row['actual_avg']:4.1f} avg)")
        print(f"      {row['scores']}")
        print()
    
    print("\n=== TOP 10 PROJECTED TEAM STACKS (Our System Yesterday) ===")
    for i, row in proj_stacks_df.head(10).iterrows():
        print(f"{row['team']:3} - {row['projected_total']:5.1f} total ({row['projected_avg']:4.1f} avg)")
        print(f"      {row['players']}")
        print()
    
    # Merge for comparison
    comparison = actual_stacks_df.merge(proj_stacks_df, on='team', how='outer', suffixes=('_actual', '_proj'))
    comparison = comparison.fillna(0)
    comparison['difference'] = comparison['actual_total'] - comparison['projected_total']
    comparison['accuracy'] = (comparison['projected_total'] / comparison['actual_total'] * 100).replace([float('inf'), -float('inf')], 0)
    
    print("\n=== DIRECT COMPARISON: OUR PROJECTIONS vs ACTUAL RESULTS ===")
    print("Teams where we had both projections AND actual results:")
    print()
    
    valid_comparisons = comparison[(comparison['actual_total'] > 0) & (comparison['projected_total'] > 0)].copy()
    valid_comparisons = valid_comparisons.sort_values('actual_total', ascending=False)
    
    for i, row in valid_comparisons.iterrows():
        acc_pct = row['accuracy'] if row['accuracy'] < 1000 else 100
        print(f"{row['team']:3} - Actual: {row['actual_total']:5.1f} | Projected: {row['projected_total']:5.1f} | Diff: {row['difference']:+5.1f} | Accuracy: {acc_pct:4.1f}%")
    
    print(f"\n=== SUMMARY STATS ===")
    if len(valid_comparisons) > 0:
        avg_actual = valid_comparisons['actual_total'].mean()
        avg_projected = valid_comparisons['projected_total'].mean()
        avg_accuracy = valid_comparisons['accuracy'].replace([float('inf'), -float('inf')], 100).mean()
        
        print(f"Average Actual Stack Score: {avg_actual:.1f}")
        print(f"Average Projected Stack Score: {avg_projected:.1f}")
        print(f"Overall Projection Accuracy: {avg_accuracy:.1f}%")
        print(f"Teams Analyzed: {len(valid_comparisons)}")
        
        # Find best and worst calls
        best_call = valid_comparisons.loc[valid_comparisons['accuracy'].idxmax()]
        worst_call = valid_comparisons.loc[valid_comparisons['accuracy'].idxmin()] 
        
        print(f"\nBest Projection: {best_call['team']} ({best_call['accuracy']:.1f}% accuracy)")
        print(f"Worst Projection: {worst_call['team']} ({worst_call['accuracy']:.1f}% accuracy)")
        
        # Top actual performers we missed
        missed_opportunities = actual_stacks_df[~actual_stacks_df['team'].isin(proj_stacks_df['team'])]
        if len(missed_opportunities) > 0:
            print(f"\nTeams we didn't project but performed well:")
            for i, row in missed_opportunities.head(5).iterrows():
                print(f"  {row['team']} - {row['actual_total']:.1f} points")
    
    print(f"\n=== KEY INSIGHTS ===")
    if len(valid_comparisons) > 0:
        over_projected = valid_comparisons[valid_comparisons['difference'] < -10]
        under_projected = valid_comparisons[valid_comparisons['difference'] > 10]
        
        if len(over_projected) > 0:
            print(f"Teams we OVER-projected (by >10 pts): {', '.join(over_projected['team'])}")
        if len(under_projected) > 0:
            print(f"Teams we UNDER-projected (by >10 pts): {', '.join(under_projected['team'])}")
        
        accurate_calls = valid_comparisons[abs(valid_comparisons['difference']) <= 10]
        print(f"Accurate calls (within 10 pts): {len(accurate_calls)}/{len(valid_comparisons)} teams")

if __name__ == "__main__":
    analyze_team_stack_performance()
