import pandas as pd
import os

def main():
    # --- 1) load today’s slate and extract player_id ---
    script_dir = os.path.dirname(__file__)
    slate_csv = os.path.join(script_dir, '..', 'fd_current_slate', 'fd_slate_today.csv')
    df_slate = pd.read_csv(slate_csv)
    print(f"Slate shape: {df_slate.shape}")

    # Id format is "118578-60643" → split on '-' and take the second part
    df_slate['player_id'] = df_slate['Id'].str.split('-').str[1].astype(int)

    # --- 2) split hitters vs pitchers ---
    df_hitters  = df_slate[df_slate['Position'] != 'P'].copy()
    df_pitchers = df_slate[df_slate['Position'] == 'P'].copy()
    print(f"Hitters count: {df_hitters.shape}")
    print(f"Pitchers count: {df_pitchers.shape}")

    # carry FD team code straight through
    df_hitters['team_standardized'] = df_hitters['Team']

    # --- 3) load and merge today’s box‐score stats (e.g. strikeOuts) ---
    stats_csv = os.path.join(script_dir, '..', 'data', 'today_hitter_features.csv')
    df_stats = pd.read_csv(stats_csv, usecols=['player_id', 'strikeOuts'])
    # keep the last row for each player_id (today’s)
    df_stats = df_stats.groupby('player_id', as_index=False).last()
    df_merged = df_hitters.merge(df_stats, on='player_id', how='left')
    print(f"After stats merge — shape: {df_merged.shape}")
    print(f"Missing strikeOuts count: {df_merged['strikeOuts'].isna().sum()}")

    # --- 4) load and merge your projections ---
    proj_csv = os.path.join(script_dir, '..', 'data', 'projected_hitter_scores.csv')
    df_proj = pd.read_csv(proj_csv)
    # ensure there’s a player_id column
    if 'player_id' not in df_proj.columns:
        df_proj['player_id'] = df_proj['Id'].str.split('-').str[1].astype(int)

    # pick off the one column we need
    df_proj = df_proj[['player_id', 'proj_points']]

    df_final = df_merged.merge(df_proj, on='player_id', how='left')
    print(f"Missing proj_points: {df_final['proj_points'].isna().sum()}")
    print(df_final[['Id', 'player_id', 'proj_points']].head())

if __name__ == '__main__':
    main()
