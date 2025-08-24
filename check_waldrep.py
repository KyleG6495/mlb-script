import pandas as pd

results_df = pd.read_csv('../data/actual_results_20250815.csv')

# Find Waldrep
waldrep_match = results_df[results_df['name'].str.contains('Waldrep', case=False, na=False)]
if len(waldrep_match) > 0:
    waldrep = waldrep_match.iloc[0]
    print(f"🎯 HURSTON WALDREP RESULT:")
    print(f"   Name: {waldrep['name']}")
    print(f"   Points: {waldrep['fanduel_points']}")
    print()

# Top performers
print("🔥 TOP PERFORMERS (40+ points) on August 15th:")
high_scorers = results_df[results_df['fanduel_points'] >= 40].sort_values('fanduel_points', ascending=False)
for i, (_, player) in enumerate(high_scorers.head(5).iterrows(), 1):
    print(f"   {i}. {player['name']} - {player['fanduel_points']} points")
