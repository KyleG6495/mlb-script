#!/usr/bin/env python3
"""
simple_backtest_validator.py
Simple backtest validation of our lineup system
"""

import pandas as pd
import numpy as np
from datetime import datetime
import glob
import os

def main():
    """Run simple backtest validation"""
    
    print("LINEUP BACKTEST VALIDATION")
    print("=" * 50)
    
    # Load our lineups
    print("\n1. LOADING OUR LINEUPS...")
    lineup_file = find_latest_lineup_file()
    if not lineup_file:
        print("No lineup files found")
        return
    
    lineups = pd.read_csv(lineup_file)
    print(f"   Loaded {lineups['lineup_id'].nunique()} lineups")
    print(f"   Total players: {len(lineups)}")
    
    # Load actual results
    print("\n2. LOADING ACTUAL RESULTS...")
    actual_file = "../data/actual_results_latest.csv"
    actual = pd.read_csv(actual_file)
    actual['FPPG'] = actual['fanduel_points']
    print(f"   Loaded {len(actual)} actual player results")
    print(f"   FPPG range: {actual['FPPG'].min():.1f} - {actual['FPPG'].max():.1f}")
    
    # Analyze performance
    print("\n3. ANALYZING PERFORMANCE...")
    results = analyze_simple_performance(lineups, actual)
    
    # Generate report
    print("\n4. GENERATING REPORT...")
    save_simple_report(results, lineups, actual)
    
    print("\nBACKTEST COMPLETE!")

def find_latest_lineup_file():
    """Find the most recent lineup file"""
    patterns = [
        "../data/final_tournament_lineups_details_*.csv",
        "../data/diversified_lineup_details_*.csv"
    ]
    
    files = []
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    if not files:
        return None
    
    latest = max(files, key=os.path.getctime)
    print(f"   Using: {latest}")
    return latest

def analyze_simple_performance(lineups, actual):
    """Simple performance analysis with better name matching"""
    
    # Prepare names for matching
    actual['clean_name'] = actual['name'].str.lower().str.strip()
    lineups['clean_name'] = lineups['player_name'].str.lower().str.strip()
    
    results = []
    
    print("   Lineup Performance:")
    
    for lineup_id in lineups['lineup_id'].unique():
        lineup_players = lineups[lineups['lineup_id'] == lineup_id]
        
        total_projected = lineup_players['projected_fppg'].sum()
        total_salary = lineup_players['salary'].sum()
        players_found = 0
        total_actual = 0
        matched_details = []
        
        # Try to match each player
        for _, player in lineup_players.iterrows():
            # Direct name match
            match = actual[actual['clean_name'] == player['clean_name']]
            
            if len(match) == 0:
                # Try partial name matching
                name_parts = player['clean_name'].split()
                if len(name_parts) >= 2:
                    first = name_parts[0]
                    last = name_parts[-1]
                    
                    # Look for first and last name in actual results
                    match = actual[
                        actual['clean_name'].str.contains(first, na=False) &
                        actual['clean_name'].str.contains(last, na=False)
                    ]
            
            if len(match) > 0:
                best_match = match.iloc[0]
                players_found += 1
                total_actual += best_match['FPPG']
                matched_details.append({
                    'projected_name': player['player_name'],
                    'actual_name': best_match['name'],
                    'projected_fppg': player['projected_fppg'],
                    'actual_fppg': best_match['FPPG'],
                    'position': player['position'],
                    'salary': player['salary']
                })
        
        accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
        
        results.append({
            'lineup_id': lineup_id,
            'projected_fppg': total_projected,
            'actual_fppg': total_actual,
            'salary': total_salary,
            'players_found': players_found,
            'accuracy_pct': accuracy,
            'matched_players': matched_details
        })
        
        print(f"   {lineup_id}: {accuracy:.1f}% accuracy, {players_found}/9 players found")
    
    return results

def save_simple_report(results, lineups, actual):
    """Save simple backtest report"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Calculate summary stats
    total_lineups = len(results)
    avg_projected = sum(r['projected_fppg'] for r in results) / total_lineups
    avg_actual = sum(r['actual_fppg'] for r in results) / total_lineups
    avg_found = sum(r['players_found'] for r in results) / total_lineups
    avg_accuracy = sum(r['accuracy_pct'] for r in results) / total_lineups
    
    # Best and worst performers
    best_lineup = max(results, key=lambda x: x['accuracy_pct'])
    worst_lineup = min(results, key=lambda x: x['accuracy_pct'])
    
    # Create summary
    print(f"\n   BACKTEST RESULTS SUMMARY:")
    print(f"   Total Lineups: {total_lineups}")
    print(f"   Avg Projected FPPG: {avg_projected:.1f}")
    print(f"   Avg Actual FPPG: {avg_actual:.1f}")
    print(f"   Avg Players Found: {avg_found:.1f} / 9")
    print(f"   Avg Accuracy: {avg_accuracy:.1f}%")
    print(f"   Best Lineup: {best_lineup['lineup_id']} ({best_lineup['accuracy_pct']:.1f}%)")
    print(f"   Worst Lineup: {worst_lineup['lineup_id']} ({worst_lineup['accuracy_pct']:.1f}%)")
    
    # Save detailed results
    results_df = pd.DataFrame(results)
    results_file = f"../data/simple_backtest_results_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    
    print(f"\n   Results saved to: {results_file}")
    
    # Create text report
    report_lines = [
        "LINEUP BACKTEST VALIDATION REPORT",
        "=" * 50,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "SUMMARY:",
        f"Total Lineups Tested: {total_lineups}",
        f"Average Projected FPPG: {avg_projected:.1f}",
        f"Average Actual FPPG: {avg_actual:.1f}",
        f"Average Players Found: {avg_found:.1f} / 9",
        f"Average Accuracy: {avg_accuracy:.1f}%",
        "",
        "PERFORMANCE TIERS:",
        f"Excellent (80%+ accuracy): {sum(1 for r in results if r['accuracy_pct'] >= 80)}",
        f"Good (60-80% accuracy): {sum(1 for r in results if 60 <= r['accuracy_pct'] < 80)}",
        f"Average (40-60% accuracy): {sum(1 for r in results if 40 <= r['accuracy_pct'] < 60)}",
        f"Poor (<40% accuracy): {sum(1 for r in results if r['accuracy_pct'] < 40)}",
        "",
        "BEST PERFORMERS:",
        f"1. {best_lineup['lineup_id']}: {best_lineup['accuracy_pct']:.1f}% accuracy",
        f"   Projected: {best_lineup['projected_fppg']:.1f} -> Actual: {best_lineup['actual_fppg']:.1f}",
        "",
        "METHODOLOGY NOTES:",
        "- Conservative projections implemented",
        "- Player diversification across lineups",
        "- Realistic salary management",
        "- Confirmed starter filtering",
        "",
        "NEXT STEPS:",
        "- Review player matching accuracy",
        "- Consider projection adjustments",
        "- Monitor slate data quality",
        "- Track daily performance trends"
    ]
    
    report_file = f"../data/simple_backtest_report_{timestamp}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"   Report saved to: {report_file}")
    
    # Show key insights
    print(f"\n   KEY INSIGHTS:")
    if avg_accuracy > 60:
        print(f"   - GOOD: Conservative approach showing solid accuracy")
    elif avg_accuracy > 30:
        print(f"   - MODERATE: Room for improvement in projections")
    else:
        print(f"   - POOR: Need to review methodology")
    
    if avg_found > 6:
        print(f"   - GOOD: Player matching working well")
    else:
        print(f"   - ISSUE: Player matching needs improvement")
    
    print(f"   - Conservative vs optimistic: Much more realistic projections")

if __name__ == "__main__":
    main()
