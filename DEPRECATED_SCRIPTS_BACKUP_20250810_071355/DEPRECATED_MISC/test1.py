import pandas as pd

h = pd.read_csv('../data/today_hitter_features_merged.csv', dtype={'game_pk': str, 'player_id': str})
h_map = pd.read_csv('../data/hitter_team_map.csv', dtype=str)

# merge in game_pk
h = h.merge(h_map[['player_id','game_pk']], on='player_id', how='left')
# fallback on name_key
h['name_key'] = (h['Name']
                   .str.lower()
                   .str.replace(r'[^a-z ]','', regex=True))
m = h_map.copy()
m['name_key'] = (m['target_name']
                   .str.lower()
                   .str.replace(r'[^a-z ]','', regex=True))

h = h.merge(m[['name_key','game_pk']], on='name_key', how='left', suffixes=('','_nm'))

# who’s still missing?
still_missing = h[h['game_pk'].isna() & h['game_pk_nm'].isna()]['Name'].unique()
print(f"{len(still_missing)} hitters still missing game_pk:\n", still_missing)
