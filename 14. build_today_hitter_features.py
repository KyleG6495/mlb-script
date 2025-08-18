import pandas as pd
import logging
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
HITTER_FILE = "../fd_current_slate/fd_slate_today.csv"  # Use FD slate with all data
ID_MAP_FILE = "../data/hitter_games_with_game_pk.csv"  # Add this line
WEATHER_PARK_FILE = "../data/merged_weather_park.csv"  # Add this line
OUTPUT_FILE = "../data/fd_hitter_features_enriched.csv"

# Team name normalization mapping
team_standardized_map = {
    'minnesota twins': 'twins',
    'los angeles dodgers': 'dodgers',
    'houston astros': 'astros',
    'atlanta braves': 'braves',
    'kansas city royals': 'royals',
    'san francisco giants': 'giants',
    'los angeles angels': 'angels',
    'colorado rockies': 'rockies',
    'detroit tigers': 'tigers',
    'cincinnati reds': 'reds',
    'arizona diamondbacks': 'diamondbacks',
    'new york mets': 'mets',
    'san diego padres': 'padres',
    'cleveland guardians': 'guardians',
    'oakland athletics': 'athletics',
    'boston red sox': 'redsox',
    'chicago white sox': 'whitesox',
    'toronto blue jays': 'bluejays',
    'tor': 'bluejays',
    'miami marlins': 'marlins',
    'seattle mariners': 'mariners',
    'washington nationals': 'nationals',
    'milwaukee brewers': 'brewers',
    'tampa bay rays': 'rays',
    'texas rangers': 'rangers',
    'baltimore orioles': 'orioles',
    'cws': 'whitesox',
    'pit': 'pirates'
}

# Manual team corrections
team_corrections = {
    '457759': 'mariners',  # Justin Turner
    '805779': 'athletics',  # Jacob Wilson
    '700932': 'guardians',  # Kyle Manzardo
    '701305': 'astros',    # Zach Dezenzo
    '543807': 'bluejays'   # George Springer
}

# Normalize names
def normalize_name(name):
    if not name or pd.isna(name):
        return ''
    name = str(name).lower().strip()
    name = re.sub(r'\s+', ' ', name)
    name = re.sub(r'\b(jr\.?|sr\.?|ii|iii|iv)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[^a-z\s]', '', name)
    return name.strip()

# Normalize FanDuel player_id to MLB ID
def normalize_fanduel_id(fanduel_id):
    if not fanduel_id or pd.isna(fanduel_id):
        return ''
    return str(fanduel_id).split('-')[-1]

# Load hitter data
logging.info(" Loading hitter data")
try:
    df_hitters = pd.read_csv(HITTER_FILE)
    logging.info(f"SUCCESS: Hitters: {len(df_hitters)} rows")
except FileNotFoundError:
    logging.error(f"ERROR: Hitter file {HITTER_FILE} not found")
    exit(1)

# Filter to hitters only (exclude pitchers)
if 'Position' in df_hitters.columns:
    df_hitters = df_hitters[~df_hitters['Position'].str.contains('P', na=False)]
    logging.info(f"Filtered to hitters only: {len(df_hitters)} rows")
else:
    logging.warning("WARNING: No 'Position' column to filter pitchers")

# Normalize player_id
logging.info(f"Available columns in hitter data: {df_hitters.columns.tolist()}")


# Apply team standardization
if 'Team' in df_hitters.columns:
    df_hitters['team_standardized'] = df_hitters['Team'].str.lower().map(team_standardized_map).fillna(df_hitters['Team'])
    logging.info("Applied team_standardized mapping to Team column")
if 'Opponent' in df_hitters.columns:
    df_hitters['opponent_standardized'] = df_hitters['Opponent'].str.lower().map(team_standardized_map).fillna(df_hitters['Opponent'])
    logging.info("Applied team_standardized mapping to Opponent column")
logging.info(f"Unique teams in df_hitters: {df_hitters['team_standardized'].unique().tolist()}")

# Create name_key
if 'First Name' in df_hitters.columns and 'Last Name' in df_hitters.columns:
    df_hitters['name_key'] = (df_hitters['First Name'].fillna('') + ' ' + df_hitters['Last Name'].fillna('')).apply(normalize_name)
    logging.info("Created name_key in df_hitters from First Name and Last Name")
else:
    logging.warning("WARNING: Missing First Name or Last Name columns in df_hitters")

# # Load ID mapping file with game_pk
# logging.info(f" Loading ID mapping file from {ID_MAP_FILE}")
# try:
#     id_map_df = pd.read_csv(ID_MAP_FILE)
#     id_map_df['player_id'] = id_map_df['player_id'].astype(str)
#     id_map_df['target_name'] = id_map_df['target_name'].apply(normalize_name)
#     logging.info(f"Sample id_map_df:\n{id_map_df[['game_pk', 'target_name', 'player_id']].head().to_string()}")
# except FileNotFoundError:
#     logging.error(f"ERROR: ID mapping file {ID_MAP_FILE} not found")
#     exit(1)

# # Merge with ID mapping to add game_pk
# df_hitters = pd.merge(
#     df_hitters,
#     id_map_df[['player_id', 'target_name', 'game_pk']],
#     left_on=['player_id', 'name_key'],
#     right_on=['player_id', 'target_name'],
#     how='left'
# )
# df_hitters = df_hitters.drop(columns=['target_name'], errors='ignore')
# logging.info(f"Sample df_hitters after ID mapping:\n{df_hitters[['player_id', 'name_key', 'team_standardized', 'game_pk']].head().to_string()}")

# Load hitter game_pk mapping
logging.info(" Loading hitter ID and game_pk mapping")
try:
    df_id_map = pd.read_csv(ID_MAP_FILE)
    logging.info(f"SUCCESS: ID Map: {len(df_id_map)} rows")
    
    # Normalize the target_name for matching
    df_id_map['name_key'] = df_id_map['target_name'].apply(normalize_name)
    logging.info(f"Sample ID map names: {df_id_map['name_key'].head().tolist()}")
    
except FileNotFoundError:
    logging.error(f"ERROR: ID map file {ID_MAP_FILE} not found")
    exit(1)

# Merge hitters with game_pk data BY NAME (not by player_id)
df_hitters = pd.merge(
    df_hitters,
    df_id_map[['name_key', 'game_pk', 'player_id']],
    on='name_key',
    how='left',
    suffixes=('_fd', '_mlb')  # Change this to ensure the suffix is applied
)
logging.info(f"SUCCESS: Merged hitters with game_pk data: {len(df_hitters)} rows")
logging.info(f"Hitters with game_pk: {df_hitters['game_pk'].notna().sum()}")

# Use the MLB player_id from the game_pk file
if 'player_id_mlb' in df_hitters.columns:
    df_hitters['player_id'] = df_hitters['player_id_mlb'].fillna(df_hitters.get('player_id_fd', df_hitters.get('player_id', '')))
    df_hitters = df_hitters.drop(columns=['player_id_mlb', 'player_id_fd'], errors='ignore')
else:
    logging.info("No player_id_mlb column found, keeping original player_id")

# Load weather and park factors
logging.info(" Loading weather and park factors data")
try:
    df_weather_park = pd.read_csv(WEATHER_PARK_FILE)
    logging.info(f"SUCCESS: Weather+Park: {len(df_weather_park)} rows")
except FileNotFoundError:
    logging.error(f"ERROR: Weather and park file {WEATHER_PARK_FILE} not found")
    exit(1)

# Normalize team_standardized in weather data
if 'team_standardized' in df_weather_park.columns:
    df_weather_park['team_standardized'] = df_weather_park['team_standardized'].str.lower().map(team_standardized_map).fillna(df_weather_park['team_standardized'])
    logging.info("Normalized team_standardized in df_weather_park")
logging.info(f"Unique teams in df_weather_park: {df_weather_park['team_standardized'].unique().tolist()}")

# Check for missing teams
missing_teams = set(df_hitters['opponent_standardized'].dropna()) - set(df_weather_park['team_standardized'].dropna())
if missing_teams:
    logging.warning(f"Teams in df_hitters['opponent_standardized'] not in df_weather_park: {missing_teams}")

# Merge hitters with weather and park data
logging.info("SWAP: Merging hitters with weather and park data")
df_final = pd.merge(
    df_hitters,
    df_weather_park,
    left_on='team_standardized',
    right_on='team_standardized',
    how='left',
    suffixes=('', '_weather')
)
logging.info(f"SUCCESS: Final merged: {len(df_final)} rows")

# Fill missing weather/park data with defaults
default_weather = {'temperature': 75.0, 'wind_speed': 5.0, 'condition': 'Clear Sky', 'Season': 2025}
default_park = {'park_factor': 100.0, '1B': 100.0, '2B': 100.0, '3B': 100.0, 'HR': 100.0, 'SO': 100.0, 'BB': 100.0, 'GB': 100.0, 'FB': 100.0, 'LD': 100.0, 'IFFB': 100.0, 'FIP': 100.0}
df_final = df_final.fillna({**default_weather, **default_park})
logging.info("Filled missing weather/park data with default values")

# Rename Id to player_id
if 'Id' in df_final.columns:
    df_final['player_id'] = df_final['Id']
    df_final = df_final.drop(columns=['Id'], errors='ignore')
    logging.info("Renamed Id to player_id in df_final")

# Apply manual team corrections
for pid, team in team_corrections.items():
    df_final.loc[df_final['player_id'] == pid, 'team_standardized'] = team
logging.info(f"Applied manual team corrections for {len(team_corrections)} players")

# Check George Springer after corrections
springer_after_corrections = df_final[df_final['player_id'] == '543807']
if springer_after_corrections.empty:
    logging.warning("George Springer (player_id 543807) not found in df_final after corrections")
else:
    logging.info(f"George Springer after corrections:\n{springer_after_corrections[['player_id', 'name_key', 'team_standardized', 'game_pk']].to_string()}")

# Log rows with default weather/park data
default_rows = df_final[df_final['temperature'] == 75.0]
if not default_rows.empty:
    logging.info(f"Found {len(default_rows)} rows with default weather/park data:")
    logging.info(f"Sample rows with default weather/park data:\n{default_rows[['player_id', 'name_key', 'team_standardized', 'game_pk']].head().to_string()}")