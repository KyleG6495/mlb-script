import pandas as pd

# 1) load your enriched FD slate (with FD IDs)
slate = pd.read_csv('../data/fd_hitter_features_today.csv', dtype=str)

# 2) build a name‐key to join on
slate['name_key'] = (
    slate['First Name'].str.lower().fillna('') + ' ' +
    slate['Last Name'].str.lower().fillna('')
)

# 3) load the map you generated earlier from FD names → MLB player_id
#    (this is whatever file you used in your mapping step)
id_map = pd.read_csv('../data/hitter_games.csv', dtype=str)
# assume id_map has columns: target_name, player_id (the MLB id)
id_map.rename(columns={'target_name':'name_key','player_id':'mlb_id'}, inplace=True)

# 4) merge in the real MLB IDs
slate = slate.merge(id_map[['name_key','mlb_id']], on='name_key', how='left')

# 5) load your historical base scores and reduce to one row per MLB player
base = pd.read_csv('../data/base_hitter_scores.csv', dtype=str)
base['base_score'] = base['base_score'].astype(float)
latest = (base
   .sort_values('date')
   .groupby('player_id', as_index=False).last()
   [['player_id','base_score']]
)

# 6) finally merge the base_score onto your slate by mlb_id
merged = slate.merge(
    latest,
    left_on='mlb_id', right_on='player_id',
    how='left', validate='many_to_one', indicator=True
)

matched = (merged['_merge']=='both').sum()
print(f"{matched}/{len(merged)} hitters got a base_score")

# and then write out your projected_fd_hitter_scores.csv as before
merged.to_csv('../data/projected_fd_hitter_scores.csv', index=False)
