import pandas as pd
import requests
import logging
import time
from datetime import datetime, date
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
OPENWEATHER_API_KEY = 'eb27f1689074b1163c5cf5a1fde8fa91'
HITTER_FILE = "data/fd_slate_starters_only.csv"
OUTPUT_FILE = "data/weather_today.csv"

# Allow date override via command line
if len(sys.argv) > 1:
    target_date = sys.argv[1]
else:
    target_date = date.today().strftime("%Y-%m-%d")

# Static team coordinates fallback (same as before)
TEAM_COORDINATES = {
    108: {'lat': 33.8003, 'lon': -117.8827},  # Los Angeles Angels
    109: {'lat': 33.4455, 'lon': -112.0667},  # Arizona Diamondbacks
    110: {'lat': 39.2839, 'lon': -76.6217},   # Baltimore Orioles
    111: {'lat': 42.3467, 'lon': -71.0972},   # Boston Red Sox
    112: {'lat': 41.9484, 'lon': -87.6553},   # Chicago Cubs
    113: {'lat': 39.0979, 'lon': -84.5081},   # Cincinnati Reds
    114: {'lat': 41.4962, 'lon': -81.6853},   # Cleveland Guardians
    115: {'lat': 39.7561, 'lon': -104.9941},  # Colorado Rockies
    116: {'lat': 42.3390, 'lon': -83.0485},   # Detroit Tigers
    117: {'lat': 29.7572, 'lon': -95.3555},   # Houston Astros
    118: {'lat': 39.0513, 'lon': -94.4803},   # Kansas City Royals
    119: {'lat': 34.0738, 'lon': -118.2400},  # Los Angeles Dodgers
    120: {'lat': 38.8730, 'lon': -77.0074},   # Washington Nationals
    121: {'lat': 40.7571, 'lon': -73.8458},   # New York Mets
    133: {'lat': 37.7516, 'lon': -122.2005},  # Oakland Athletics
    134: {'lat': 40.4469, 'lon': -80.0057},   # Pittsburgh Pirates
    135: {'lat': 32.7076, 'lon': -117.1570},  # San Diego Padres
    136: {'lat': 47.5911, 'lon': -122.3331},  # Seattle Mariners
    137: {'lat': 37.7786, 'lon': -122.3893},  # San Francisco Giants
    138: {'lat': 38.6226, 'lon': -90.1928},   # St. Louis Cardinals
    139: {'lat': 27.7682, 'lon': -82.6534},   # Tampa Bay Rays
    140: {'lat': 32.7511, 'lon': -97.0821},   # Texas Rangers
    141: {'lat': 43.6414, 'lon': -79.3890},   # Toronto Blue Jays
    142: {'lat': 44.9817, 'lon': -93.2783},   # Minnesota Twins
    143: {'lat': 39.9050, 'lon': -75.1665},   # Philadelphia Phillies
    144: {'lat': 33.8908, 'lon': -84.4679},   # Atlanta Braves
    145: {'lat': 41.8300, 'lon': -87.6339},   # Chicago White Sox
    146: {'lat': 25.7781, 'lon': -80.2196},   # Miami Marlins
    147: {'lat': 40.8296, 'lon': -73.9262},   # New York Yankees
    158: {'lat': 43.0280, 'lon': -87.9712}    # Milwaukee Brewers
}

# Map full team name to abbreviation
TEAM_NAME_TO_ABBREV = {
    'Arizona Diamondbacks': 'ARI',
    'Atlanta Braves': 'ATL',
    'Baltimore Orioles': 'BAL',
    'Boston Red Sox': 'BOS',
    'Chicago Cubs': 'CHC',
    'Chicago White Sox': 'CWS',
    'Cincinnati Reds': 'CIN',
    'Cleveland Guardians': 'CLE',
    'Colorado Rockies': 'COL',
    'Detroit Tigers': 'DET',
    'Houston Astros': 'HOU',
    'Kansas City Royals': 'KC',
    'Los Angeles Angels': 'LAA',
    'Los Angeles Dodgers': 'LAD',
    'Miami Marlins': 'MIA',
    'Milwaukee Brewers': 'MIL',
    'Minnesota Twins': 'MIN',
    'New York Mets': 'NYM',
    'New York Yankees': 'NYY',
    'Oakland Athletics': 'OAK',
    'Philadelphia Phillies': 'PHI',
    'Pittsburgh Pirates': 'PIT',
    'San Diego Padres': 'SD',
    'San Francisco Giants': 'SF',
    'Seattle Mariners': 'SEA',
    'St. Louis Cardinals': 'STL',
    'Tampa Bay Rays': 'TB',
    'Texas Rangers': 'TEX',
    'Toronto Blue Jays': 'TOR',
    'Washington Nationals': 'WSN'
}

# Weather cache to avoid duplicate API calls
weather_cache = {}

def get_weather(lat: float, lon: float) -> dict:
    key = (round(lat, 4), round(lon, 4))
    if key in weather_cache:
        return weather_cache[key]
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=imperial"
    )
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        js = res.json()
        weather = {
            'temperature': js['main']['temp'],
            'humidity': js['main'].get('humidity'),
            'wind_speed': js['wind']['speed'],
            'wind_deg': js['wind'].get('deg'),
            'condition': js['weather'][0]['description'].title()
        }
        weather_cache[key] = weather
        return weather
    except requests.RequestException as e:
        logging.warning(f"Weather API failed for {lat},{lon}: {e}")
        fallback = {'temperature': 75.0, 'humidity': 50, 'wind_speed': 5.0, 'wind_deg': 0, 'condition': 'Clear Sky'}
        weather_cache[key] = fallback
        return fallback

def main():
    # 1) Load data
    logging.info(" Loading hitter data from %s", HITTER_FILE)
    try:
        df = pd.read_csv(HITTER_FILE)
        logging.info("SUCCESS: Hitters loaded: %d rows", len(df))
    except FileNotFoundError:
        logging.error(f"Hitter file not found: {HITTER_FILE}")
        logging.info("Creating sample data file for testing...")
        # Create a minimal sample file for testing
        sample_data = {
            'First Name': ['Test', 'Sample'],
            'Last Name': ['Player1', 'Player2'], 
            'Team': ['BOS', 'ATL'],
            'Game': ['BOS@ATL', 'BOS@ATL']
        }
        df = pd.DataFrame(sample_data)
        logging.info("Using sample data: %d rows", len(df))

    # 2) Ensure name_key exists
    if 'name_key' not in df.columns and {'First Name', 'Last Name'}.issubset(df.columns):
        df['name_key'] = df['First Name'].str.strip() + ' ' + df['Last Name'].str.strip()
        logging.info("Created 'name_key'")

    # 3) Standardize team column to abbreviations
    if 'Team' in df.columns:
        df['team_standardized'] = df['Team'].str.strip().str.upper()
    elif 'team' in df.columns:
        df['team_standardized'] = df['team'].str.strip().str.upper()
    else:
        logging.error("No team column found for standardization")
        raise KeyError("Cannot create 'team_standardized'")
    logging.info("Unique team_standardized codes: %s", df['team_standardized'].unique().tolist())

    # Filter out All-Star teams
    df = df[~df['team_standardized'].isin(['ALS', 'NLS'])]
    logging.info("Filtered out All-Star teams. Remaining rows: %d", len(df))

    # 4) Map FanDuel game matchups to MLB API game_pk values
    df['game_pk'] = 0  # Initialize
    
    # Get today's MLB schedule
    sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={target_date}"
    try:
        res = requests.get(sched_url, timeout=10)
        res.raise_for_status()
        games = res.json().get('dates', [])[0].get('games', [])
        logging.info("Schedule API returned %d games", len(games))
    except Exception as e:
        logging.warning("Schedule API error: %s", e)
        games = []

    # Create mapping from FanDuel game format to game_pk
    game_pk_map = {}
    for g in games:
        away_name = g['teams']['away']['team']['name']
        home_name = g['teams']['home']['team']['name']
        away_abbrev = TEAM_NAME_TO_ABBREV.get(away_name, away_name[:3].upper())
        home_abbrev = TEAM_NAME_TO_ABBREV.get(home_name, home_name[:3].upper())
        fd_game_format = f"{away_abbrev}@{home_abbrev}"
        game_pk_map[fd_game_format] = g['gamePk']
        logging.info(f"Mapped {fd_game_format} -> game_pk {g['gamePk']}")
    
    # Apply mapping to our FanDuel data
    if 'Game' in df.columns:
        df['game_pk'] = df['Game'].map(game_pk_map).fillna(0).astype(int)
        mapped_games = df[df['game_pk'] > 0]['Game'].nunique()
        logging.info(f"Successfully mapped {mapped_games} FanDuel games to game_pk values")
    
    game_pks = [pk for pk in df['game_pk'].unique() if pk > 0]
    logging.info(f"Final game_pks to process: {game_pks}")
    
    # Also process all FanDuel games directly using team coordinates
    unique_fd_games = df['Game'].dropna().unique() if 'Game' in df.columns else []
    logging.info(f"Processing all {len(unique_fd_games)} FanDuel games for weather")
    
    # Team abbreviation to coordinates mapping
    team_coord_map = {
        'BOS': 111, 'ATL': 144, 'SD': 135, 'CIN': 113, 'MIL': 158, 'TEX': 140,
        'LAD': 119, 'SEA': 136, 'NYY': 147, 'CHC': 112, 'TOR': 141, 'ARI': 109,
        'KC': 118, 'NYM': 121, 'TB': 139, 'CWS': 145, 'LAA': 108, 'CLE': 114,
        'STL': 138, 'COL': 115, 'ATH': 133, 'OAK': 133, 'MIN': 142, 'SF': 137
    }

    # 6) Fetch weather for all FanDuel games
    weather_records = []
    
    # First, get weather from mapped game_pks (if any)
    for pk in game_pks:
        try:
            meta = requests.get(f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live", timeout=10)
            meta.raise_for_status()
            venue = meta.json().get('gameData', {}).get('venue', {})
            lat = venue.get('venueLat')
            lon = venue.get('venueLon')
            if lat is None or lon is None:
                hid = meta.json().get('gameData', {}).get('teams', {}).get('home', {}).get('id')
                coords = TEAM_COORDINATES.get(hid)
                if coords:
                    lat, lon = coords['lat'], coords['lon']
                else:
                    logging.warning("Skipping game_pk %d: no coordinates", pk)
                    continue
            
            w = get_weather(lat, lon)
            weather_records.append({'game_pk': pk, **w})
            time.sleep(1)
        except Exception as e:
            logging.warning("Error fetching meta for %d: %s", pk, e)
            continue
    
    # Then, get weather for ALL FanDuel games using team coordinates
    for game in unique_fd_games:
        if '@' in game:
            away, home = game.split('@')
            home_team_id = team_coord_map.get(home.upper())
            
            if home_team_id and home_team_id in TEAM_COORDINATES:
                coords = TEAM_COORDINATES[home_team_id]
                w = get_weather(coords['lat'], coords['lon'])
                weather_records.append({'game': game, 'home_team': home, **w})
                logging.info(f"Got weather for {game} at {home}")
                time.sleep(1)
            else:
                logging.warning(f"No coordinates found for {game} (home team: {home})")

    # 7) Save
    if weather_records:
        pd.DataFrame(weather_records).to_csv(OUTPUT_FILE, index=False)
        logging.info(" Weather data saved to %s", OUTPUT_FILE)
    else:
        logging.warning("No weather data to save.")

if __name__ == '__main__':
    main()
