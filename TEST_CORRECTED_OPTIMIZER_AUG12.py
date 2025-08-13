import pandas as pd
import numpy as np

def test_corrected_optimizer_against_actuals():
    """
    Test our corrected optimizer lineups against August 12th actual results
    to see if we would have beaten the 306-point tournament winner
    """
    
    print("=== TESTING CORRECTED OPTIMIZER AGAINST AUGUST 12TH ACTUALS ===")
    print("Checking if our corrected lineups would have won the tournament...")
    print()
    
    # Load our corrected tournament lineups
    import glob
    lineup_files = glob.glob(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\CORRECTED_TOURNAMENT_LINEUPS_*.csv")
    if not lineup_files:
        print("❌ No corrected lineup files found! Run CORRECTED_TOURNAMENT_OPTIMIZER.py first")
        return
    
    latest_lineups = sorted(lineup_files)[-1]
    lineup_filename = latest_lineups.split('\\')[-1]
    print(f"📊 Loading lineups: {lineup_filename}")
    
    lineup_df = pd.read_csv(latest_lineups)
    
    # Load actual results
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    actual_results['full_name'] = actual_results['name'].str.strip()
    
    print(f"Loaded {len(actual_results)} actual results from August 12th")
    
    # Test each strategy
    strategies = lineup_df['Strategy'].unique()
    print(f"\nTesting {len(strategies)} strategies against actual results...")
    
    results = []
    
    for strategy in strategies:
        print(f"\n=== {strategy.upper()} STRATEGY RESULTS ===")
        
        strategy_players = lineup_df[lineup_df['Strategy'] == strategy].copy()
        strategy_players['full_name'] = (strategy_players['First Name'] + ' ' + strategy_players['Last Name']).str.strip()
        
        # Merge with actual results
        merged = strategy_players.merge(
            actual_results[['full_name', 'fanduel_points']], 
            on='full_name', 
            how='left'
        )
        
        # Calculate actual performance
        total_actual = 0
        total_projected = 0
        total_salary = 0
        matched_players = 0
        
        print("Player | Position | Salary | Projected | ACTUAL | Diff")
        print("-" * 65)
        
        for _, player in merged.iterrows():
            name = f"{player['First Name']} {player['Last Name']}"
            actual_points = player['fanduel_points'] if not pd.isna(player['fanduel_points']) else 0
            projected_points = player['FPPG']
            salary = player['Salary']
            
            total_actual += actual_points
            total_projected += projected_points
            total_salary += salary
            
            if actual_points > 0:
                matched_players += 1
            
            diff = actual_points - projected_points
            print(f"{name:15} | {player['Position']:8} | ${salary:5} | {projected_points:8.1f} | {actual_points:6.1f} | {diff:+5.1f}")
        
        # Strategy summary
        print(f"\nSTRATEGY SUMMARY:")
        print(f"Total Salary: ${total_salary:,} ({total_salary/35000:.1%})")
        print(f"Projected Score: {total_projected:.1f}")
        print(f"ACTUAL Score: {total_actual:.1f}")
        print(f"Difference: {total_actual - total_projected:+.1f}")
        print(f"Players Matched: {matched_players}/9")
        
        # Compare to tournament results
        print(f"\nTOURNAMENT COMPARISON:")
        print(f"Tournament Winner: 306.0 points")
        print(f"Our Original: 139.9 points")
        print(f"This Strategy: {total_actual:.1f} points")
        print(f"Gap to Winner: {306.0 - total_actual:+.1f}")
        print(f"Improvement over Original: {total_actual - 139.9:+.1f}")
        
        if total_actual >= 306:
            print("🏆 CHAMPION! Would have WON the tournament!")
        elif total_actual >= 280:
            print("🥇 ELITE! Top 3 finish!")
        elif total_actual >= 250:
            print("🎯 EXCELLENT! Top 10 finish!")
        elif total_actual >= 200:
            print("✅ GOOD! Major improvement!")
        elif total_actual >= 160:
            print("📈 BETTER! Solid progress!")
        else:
            print("❌ NEEDS WORK! Still underperforming!")
        
        # Store results
        results.append({
            'Strategy': strategy,
            'Projected_Score': total_projected,
            'Actual_Score': total_actual,
            'Difference': total_actual - total_projected,
            'Players_Matched': matched_players,
            'Tournament_Gap': 306.0 - total_actual,
            'Improvement_Over_Original': total_actual - 139.9
        })
    
    # Overall summary
    print("\n" + "="*80)
    print("OVERALL CORRECTED OPTIMIZER PERFORMANCE")
    print("="*80)
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Actual_Score', ascending=False)
    
    print("\nSTRATEGY RANKINGS (by actual score):")
    print("Rank | Strategy | Projected | Actual | Gap to Winner | vs Original")
    print("-" * 70)
    
    for i, (_, row) in enumerate(results_df.iterrows(), 1):
        print(f"{i:4d} | {row['Strategy']:15} | {row['Projected_Score']:8.1f} | {row['Actual_Score']:6.1f} | {row['Tournament_Gap']:+8.1f} | {row['Improvement_Over_Original']:+7.1f}")
    
    best_strategy = results_df.iloc[0]
    print(f"\n🏆 BEST STRATEGY: {best_strategy['Strategy']}")
    print(f"   Actual Score: {best_strategy['Actual_Score']:.1f}")
    print(f"   Would have finished {306.0 - best_strategy['Actual_Score']:.1f} points behind winner")
    print(f"   Improvement: {best_strategy['Improvement_Over_Original']:+.1f} over our original 139.9")
    
    # Key insights
    print(f"\n🔍 KEY INSIGHTS:")
    avg_actual = results_df['Actual_Score'].mean()
    avg_improvement = results_df['Improvement_Over_Original'].mean()
    
    print(f"   Average actual score: {avg_actual:.1f}")
    print(f"   Average improvement: {avg_improvement:+.1f}")
    print(f"   Best gap to winner: {results_df['Tournament_Gap'].min():+.1f}")
    
    if results_df['Actual_Score'].max() >= 280:
        print("   ✅ SUCCESS! At least one strategy would have been elite!")
    elif avg_actual >= 200:
        print("   📈 PROGRESS! Significant improvement but need more work")
    else:
        print("   ❌ FAILURE! Need major adjustments to compete")
    
    return results_df

if __name__ == "__main__":
    results = test_corrected_optimizer_against_actuals()
