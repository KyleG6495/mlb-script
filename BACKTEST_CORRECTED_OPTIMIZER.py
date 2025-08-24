import pandas as pd
import numpy as np

def backtest_corrected_optimizer():
    """
    Test our CORRECTED tournament lineups against August 12th actual results
    to see if we would have beaten the 306-point winner
    """
    
    print("=== BACKTEST CORRECTED OPTIMIZER vs AUGUST 12TH ===")
    print("Testing if our corrected lineups would have won the tournament...")
    print()
    
    # Load our corrected tournament lineups
    import glob
    lineup_files = glob.glob(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\CORRECTED_TOURNAMENT_LINEUPS_*.csv")
    if not lineup_files:
        print("ERROR: No corrected lineups found! Run CORRECTED_TOURNAMENT_OPTIMIZER.py first")
        return
    
    latest_lineups = sorted(lineup_files)[-1]
    filename = latest_lineups.split('\\')[-1]
    print(f"DATA: Loading: {filename}")
    
    lineups_df = pd.read_csv(latest_lineups)
    
    # Load actual results
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    actual_results['full_name'] = actual_results['name'].str.strip()
    
    # Test each strategy
    strategies = lineups_df['Strategy'].unique()
    
    print(f"Testing {len(strategies)} strategies against actual results:\n")
    
    results = []
    
    for strategy in strategies:
        print(f"=== {strategy.upper()} STRATEGY ===")
        
        strategy_lineup = lineups_df[lineups_df['Strategy'] == strategy].copy()
        
        # Match with actual results
        strategy_lineup['full_name'] = (strategy_lineup['First Name'] + ' ' + strategy_lineup['Last Name']).str.strip()
        
        merged = strategy_lineup.merge(
            actual_results[['full_name', 'fanduel_points']], 
            on='full_name', 
            how='left'
        )
        merged['actual_fppg'] = merged['fanduel_points'].fillna(0)
        
        # Calculate lineup performance
        total_salary = merged['Salary'].sum()
        total_projected = merged['FPPG'].sum()
        total_actual = merged['actual_fppg'].sum()
        matched_players = (merged['actual_fppg'] > 0).sum()
        
        print("Player | Position | Salary | Projected | ACTUAL")
        print("-" * 55)
        
        for _, row in merged.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            actual = row['actual_fppg'] if row['actual_fppg'] > 0 else "N/A"
            print(f"{name:20} | {row['Position']:8} | ${row['Salary']:5} | {row['FPPG']:8.1f} | {actual}")
        
        print(f"\nSUMMARY:")
        print(f"Total Salary: ${total_salary:,} ({total_salary/35000:.1%})")
        print(f"Projected Score: {total_projected:.1f}")
        print(f"ACTUAL Score: {total_actual:.1f}")
        print(f"Players Matched: {matched_players}/9")
        print(f"Tournament Winner: 306.0")
        print(f"Our Original Best: 139.9")
        
        if total_actual >= 306.0:
            print("LINEUP: CHAMPION! Would have WON the tournament!")
            status = "WINNER"
        elif total_actual >= 280.0:
            print(" ELITE! Top 3 finish!")
            status = "TOP_3"
        elif total_actual >= 250.0:
            print("TARGET: EXCELLENT! Top 10 finish!")
            status = "TOP_10"
        elif total_actual >= 200.0:
            print("SUCCESS: GREAT! Solid finish!")
            status = "SOLID"
        elif total_actual >= 160.0:
            print("PROGRESS: GOOD! Better than original!")
            status = "BETTER"
        else:
            print("ERROR: POOR! Worse than original")
            status = "WORSE"
        
        improvement = total_actual - 139.9
        print(f"Improvement vs Original: {improvement:+.1f} points")
        print()
        
        results.append({
            'Strategy': strategy,
            'Total_Salary': total_salary,
            'Projected_Score': total_projected,
            'Actual_Score': total_actual,
            'Players_Matched': matched_players,
            'Status': status,
            'Improvement': improvement
        })
    
    # Summary comparison
    print("=== STRATEGY COMPARISON SUMMARY ===")
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('Actual_Score', ascending=False)
    
    print("Strategy | Projected | Actual | Status | Improvement")
    print("-" * 55)
    for _, row in results_df.iterrows():
        print(f"{row['Strategy']:20} | {row['Projected_Score']:8.1f} | {row['Actual_Score']:6.1f} | {row['Status']:8} | {row['Improvement']:+6.1f}")
    
    best_strategy = results_df.iloc[0]
    print(f"\nLINEUP: BEST STRATEGY: {best_strategy['Strategy']}")
    print(f"   Actual Score: {best_strategy['Actual_Score']:.1f}")
    print(f"   Would finish: {best_strategy['Status']}")
    print(f"   Improvement: {best_strategy['Improvement']:+.1f} vs original")
    
    # Final assessment
    print("\n=== FINAL ASSESSMENT ===")
    winning_strategies = len(results_df[results_df['Actual_Score'] >= 306.0])
    top_strategies = len(results_df[results_df['Actual_Score'] >= 280.0])
    improved_strategies = len(results_df[results_df['Actual_Score'] > 139.9])
    
    print(f"Strategies that would WIN tournament: {winning_strategies}/5")
    print(f"Strategies that would finish TOP 3: {top_strategies}/5")
    print(f"Strategies better than original: {improved_strategies}/5")
    
    if winning_strategies > 0:
        print("\nCOMPLETE: SUCCESS! Our corrected optimizer CAN WIN tournaments!")
        print("START: READY to deploy this approach for today's slate!")
    elif top_strategies > 0:
        print("\nSUCCESS: GOOD! Our corrected optimizer is tournament competitive!")
        print("STEP: Minor tweaks needed for consistent wins")
    elif improved_strategies >= 3:
        print("\nPROGRESS: PROGRESS! Significant improvement over original")
        print("STEP: Need more refinement for tournament wins")
    else:
        print("\nERROR: NEEDS WORK! Corrected optimizer isn't consistently better")
        print("STEP: Major revisions needed")
    
    return results_df

if __name__ == "__main__":
    results = backtest_corrected_optimizer()
