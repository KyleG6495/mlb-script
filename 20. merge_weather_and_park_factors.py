import pandas as pd
import requests
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to get home team from game_pk (if needed)
def get_home_team(game_pk):
    try:
        url = f"https://statsapi.mlb.com/api/v1/game/{game_pk}/boxscore"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        time.sleep(1)  # Avoid rate limits
        return data['teams']['home']['team']['name']
    except Exception as e:
        logger.error(f"Failed to fetch home team for game_pk {game_pk}: {e}")
        return None

# Team name mapping
team_mapping = {
    "Arizona Diamondbacks": "Diamondbacks",
    "Atlanta Braves": "Braves",
    "Baltimore Orioles": "Oriols",
    "Boston Red Sox": "Red Sox",
    "Chicago Cubs": "Cubs",
    "Chicago White Sox": "White Sox",
    "Cincinnati Reds": "Reds",
    "Cleveland Guardians": "Guardians",
    "Colorado Rockies": "Rockies",
    "Detroit Tigers": "Tigers",
    "Houston Astros": "Astros",
    "Kansas City Royals": "Royals",
    "Los Angeles Angels": "Angels",
    "Los Angeles Dodgers": "Dodgers",
    "Miami Marlins": "Marlins",
    "Milwaukee Brewers": "Brewers",
    "Minnesota Twins": "Twins",
    "New York Mets": "Mets",
    "New York Yankees": "Yankees",
    "Oakland Athletics": "OAK",
    "Philadelphia Phillies": "Phillies",
    "Pittsburgh Pirates": "Pirates",
    "San Diego Padres": "Padres",
    "San Francisco Giants": "Giants",
    "Seattle Mariners": "Mariners",
    "St. Louis Cardinals": "Cardinals",
    "Tampa Bay Rays": "Rays",
    "Texas Rangers": "Rangers",
    "Toronto Blue Jays": "Blue Jays",
    "Washington Nationals": "Nationals"
}

# Load data
logger.info("📥 Loading data files...")
weather = pd.read_csv("../data/weather_today.csv")
logger.info(f"✅ Loaded weather data: {len(weather)} rows")
logger.info(f"Weather columns: {weather.columns.tolist()}")
logger.info(f"Weather data sample:\n{weather.head().to_string()}")

# Add home_team if not present
if 'home_team' not in weather.columns:
    logger.info("🔄 Fetching home team for each game_pk...")
    weather['home_team'] = weather['game_pk'].apply(get_home_team)
    logger.info(f"Home teams added: {weather['home_team'].tolist()}")
    if weather['home_team'].isnull().any():
        logger.error("Some games are missing home team data")
        raise ValueError("Missing home team data for some games")

# Standardize team names
weather['home_team'] = weather['home_team'].map(team_mapping).fillna(weather['home_team'])

# Add team_standardized column by converting home_team to lowercase
weather['team_standardized'] = weather['home_team'].str.lower()

# Apply team name mapping if needed
team_mapping_lower = {
    'blue jays': 'bluejays',
    'red sox': 'redsox',
    'white sox': 'whitesox',
    # Add more mappings as needed
}

weather['team_standardized'] = weather['team_standardized'].map(team_mapping_lower).fillna(weather['team_standardized'])

park_factors = pd.read_csv("../park_factors/park_factors.csv")
logger.info(f"✅ Loaded park factor data: {len(park_factors)} rows")
logger.info(f"Park factor columns: {park_factors.columns.tolist()}")
logger.info(f"Park factor teams: {park_factors['Team'].unique().tolist()}")

# Validate columns
if 'home_team' not in weather.columns:
    logger.error("Column 'home_team' not found in weather data")
    raise KeyError("Column 'home_team' not found in weather data")
if 'Team' not in park_factors.columns:
    logger.error("Column 'Team' not found in park_factors data")
    raise KeyError("Column 'Team' not found in park_factors data")

# Merge data
try:
    merged_df = weather.merge(park_factors, left_on='home_team', right_on='Team', how='left')
    logger.info(f"✅ Merged data: {len(merged_df)} rows")
    # Log missing park factors
    missing_park = merged_df[merged_df['Team'].isnull()]
    if not missing_park.empty:
        logger.warning(f"Games without park factors: {missing_park['game'].tolist()}")
except KeyError as e:
    logger.error(f"Merge failed: {e}")
    raise

# Save output
merged_df.to_csv("../data/merged_weather_park.csv", index=False)
logger.info("✅ Saved merged data")