import logging
import os
import pandas as pd
import numpy as np
from fuzzywuzzy import process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y%m%d %H:%M:%S"
)

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")
SLATE_DIR = os.path.join(SCRIPT_DIR, "..", "fd_current_slate")

def normalize_player_id(pid):
    if pd.isna(pid):
        return ''
    pid = str(pid).strip().lstrip('0')
    return pid.split('-')[-1] if '-' in pid else pid

def normalize_team_name(team):
    if pd.isna(team):
        return ''
    team_map = {
        'LAD': 'Dodgers', 'SEA': 'Mariners', 'LA': 'Dodgers', 'LAA': 'Angels',
        'NYY': 'Yankees', 'NYM': 'Mets', 'CHC': 'Cubs', 'CHW': 'White Sox',
        'SFG': 'Giants', 'SDP': 'Padres', 'BOS': 'Red Sox', 'TOR': 'Blue Jays',
        'HOU': 'Astros', 'ATL': 'Braves', 'STL': 'Cardinals', 'MIL': 'Brewers',
        'PHI': 'Phillies', 'PIT': 'Pirates', 'CIN': 'Reds', 'CLE': 'Guardians',
        'COL': 'Rockies', 'MIA': 'Marlins', 'ARI': 'Diamondbacks', 'TBR': 'Rays',
        'BAL': 'Orioles', 'DET': 'Tigers', 'TEX': 'Rangers', 'KCR': 'Royals',
        'MIN': 'Twins', 'OAK': 'Athletics', 'WSN': 'Nationals', 'SF': 'Giants',
        'SD': 'Padres', 'ATH': 'Athletics'
    }
    team = str(team).strip().upper()
    return team_map.get(team, team)

def normalize_name(name):
    if pd.isna(name):
        return ''
    name = str(name).strip().lower().replace('.', '').replace(' ', '')
    if ',' in name:
        last, first = name.split(',', 1)
        name = (first.strip() + last.strip()).lower().replace(' ', '')
    return name

def fuzzy_match_name(name, choices, threshold=50):
    if not name or not choices:
        return None, 0
    result = process.extractOne(name, choices, score_cutoff=threshold)
    return result if result else (None, 0)

def compute_rolling_features(df, rolling_df, agg_df):
    df['player_id_norm'] = df['player_id'].apply(normalize_player_id)
    rolling_df['player_id_norm'] = rolling_df['player_id'].apply(normalize_player_id)
    agg_df['player_id_norm'] = agg_df['player_id'].apply(normalize_player_id)

    if 'First Name' in df.columns and 'Last Name' in df.columns:
        df['name_norm'] = (df['First Name'] + ' ' + df['Last Name']).apply(normalize_name)
        logging.info(f"Created name_norm column in hitters: {df['name_norm'].head().tolist()}")
    else:
        df['name_norm'] = ''
        logging.warning("First Name or Last Name missing in hitters. Name-based matching may fail.")

    if 'name' in agg_df.columns:
        agg_df['name_norm'] = agg_df['name'].apply(normalize_name)
        logging.info(f"Created name_norm column in agg_df: {agg_df['name_norm'].head().tolist()}")
    else:
        agg_df['name_norm'] = ''
        logging.warning("Name column missing in aggregated features. Using league averages.")

    if 'name' in rolling_df.columns:
        rolling_df['name_norm'] = rolling_df['name'].apply(normalize_name)
        logging.info(f"Created name_norm column in rolling_df: {rolling_df['name_norm'].head().tolist()}")
    else:
        rolling_df['name_norm'] = ''
        logging.warning("Name column missing in rolling features. Skipping rolling stats.")

    rolling_df = rolling_df[rolling_df['date'] == '2025-07-11'].copy()
    logging.info(f"Filtered rolling features to {len(rolling_df):,} rows for date 2025-07-11")

    hitters_ids = set(df['player_id_norm'])
    rolling_ids = set(rolling_df['player_id_norm'])
    agg_ids = set(agg_df['player_id_norm'])
    common_ids = hitters_ids.intersection(rolling_ids)
    common_agg_ids = hitters_ids.intersection(agg_ids)
    logging.info(f"Unique player_ids in hitters: {len(hitters_ids)}, in rolling: {len(rolling_ids)}, common: {len(common_ids)}")
    logging.info(f"Unique player_ids in hitters: {len(hitters_ids)}, in aggregated: {len(agg_ids)}, common: {len(common_agg_ids)}")
    if len(common_ids) < len(hitters_ids):
        logging.warning(f"Missing player_ids in rolling features: {list(hitters_ids - rolling_ids)[:10]}...")
        logging.info(f"Sample hitter player_ids: {list(hitters_ids)[:5]}")
        logging.info(f"Sample rolling player_ids: {list(rolling_ids)[:5]}")
    if len(common_agg_ids) < len(hitters_ids):
        logging.warning(f"Missing player_ids in aggregated features: {list(hitters_ids - agg_ids)[:10]}...")
        logging.info(f"Sample aggregated player_ids: {list(agg_ids)[:5]}")

    # Merge with rolling_df using name_norm
    merged = df.merge(
        rolling_df[['name_norm', 'hits', 'atBats', 'baseOnBalls', 'hitByPitch', 'sacFlies']],
        on='name_norm',
        how='left'
    )
    logging.info(f"Merged rolling features: {len(merged):,} rows")
    logging.info(f"Sample hitter names after rolling merge: {merged['name_norm'].head().tolist()}")

    # Calculate rolling stats
    merged['rolling_avg_hits'] = merged['hits'].div(merged['atBats'].where(merged['atBats'] > 0, np.nan)).fillna(0)
    denominator = (
        merged['atBats'].fillna(0) +
        merged['baseOnBalls'].fillna(0) +
        merged['hitByPitch'].fillna(0) +
        merged['sacFlies'].fillna(0)
    )
    numerator = (
        merged['hits'].fillna(0) +
        merged['baseOnBalls'].fillna(0) +
        merged['hitByPitch'].fillna(0)
    )
    merged['rolling_avg_OBP'] = np.where(
        denominator > 0,
        numerator / denominator,
        0.0
    )

    # Add low-plate-appearance flag based on Played
    merged['low_pa_flag'] = merged['Played'] <= 20
    logging.info(f"Players with low plate appearances (Played <= 20): {len(merged[merged['low_pa_flag']])}")

    # Merge with agg_df using name_norm
    merged = merged.merge(
        agg_df[['name_norm', 'AVG', 'OBP']],
        on='name_norm',
        how='left'
    )
    logging.info(f"Sample hitter names after agg merge: {merged['name_norm'].head().tolist()}")

    manual_stats = {
        'kyleschwarber': {'AVG': 0.270, 'OBP': 0.340},
        'bryceharper': {'AVG': 0.290, 'OBP': 0.360},
        'treaturner': {'AVG': 0.300, 'OBP': 0.350},
        'nickcastellanos': {'AVG': 0.260, 'OBP': 0.320},
        'brysonstott': {'AVG': 0.280, 'OBP': 0.330},
        'maxmuncy': {'AVG': 0.250, 'OBP': 0.340},
        'jtrealmuto': {'AVG': 0.275, 'OBP': 0.330},
        'alecbohm': {'AVG': 0.290, 'OBP': 0.345},
        'maxkepler': {'AVG': 0.265, 'OBP': 0.325},
        'brandonmarsh': {'AVG': 0.270, 'OBP': 0.335},
        'ottokemp': {'AVG': 0.260, 'OBP': 0.320},
        'samhuff': {'AVG': 0.260, 'OBP': 0.320},
        'danieljohnson': {'AVG': 0.260, 'OBP': 0.320}
    }

    # Apply name-based matching for aggregated stats
    if 'name_norm' in merged.columns:
        logging.info("Attempting name-based matching for aggregated stats")
        agg_names = agg_df['name_norm'].dropna().unique().tolist()
        valid_names = merged['name_norm'].dropna()
        fuzzy_matches = valid_names.apply(lambda x: fuzzy_match_name(x, agg_names, threshold=50))
        merged['matched_name'] = pd.Series([m[0] if m else None for m in fuzzy_matches], index=valid_names.index)
        merged['match_score'] = pd.Series([m[1] if m else 0 for m in fuzzy_matches], index=valid_names.index)
        agg_name_to_stats = agg_df.set_index('name_norm')[['AVG', 'OBP']].to_dict()
        merged['AVG_name'] = merged['matched_name'].map(agg_name_to_stats.get('AVG', {}))
        merged['OBP_name'] = merged['matched_name'].map(agg_name_to_stats.get('OBP', {}))
        logging.info(f"Name-based matches: {len(merged[merged['AVG_name'].notna()])}")
        logging.info(f"Sample hitter names: {merged['name_norm'].head().tolist()}")
        logging.info(f"Sample agg names: {agg_df['name_norm'].head().tolist()}")
        logging.info(f"Sample match scores: {merged['match_score'].head().tolist()}")
        unmatched = merged[merged['AVG_name'].isna()]['name_norm'].dropna().unique()
        logging.info(f"Unmatched hitter names: {unmatched[:10].tolist()}")

        # Apply manual stats
        merged['AVG_manual'] = merged['name_norm'].map(lambda x: manual_stats.get(x, {}).get('AVG'))
        merged['OBP_manual'] = merged['name_norm'].map(lambda x: manual_stats.get(x, {}).get('OBP'))
        logging.info(f"Manual stats applied: {len(merged[merged['AVG_manual'].notna()])} rows")

    # Compute league averages as fallback
    avg_avg = agg_df['AVG'].mean() if not agg_df['AVG'].isna().all() else 0.250
    avg_obp = agg_df['OBP'].mean() if not agg_df['OBP'].isna().all() else 0.320
    logging.info(f"League average AVG: {avg_avg:.3f}, OBP: {avg_obp:.3f}")

    # Use rolling stats, then manual stats, then aggregated stats, then league averages
    merged['rolling_avg_hits'] = np.where(
        (merged['rolling_avg_hits'] > 0) & (merged['atBats'] > 0),
        merged['rolling_avg_hits'],
        np.where(
            merged['AVG_manual'].notna(),
            merged['AVG_manual'],
            np.where(
                merged['AVG_name'].notna() & (merged['AVG_name'] > 0),
                merged['AVG_name'],
                avg_avg
            )
        )
    )
    merged['rolling_avg_OBP'] = np.where(
        (merged['rolling_avg_OBP'] > 0) & (denominator > 0),
        merged['rolling_avg_OBP'],
        np.where(
            merged['OBP_manual'].notna(),
            merged['OBP_manual'],
            np.where(
                merged['OBP_name'].notna() & (merged['OBP_name'] > 0),
                merged['OBP_name'],
                avg_obp
            )
        )
    )
    merged = merged.drop(columns=['AVG', 'OBP', 'AVG_name', 'OBP_name', 'AVG_manual', 'OBP_manual', 'name_norm', 'matched_name', 'match_score', 'hits', 'atBats', 'baseOnBalls', 'hitByPitch', 'sacFlies'], errors='ignore')

    logging.info(f"Non-zero rolling_avg_hits: {len(merged[merged['rolling_avg_hits'] > 0])}, non-zero rolling_avg_OBP: {len(merged[merged['rolling_avg_OBP'] > 0])}")
    logging.info(f"League average rolling_avg_hits ({avg_avg:.3f}): {len(merged[merged['rolling_avg_hits'] == avg_avg])}, League average rolling_avg_OBP ({avg_obp:.3f}): {len(merged[merged['rolling_avg_OBP'] == avg_obp])}")

    return merged

def add_weather_park_features(df, weather_park_df):
    hitters_pks = set(df['game_pk'].dropna().astype(str).str.strip())
    weather_pks = set(weather_park_df['game_pk'].astype(str).str.strip())
    logging.info(f"Unique game_pks in hitters: {len(hitters_pks)}, in weather_park: {len(weather_pks)}, common: {len(hitters_pks.intersection(weather_pks))}")
    if len(hitters_pks.intersection(weather_pks)) < len(hitters_pks):
        logging.warning(f"Missing game_pks in weather_park: {list(hitters_pks - weather_pks)[:10]}...")

    weather_park_df['Team'] = weather_park_df['Team'].apply(normalize_team_name)
    df['team_standardized'] = df['Team'].apply(normalize_team_name)

    merged = df.merge(
        weather_park_df[['game_pk', 'park_factor', 'temperature']],
        on='game_pk',
        how='left',
        suffixes=('_existing', '_weather')
    )
    logging.info(f"Merged with weather_park features: {len(merged):,} rows")

    if 'park_factor_weather' in merged.columns:
        merged['park_factor_merge'] = merged['park_factor_weather']
    else:
        merged['park_factor_merge'] = merged['park_factor'] if 'park_factor' in merged.columns else np.nan
    if 'temperature_weather' in merged.columns:
        merged['temperature_merge'] = merged['temperature_weather']
    else:
        merged['temperature_merge'] = merged['temperature'] if 'temperature' in merged.columns else np.nan

    if 'team_standardized' in merged.columns:
        team_to_park = weather_park_df.set_index('Team')[['park_factor', 'temperature']].to_dict()
        merged['park_factor_team'] = merged['team_standardized'].apply(normalize_team_name).map(team_to_park.get('park_factor', {}))
        merged['temperature_team'] = merged['team_standardized'].apply(normalize_team_name).map(team_to_park.get('temperature', {}))
        logging.info(f"Team-standardized matches: {len(merged[merged['park_factor_team'].notna()])}")
        logging.info(f"Sample team_standardized values: {merged['team_standardized'].dropna().unique()[:5].tolist()}")
    else:
        merged['park_factor_team'] = np.nan
        merged['temperature_team'] = np.nan
        logging.warning("No team_standardized column for team mapping.")

    avg_park_factor = weather_park_df['park_factor'].mean() if not weather_park_df['park_factor'].isna().all() else 1.0
    avg_temperature = weather_park_df['temperature'].mean() if not weather_park_df['temperature'].isna().all() else 70.0

    merged['park_factor'] = np.where(
        merged['park_factor_merge'].notna(),
        merged['park_factor_merge'],
        np.where(
            merged['park_factor_team'].notna(),
            merged['park_factor_team'],
            avg_park_factor
        )
    )
    merged['temperature'] = np.where(
        merged['temperature_merge'].notna(),
        merged['temperature_merge'],
        np.where(
            merged['temperature_team'].notna(),
            merged['temperature_team'],
            avg_temperature
        )
    )
    merged = merged.drop(columns=['park_factor_merge', 'temperature_merge', 'park_factor_team', 'temperature_team', 'park_factor_weather', 'temperature_weather', 'park_factor_existing', 'temperature_existing'], errors='ignore')
    logging.info(f"Non-null park_factor: {len(merged[merged['park_factor'] != avg_park_factor])}, non-null temperature: {len(merged[merged['temperature'] != avg_temperature])}")
    logging.info(f"Average park_factor used: {avg_park_factor}, Average temperature used: {avg_temperature}")

    return merged

def add_required_features(df):
    if 'Salary' in df.columns:
        df['log_Salary'] = np.log(df['Salary'].astype(float) + 1)
        logging.info("Added log_Salary")
    else:
        logging.warning("Salary column missing. Assigning NaN to log_Salary.")
        df['log_Salary'] = np.nan

    if 'FPPG' in df.columns:
        fppg_mean = df['FPPG'].mean()
        df['FPPG'] = df['FPPG'].fillna(fppg_mean)
        logging.info(f"Imputed {df['FPPG'].isna().sum()} missing FPPG values with mean {fppg_mean:.2f}")

    return df

def main():
    today_fn = os.path.join(SLATE_DIR, 'fd_slate_today.csv')
    logging.info(f"Loading today features: {today_fn}")
    try:
        hitters = pd.read_csv(today_fn, dtype={"Id": str})
        hitters['player_id'] = hitters['Id'].astype(str).str.strip()
        hitters['game_pk'] = hitters['Game'].map({'LAD@SF': '777206', 'PHI@SD': '777205'})
        logging.info(f" → {len(hitters):,} hitter rows")
    except FileNotFoundError:
        logging.error(f"Today features file {today_fn} not found")
        raise

    if 'Position' in hitters.columns:
        logging.info(f"Unique positions in hitters: {hitters['Position'].unique()}")
        hitters = hitters[~hitters['Position'].str.contains("P", na=False)]
        logging.info(f" → Filtered to {len(hitters):,} hitter rows")
    else:
        logging.warning("Position column missing in hitters. Processing all rows.")

    before = len(hitters)
    hitters = hitters[hitters['game_pk'].notna() & (hitters['game_pk'] != "") & (hitters['game_pk'] != "nan") & (hitters['game_pk'].isin(['777205', '777206']))]
    logging.info(f"Filtered to {len(hitters):,} rows with valid game_pk 777205, 777206 (removed {before - len(hitters):,})")

    rolling_fn = os.path.join(DATA_DIR, 'hitter_rolling_5game_features.csv')
    logging.info(f"Loading rolling features: {rolling_fn}")
    try:
        rolling = pd.read_csv(rolling_fn, dtype={"player_id": str})
        logging.info(f" → {len(rolling):,} rolling feature rows")
    except FileNotFoundError:
        logging.error(f"Rolling features file {rolling_fn} not found")
        raise

    agg_fn = os.path.join(DATA_DIR, 'aggregated_hitter_features_2025.csv')
    logging.info(f"Loading aggregated features: {agg_fn}")
    try:
        agg = pd.read_csv(agg_fn, dtype={"player_id": str})
        logging.info(f" → {len(agg):,} aggregated feature rows")
    except FileNotFoundError:
        logging.error(f"Aggregated features file {agg_fn} not found")
        raise

    weather_park_fn = os.path.join(DATA_DIR, 'merged_weather_park.csv')
    logging.info(f"Loading weather and park features: {weather_park_fn}")
    try:
        weather_park_df = pd.read_csv(weather_park_fn, dtype={"game_pk": str})
        weather_park_df['game_pk'] = weather_park_df['game_pk'].astype(str).str.strip()
        logging.info(f" → {len(weather_park_df):,} weather_park rows")
    except FileNotFoundError:
        logging.error(f"Weather_park file {weather_park_fn} not found")
        raise

    hitters = compute_rolling_features(hitters, rolling, agg)
    hitters = add_weather_park_features(hitters, weather_park_df)
    hitters = add_required_features(hitters)

    required_columns = [
        'player_id', 'FPPG', 'log_Salary', 'Played', 'rolling_avg_hits',
        'rolling_avg_OBP', 'park_factor', 'temperature', 'game_pk', 'low_pa_flag'
    ]
    hitters = hitters[required_columns]
    logging.info(f"Selected required columns: {required_columns}")

    for col in required_columns:
        nans = hitters[col].isna().sum()
        if nans > 0:
            logging.warning(f"Found {nans} NaN values in {col}")

    out_h = os.path.join(DATA_DIR, 'finalize_hitter_features.csv')
    logging.info(f"Saving hitters → {out_h}")
    hitters.to_csv(out_h, index=False)

    logging.info("Done.")

if __name__ == '__main__':
    main()