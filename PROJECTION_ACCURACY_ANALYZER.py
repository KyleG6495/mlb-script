import pandas as pd
import numpy as np

def analyze_projection_accuracy():
    """
    Analyze how badly our projections failed on August 12th
    and identify patterns for improvement
    """
    
    print("=== PROJECTION ACCURACY ANALYSIS ===")
    print("Analyzing August 12th projection failures...\n")
    
    # Load actual results
    actual_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    # Load our slate with projections
    slate_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv")
    
    # Merge
    actual_df['full_name'] = actual_df['name'].str.strip()
    slate_df['full_name'] = (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.strip()
    
    merged = slate_df.merge(
        actual_df[['full_name', 'fanduel_points']], 
        on='full_name', 
        how='left'
    )
    merged['actual_fppg'] = merged['fanduel_points'].fillna(0)
    merged = merged[merged['actual_fppg'] > 0]  # Only matched players
    
    print(f"Analyzing {len(merged)} players with actual results\n")
    
    # Calculate projection errors
    merged['projection_error'] = merged['actual_fppg'] - merged['FPPG']
    merged['abs_error'] = abs(merged['projection_error'])
    merged['error_ratio'] = merged['actual_fppg'] / merged['FPPG']
    
    # Overall accuracy metrics
    mae = merged['abs_error'].mean()
    rmse = np.sqrt((merged['projection_error'] ** 2).mean())
    correlation = merged['FPPG'].corr(merged['actual_fppg'])
    
    print("=== OVERALL PROJECTION ACCURACY ===")
    print(f"Mean Absolute Error: {mae:.2f} points")
    print(f"Root Mean Square Error: {rmse:.2f} points")
    print(f"Correlation (proj vs actual): {correlation:.3f}")
    print(f"Average actual: {merged['actual_fppg'].mean():.1f}")
    print(f"Average projected: {merged['FPPG'].mean():.1f}")
    
    # Top busts (over-projected)
    print("\n=== TOP 10 PROJECTION BUSTS (Over-projected) ===")
    busts = merged.nlargest(10, 'projection_error')[['full_name', 'Position', 'Salary', 'FPPG', 'actual_fppg', 'projection_error']]
    for _, row in busts.iterrows():
        print(f"{row['full_name']:20} ({row['Position']:2}) ${row['Salary']:,} | Proj: {row['FPPG']:5.1f} | Actual: {row['actual_fppg']:5.1f} | Error: {row['projection_error']:+6.1f}")
    
    # Top misses (under-projected)
    print("\n=== TOP 10 PROJECTION MISSES (Under-projected) ===")
    misses = merged.nsmallest(10, 'projection_error')[['full_name', 'Position', 'Salary', 'FPPG', 'actual_fppg', 'projection_error']]
    for _, row in misses.iterrows():
        print(f"{row['full_name']:20} ({row['Position']:2}) ${row['Salary']:,} | Proj: {row['FPPG']:5.1f} | Actual: {row['actual_fppg']:5.1f} | Error: {row['projection_error']:+6.1f}")
    
    # Position-specific analysis
    print("\n=== PROJECTION ACCURACY BY POSITION ===")
    position_stats = merged.groupby('Position').agg({
        'abs_error': 'mean',
        'projection_error': 'mean',
        'FPPG': 'mean',
        'actual_fppg': 'mean',
        'full_name': 'count'
    }).round(2)
    position_stats.columns = ['MAE', 'Avg_Error', 'Avg_Proj', 'Avg_Actual', 'Count']
    print(position_stats)
    
    # Salary range analysis
    print("\n=== PROJECTION ACCURACY BY SALARY RANGE ===")
    merged['salary_bin'] = pd.cut(merged['Salary'], bins=[0, 3000, 4000, 6000, 9000, 15000], 
                                  labels=['<$3K', '$3K-4K', '$4K-6K', '$6K-9K', '$9K+'])
    salary_stats = merged.groupby('salary_bin').agg({
        'abs_error': 'mean',
        'projection_error': 'mean', 
        'FPPG': 'mean',
        'actual_fppg': 'mean',
        'full_name': 'count'
    }).round(2)
    salary_stats.columns = ['MAE', 'Avg_Error', 'Avg_Proj', 'Avg_Actual', 'Count']
    print(salary_stats)
    
    # Critical insights
    print("\n=== CRITICAL INSIGHTS FOR MODEL IMPROVEMENT ===")
    
    # Expensive pitcher failures
    expensive_pitchers = merged[(merged['Position'] == 'P') & (merged['Salary'] >= 9000)]
    if len(expensive_pitchers) > 0:
        print(f"Expensive Pitchers ($9K+): {expensive_pitchers['abs_error'].mean():.1f} MAE")
        print(f"  Shane Bieber performance: {expensive_pitchers[expensive_pitchers['full_name'].str.contains('Bieber', na=False)]['actual_fppg'].iloc[0] if len(expensive_pitchers[expensive_pitchers['full_name'].str.contains('Bieber', na=False)]) > 0 else 'Not found'}")
    
    # Value range success
    value_players = merged[(merged['Salary'] >= 3000) & (merged['Salary'] <= 4000)]
    if len(value_players) > 0:
        print(f"Value Range ($3K-4K): {value_players['actual_fppg'].mean():.1f} actual avg vs {value_players['FPPG'].mean():.1f} projected")
        top_value = value_players.nlargest(3, 'actual_fppg')[['full_name', 'actual_fppg', 'FPPG']]
        print("  Top value performers:")
        for _, row in top_value.iterrows():
            print(f"    {row['full_name']}: {row['actual_fppg']:.1f} actual vs {row['FPPG']:.1f} projected")
    
    # SS/3B explosion analysis
    explosive_pos = merged[merged['Position'].isin(['SS', '3B'])]
    if len(explosive_pos) > 0:
        print(f"SS/3B Positions: {explosive_pos['actual_fppg'].mean():.1f} actual avg")
        top_ss_3b = explosive_pos.nlargest(3, 'actual_fppg')[['full_name', 'Position', 'actual_fppg', 'FPPG']]
        print("  Top SS/3B performers:")
        for _, row in top_ss_3b.iterrows():
            print(f"    {row['full_name']} ({row['Position']}): {row['actual_fppg']:.1f} actual vs {row['FPPG']:.1f} projected")

if __name__ == "__main__":
    analyze_projection_accuracy()
