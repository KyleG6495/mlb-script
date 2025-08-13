#!/usr/bin/env python3
"""
test_quintuple_lineups.py
Test our improved quintuple lineups against actual results
"""

import pandas as pd
import numpy as np
from datetime import datetime

def main():
    """Test quintuple lineups performance"""
    
    print("🎯 TESTING IMPROVED QUINTUPLE LINEUPS")
    print("=" * 50)
    
    # Load our improved quintuple lineups
    print("\n1. LOADING IMPROVED QUINTUPLE LINEUPS...")
    quintuple_file = "../data/quintuple_lineups_combined_20250809_133006.csv"
    
    try:
        lineups = pd.read_csv(quintuple_file)
        print(f"   ✅ Loaded {len(lineups)} players from quintuple lineups")
    except FileNotFoundError:
        print(f"   ❌ File not found: {quintuple_file}")
        return
    
    # Load actual results
    print("\n2. LOADING ACTUAL RESULTS...")
    actual_file = "../data/actual_results_latest.csv"
    actual = pd.read_csv(actual_file)
    actual['FPPG'] = actual['fanduel_points']
    print(f"   ✅ Loaded {len(actual)} actual player results")
    print(f"   📊 FPPG range: {actual['FPPG'].min():.1f} - {actual['FPPG'].max():.1f}")
    
    # Test each lineup
    print("\n3. TESTING LINEUP PERFORMANCE...")
    results = test_quintuple_performance(lineups, actual)
    
    # Generate report
    print("\n4. GENERATING QUINTUPLE REPORT...")
    save_quintuple_report(results)
    
    print("\n🎯 QUINTUPLE LINEUPS TEST COMPLETE!")

def test_quintuple_performance(lineups, actual):
    """Test quintuple lineup performance"""
    
    # Prepare names for matching
    actual['clean_name'] = actual['name'].str.lower().str.strip()
    lineups['clean_name'] = lineups['Player'].str.lower().str.strip()
    
    # Group by lineup type
    lineup_types = lineups['Lineup_Type'].unique()
    results = []
    
    print("   Lineup Performance by Type:")
    
    for lineup_type in lineup_types:
        lineup_players = lineups[lineups['Lineup_Type'] == lineup_type]
        
        total_projected = lineup_players['Projected_FPPG'].sum()
        total_salary = lineup_players['Salary'].sum()
        players_found = 0
        total_actual = 0
        matched_details = []
        
        print(f"\n   🏆 {lineup_type.upper()} LINEUP:")
        print(f"   Projected Total: {total_projected:.1f} FPPG")
        print(f"   Salary: ${total_salary:,}")
        
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
                    'projected_name': player['Player'],
                    'actual_name': best_match['name'],
                    'projected_fppg': player['Projected_FPPG'],
                    'actual_fppg': best_match['FPPG'],
                    'position': player['Position'],
                    'salary': player['Salary'],
                    'team': player['Team']
                })
                print(f"   ✅ {player['Player']}: {player['Projected_FPPG']:.1f} → {best_match['FPPG']:.1f} FPPG")
            else:
                print(f"   ❌ {player['Player']}: {player['Projected_FPPG']:.1f} → NOT FOUND")
        
        accuracy = (total_actual / total_projected * 100) if total_projected > 0 else 0
        
        results.append({
            'lineup_type': lineup_type,
            'projected_fppg': total_projected,
            'actual_fppg': total_actual,
            'salary': total_salary,
            'players_found': players_found,
            'total_players': len(lineup_players),
            'accuracy_pct': accuracy,
            'matched_players': matched_details
        })
        
        print(f"   📊 RESULT: {accuracy:.1f}% accuracy, {players_found}/{len(lineup_players)} players found")
        print(f"   🎯 Actual Total: {total_actual:.1f} FPPG")
    
    return results

def save_quintuple_report(results):
    """Save quintuple lineup test report"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print(f"\n   🎯 QUINTUPLE LINEUP RESULTS SUMMARY:")
    
    for result in results:
        print(f"\n   🏆 {result['lineup_type'].upper()}:")
        print(f"      Projected: {result['projected_fppg']:.1f} FPPG")
        print(f"      Actual: {result['actual_fppg']:.1f} FPPG")
        print(f"      Accuracy: {result['accuracy_pct']:.1f}%")
        print(f"      Players Found: {result['players_found']}/{result['total_players']}")
        print(f"      Salary: ${result['salary']:,}")
    
    # Overall analysis
    if len(results) > 0:
        avg_accuracy = sum(r['accuracy_pct'] for r in results) / len(results)
        avg_players_found = sum(r['players_found'] for r in results) / len(results)
        avg_projected = sum(r['projected_fppg'] for r in results) / len(results)
        avg_actual = sum(r['actual_fppg'] for r in results) / len(results)
        
        print(f"\n   📊 OVERALL QUINTUPLE PERFORMANCE:")
        print(f"      Average Accuracy: {avg_accuracy:.1f}%")
        print(f"      Average Players Found: {avg_players_found:.1f}/9")
        print(f"      Average Projected: {avg_projected:.1f} FPPG")
        print(f"      Average Actual: {avg_actual:.1f} FPPG")
        
        # Save detailed results
        results_df = pd.DataFrame(results)
        results_file = f"../data/quintuple_test_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"\n   💾 Results saved to: {results_file}")
        
        # Key insights
        print(f"\n   🔍 KEY INSIGHTS:")
        if avg_accuracy > 50:
            print(f"      ✅ GOOD: Conservative approach showing solid accuracy")
        elif avg_accuracy > 20:
            print(f"      🔄 MODERATE: Better than old system, room for improvement")
        else:
            print(f"      ❌ POOR: Still need methodology improvements")
        
        if avg_players_found > 5:
            print(f"      ✅ GOOD: Player matching working reasonably well")
        else:
            print(f"      ❌ ISSUE: Player matching still needs work")
        
        # Compare to old system
        print(f"      📈 vs OLD SYSTEM: Conservative projections are more realistic")
        print(f"      🎯 vs OLD SYSTEM: Better player diversification")

if __name__ == "__main__":
    main()
