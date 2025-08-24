import pandas as pd
import logging
import os
import re
from fuzzywuzzy import process

# Import centralized configuration
from config import FilePaths, LoggingConfig, TEAM_STANDARDIZED_MAP
from player_data_config import TEAM_CORRECTIONS

# Setup logging from centralized config
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LEVEL),
    format=LoggingConfig.FORMAT,
    datefmt=LoggingConfig.DATE_FORMAT
)

# File paths from centralized config
SEASON_FILE = FilePaths.TODAY_PITCHER_FEATURES
ROLLING_FILE = FilePaths.PITCHER_ROLLING_FEATURES
TEAM_FILE = FilePaths.PITCHER_FEATURES_ENRICHED
ID_MAP_FILE = FilePaths.PITCHER_GAMES_WITH_GAMEPK
TEAM_MAP_FILE = FilePaths.DATA_DIR / "team_name_map.csv"
OUTPUT_FILE = FilePaths.DATA_DIR / "pitcher_features_merged.csv"

# Use team mappings from centralized configuration
team_standardized_map = TEAM_STANDARDIZED_MAP
team_corrections = TEAM_CORRECTIONS

# Normalize names
def normalize_name(name):
    if not name or pd.isna(name):
        return ''
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\b(jr\.?|sr\.?|ii|iii|iv)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z\s]', '', name)
    return name.strip()

# Load data files
logging.info(f"📥 Loading season features from {SEASON_FILE}")
try:
    season_df = pd.read_csv(SEASON_FILE)
    season_df['player_id'] = season_df['player_id'].astype(str)
    logging.info(f"season_df player_id dtype: {season_df['player_id'].dtype}")
    logging.info(f"Sample season_df player_id: {season_df['player_id'].head().tolist()}")
    name_col = 'name' if 'name' in season_df.columns else 'target_name' if 'target_name' in season_df.columns else None
    if name_col:
        logging.info(f"Sample season_df {name_col}: {season_df[name_col].head().tolist()}")
    else:
        logging.warning(f"No 'name' or 'target_name' column in season_df.")
except FileNotFoundError:
    logging.error(f"❌ Season file {SEASON_FILE} not found")
    exit(1)

# Check for Shane Bieber in season_df
bieber_in_season = season_df[season_df['player_id'] == '669203']
if bieber_in_season.empty:
    logging.warning("Shane Bieber (player_id 669203) not found in season_df")
else:
    logging.info(f"Shane Bieber found in season_df:\n{bieber_in_season[['player_id', name_col] if name_col else ['player_id']].to_string()}")

logging.info(f"📥 Loading rolling 5-game features from {ROLLING_FILE}")
try:
    rolling_df = pd.read_csv(ROLLING_FILE)
    rolling_df['player_id'] = rolling_df['player_id'].astype(str)
    logging.info(f"rolling_df player_id dtype: {rolling_df['player_id'].dtype}")
    logging.info(f"Sample rolling_df player_id: {rolling_df['player_id'].head().tolist()}")
except FileNotFoundError:
    logging.error(f"❌ Rolling file {ROLLING_FILE} not found")
    exit(1)

logging.info(f"📥 Loading team data from {TEAM_FILE}")
try:
    team_df = pd.read_csv(TEAM_FILE)
    logging.info(f"Columns in team_df: {team_df.columns.tolist()}")
    logging.info(f"Sample team_df rows:\n{team_df.head().to_string()}")
    logging.info(f"team_df player_id dtype: {team_df['player_id'].dtype}")
    logging.info(f"Sample team_df player_id: {team_df['player_id'].head().tolist()}")
    if team_df.empty:
        logging.error(f"team_df is empty. Please check the file: {TEAM_FILE}")
        raise ValueError("team_df is empty")
except FileNotFoundError:
    logging.error(f"❌ Team file {TEAM_FILE} not found")
    exit(1)

# Ensure name_key is string and handle NaN
if 'name_key' in team_df.columns:
    team_df['name_key'] = team_df['name_key'].fillna('').astype(str)
else:
    logging.warning("name_key column missing in team_df, creating from name")
    team_df['name_key'] = team_df['name'].apply(normalize_name).fillna('')

# Ensure team_standardized exists
if 'team_standardized' not in team_df.columns:
    logging.warning("team_standardized column missing in team_df, creating from Team")
    team_df['team_standardized'] = team_df['Team'].str.lower().map(team_standardized_map).fillna('')

# Check for Shane Bieber in team_df
bieber_in_team = team_df[team_df['name_key'] == 'shane bieber']
if bieber_in_team.empty:
    logging.warning("Shane Bieber not found in team_df")
else:
    logging.info(f"Shane Bieber found in team_df:\n{bieber_in_team[['player_id', 'name_key', 'team_standardized']].to_string()}")

# Check for invalid player_id values
if team_df['player_id'].isna().any():
    logging.warning(f"Found {team_df['player_id'].isna().sum()} NaN player_id values in team_df")
    logging.warning(f"Sample rows with NaN player_id:\n{team_df[team_df['player_id'].isna()][['player_id', 'name', 'team_standardized']].head().to_string()}")

# Load ID mapping file
logging.info(f"📥 Loading ID mapping file from {ID_MAP_FILE}")
try:
    id_map_df = pd.read_csv(ID_MAP_FILE)
    id_map_df['player_id'] = id_map_df['player_id'].astype(str)
    if 'game_pk' not in id_map_df.columns:
        logging.error(f"❌ game_pk column missing in {ID_MAP_FILE}. Please run the pitcher game_pk enrichment script.")
        exit(1)
    id_map_df['target_name'] = id_map_df['target_name'].apply(normalize_name)
    team_df['name_key'] = team_df['name_key'].apply(normalize_name)
    logging.info(f"Sample id_map_df:\n{id_map_df[['game_pk', 'target_name', 'player_id']].head().to_string()}")
except FileNotFoundError:
    logging.error(f"❌ ID mapping file {ID_MAP_FILE} not found")
    exit(1)

# Log duplicate FanDuel IDs
duplicate_fanduel_ids = team_df[team_df.duplicated(subset=['name_key'], keep=False) & (team_df['name_key'] != '')]
if not duplicate_fanduel_ids.empty:
    logging.warning(f"Found {len(duplicate_fanduel_ids)} duplicate FanDuel IDs in team_df:")
    logging.info(f"Sample duplicates:\n{duplicate_fanduel_ids[['player_id', 'name_key', 'team_standardized']].head().to_string()}")

# Merge team_df with id_map_df, preserving team_standardized
team_df = pd.merge(
    team_df,
    id_map_df[['game_pk', 'target_name', 'player_id']],
    left_on='name_key',
    right_on='target_name',
    how='left',
    suffixes=('_team', '_mlb')
)
team_df['player_id'] = team_df['player_id_mlb'].where(team_df['player_id_mlb'].notna(), team_df['player_id_team'])
team_df = team_df.drop(columns=['target_name', 'player_id_mlb', 'player_id_team'], errors='ignore')
if 'team_standardized_team' in team_df.columns:
    team_df['team_standardized'] = team_df['team_standardized_team']
    team_df = team_df.drop(columns=['team_standardized_team'], errors='ignore')
logging.info(f"Sample team_df after ID mapping:\n{team_df[['player_id', 'name_key', 'team_standardized', 'game_pk']].head().to_string()}")

# Check Shane Bieber after ID mapping
bieber_after_mapping = team_df[team_df['player_id'] == '669203']
if bieber_after_mapping.empty:
    logging.warning("Shane Bieber (player_id 669203) not found in team_df after ID mapping")
else:
    logging.info(f"Shane Bieber after ID mapping:\n{bieber_after_mapping[['player_id', 'name_key', 'team_standardized', 'game_pk']].to_string()}")

# Deduplicate team_df by player_id, prioritizing MLB IDs
team_df['is_mlb_id'] = team_df['player_id'].isin(id_map_df['player_id'])
team_df = team_df.sort_values(by='is_mlb_id', ascending=False).drop_duplicates(subset=['player_id'], keep='first').drop(columns=['is_mlb_id'])
logging.info(f"team_df rows after removing duplicate player_id (prioritizing MLB IDs): {len(team_df)}")

# Apply manual team corrections
for pid, team in team_corrections.items():
    team_df.loc[team_df['player_id'] == pid, 'team_standardized'] = team
logging.info(f"Applied manual team corrections for {len(team_corrections)} players")

# Check Shane Bieber after team corrections
bieber_after_corrections = team_df[team_df['player_id'] == '669203']
if bieber_after_corrections.empty:
    logging.warning("Shane Bieber (player_id 669203) not found in team_df after corrections")
else:
    logging.info(f"Shane Bieber after team corrections:\n{bieber_after_corrections[['player_id', 'name_key', 'team_standardized', 'game_pk']].to_string()}")

# Fallback for players in season_df but not team_df
missing_team_players = season_df[~season_df['player_id'].isin(team_df['player_id'])]
if not missing_team_players.empty:
    logging.warning(f"Found {len(missing_team_players)} players in season_df but not in team_df")
    logging.info(f"Sample missing players:\n{missing_team_players[['player_id', name_col] if name_col else ['player_id']].head().to_string()}")
    for pid, team in team_corrections.items():
        if pid in missing_team_players['player_id'].values:
            team_df = pd.concat([team_df, pd.DataFrame({'player_id': [pid], 'team_standardized': [team], 'name_key': ['shane bieber' if pid == '669203' else '']})], ignore_index=True)
    logging.info(f"team_df rows after adding missing players: {len(team_df)}")

# Select relevant columns for merge
team_df = team_df[['player_id', 'team_standardized', 'game_pk']].copy()
logging.info(f"Rows in team_df after mapping: {len(team_df)}")

# Load team name map if available
if os.path.exists(TEAM_MAP_FILE):
    logging.info(f"📥 Loading team name map from {TEAM_MAP_FILE}")
    team_map_df = pd.read_csv(TEAM_MAP_FILE)
    team_map_df['from'] = team_map_df['from'].str.strip().str.lower()
    team_map_df['to'] = team_map_df['to'].str.strip().str.lower()
    team_standardized_map = dict(zip(team_map_df['from'], team_map_df['to']))
else:
    logging.info("Team name map file not found. Using default mapping.")

# Check for duplicates in inputs
logging.info(f"Rows in season_df: {len(season_df)}")
season_duplicates = season_df.duplicated(subset=['player_id']).sum()
logging.info(f"Duplicate rows in season_df: {season_duplicates}")

logging.info(f"Rows in rolling_df before deduplication: {len(rolling_df)}")
if 'date' in rolling_df.columns:
    rolling_duplicates = rolling_df.duplicated(subset=['player_id', 'date']).sum()
    if rolling_duplicates > 0:
        logging.warning(f"Duplicate rows in rolling_df: {rolling_duplicates}")
        logging.info(f"Sample duplicates:\n{rolling_df[rolling_df.duplicated(subset=['player_id', 'date'], keep=False)][['player_id', 'date']].head().to_string()}")
    rolling_df = rolling_df.drop_duplicates(subset=['player_id', 'date'])
else:
    rolling_duplicates = rolling_df.duplicated(subset=['player_id']).sum()
    if rolling_duplicates > 0:
        logging.warning(f"Duplicate rows in rolling_df (by player_id only): {rolling_duplicates}")
    rolling_df = rolling_df.drop_duplicates(subset=['player_id'])
logging.info(f"Rows in rolling_df after deduplication: {len(rolling_df)}")

# Merge season and rolling features
logging.info("🔄 Merging season and rolling features")
merged_df = pd.merge(
    season_df,
    rolling_df.drop(columns=['name'], errors='ignore'),  # Avoid name column conflicts
    on=["player_id"],
    how="left",
    suffixes=('_season', '_rolling')
)
logging.info(f"merged_df player_id dtype after season+rolling merge: {merged_df['player_id'].dtype}")
logging.info(f"Sample merged_df player_id: {merged_df['player_id'].head().to_string()}")

# Check Shane Bieber in merged_df
bieber_in_merged = merged_df[merged_df['player_id'] == '669203']
if bieber_in_merged.empty:
    logging.warning("Shane Bieber (player_id 669203) not found in merged_df after season+rolling merge")
else:
    available_cols = []
    if 'player_id' in merged_df.columns:
        available_cols.append('player_id')
    if name_col in merged_df.columns:
        available_cols.append(name_col)
    if 'date' in merged_df.columns:
        available_cols.append('date')
    
    if available_cols:
        logging.info(f"Shane Bieber in merged_df:\n{bieber_in_merged[available_cols].head().to_string()}")
    else:
        logging.info(f"Shane Bieber in merged_df: {len(bieber_in_merged)} rows found")

# Remove duplicates by player_id and date (if date column exists)
logging.info(f"Rows before removing duplicates: {len(merged_df)}")
if 'date' in merged_df.columns:
    duplicates = merged_df.duplicated(subset=['player_id', 'date']).sum()
    if duplicates > 0:
        logging.warning(f"Duplicate rows in merged_df: {duplicates}")
        logging.info(f"Sample duplicates:\n{merged_df[merged_df.duplicated(subset=['player_id', 'date'], keep=False)][['player_id', 'date']].head().to_string()}")
    merged_df = merged_df.drop_duplicates(subset=['player_id', 'date'])
else:
    duplicates = merged_df.duplicated(subset=['player_id']).sum()
    if duplicates > 0:
        logging.warning(f"Duplicate rows in merged_df (by player_id only): {duplicates}")
        logging.info(f"Sample duplicates:\n{merged_df[merged_df.duplicated(subset=['player_id'], keep=False)][['player_id']].head().to_string()}")
    merged_df = merged_df.drop_duplicates(subset=['player_id'])
logging.info(f"Rows after removing duplicates: {len(merged_df)}")

# Merge with team data to add team_standardized and game_pk
logging.info("🔄 Merging with team data to add team_standardized and game_pk")
merged_df = pd.merge(
    merged_df,
    team_df[['player_id', 'team_standardized', 'game_pk']],
    on=['player_id'],
    how='left'
)

# Check Shane Bieber after team merge
bieber_after_team_merge = merged_df[merged_df['player_id'] == '669203']
if bieber_after_team_merge.empty:
    logging.warning("Shane Bieber (player_id 669203) not found in merged_df after team merge")
else:
    cols = ['player_id', name_col, 'team_standardized', 'game_pk'] if name_col in merged_df.columns else ['player_id', 'team_standardized', 'game_pk']
    logging.info(f"Shane Bieber after team merge:\n{bieber_after_team_merge[cols].head().to_string()}")

# Deduplicate merged_df after team merge
if 'date' in merged_df.columns:
    duplicates_after_team = merged_df.duplicated(subset=['player_id', 'date']).sum()
    if duplicates_after_team > 0:
        logging.warning(f"Duplicate rows after team merge: {duplicates_after_team}")
        logging.info(f"Sample duplicates:\n{merged_df[merged_df.duplicated(subset=['player_id', 'date'], keep=False)][['player_id', 'date']].to_string()}")
    merged_df = merged_df.drop_duplicates(subset=['player_id', 'date'])
else:
    duplicates_after_team = merged_df.duplicated(subset=['player_id']).sum()
    if duplicates_after_team > 0:
        logging.warning(f"Duplicate rows after team merge (by player_id only): {duplicates_after_team}")
    merged_df = merged_df.drop_duplicates(subset=['player_id'])
logging.info(f"Rows after removing duplicates post-team merge: {len(merged_df)}")

# Log merge results
matched_team_rows = merged_df['team_standardized'].notna().sum()
logging.info(f"Team merge results: {matched_team_rows} rows with team assigned, {len(merged_df) - matched_team_rows} rows with missing team")
matched_game_pk_rows = merged_df['game_pk'].notna().sum()
logging.info(f"Game PK merge results: {matched_game_pk_rows} rows with game_pk assigned, {len(merged_df) - matched_game_pk_rows} rows with missing game_pk")
if matched_game_pk_rows < len(merged_df):
    missing_game_pk = merged_df[merged_df['game_pk'].isna()]
    logging.warning(f"Sample rows with missing game_pk:\n{missing_game_pk[['player_id', name_col] if name_col in merged_df.columns else ['player_id']].head().to_string()}")

# Log unique teams and dates for debugging
logging.info(f"Unique teams in merged_df: {merged_df['team_standardized'].unique().tolist()}")
if 'date' in merged_df.columns:
    logging.info(f"Unique dates in merged_df: {sorted(merged_df['date'].dropna().unique().tolist())[:10]} (first 10)")
else:
    logging.info("No date column found in merged_df")

# Filter out rows with NaN dates
logging.info(f"Rows before filtering NaN dates: {len(merged_df)}")
if 'date' in merged_df.columns:
    merged_df = merged_df.dropna(subset=['date'])
    logging.info(f"Rows after filtering NaN dates: {len(merged_df)}")
else:
    logging.info("No date column found - skipping date filtering")
logging.info(f"Rows after filtering NaN dates: {len(merged_df)}")

# Save merged output
try:
    merged_df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"✅ Saved merged pitcher features → {OUTPUT_FILE} with {len(merged_df)} rows")
except Exception as e:
    logging.error(f"❌ Failed to save to {OUTPUT_FILE}: {e}")
    exit(1)