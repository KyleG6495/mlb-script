import pandas as pd
df = pd.read_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/finalize_hitter_features.csv')
print("Columns in fd_hitter_features_final.csv:", df.columns.tolist())
print(df[['player_id', 'Position', 'Team', 'Game']].head())
print("Sample player_id values:", df['player_id'].head().tolist())