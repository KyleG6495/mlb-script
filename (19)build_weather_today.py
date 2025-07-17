import pandas as pd
import requests
import logging
import time
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
OPENWEATHER_API_KEY = 'eb27f1689074b1163c5cf5a1fde8fa91'
HITTER_FILE = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_hitter_features_enriched.csv"
OUTPUT_FILE = r"../data/weather_today.csv"

# Static team coordinates fallback
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

# Map full team name (lower) to standardized code
NAME_TO_CODE = {
    'texas rangers': 'TEX',
    'pittsburgh pirates': 'PIT',
    'los angeles dodgers': 'LAD',
    'detroit tigers': 'DET',
    'san francisco giants': 'SF',
    'seattle mariners': 'SEA',
    'san diego padres': 'SD',
    'houston astros': 'HOU',
    'chicago white sox': 'CWS',
    'cleveland guardians': 'CLE',
    'oakland athletics': 'ATH',
    'colorado rockies': 'COL'
}


def get_weather(lat: float, lon: float) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=imperial"
    )
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        js = res.json()
        return {
            'temperature': js['main']['temp'],
            'wind_speed': js['wind']['speed'],
            'condition': js['weather'][0]['description'].title()
        }
    except requests.RequestException as e:
        logging.warning(f"Weather API failed for {lat},{lon}: {e}")
        return {'temperature': 75.0, 'wind_speed': 5.0, 'condition': 'Clear Sky'}


def main():
    # 1) Load data
    logging.info("📄 Loading hitter data from %s", HITTER_FILE)
    df = pd.read_csv(HITTER_FILE)
    logging.info("✅ Hitters loaded: %d rows", len(df))

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

    # 4) Direct extraction from 'Game' if present
    if 'Game' in df.columns:
        df['game_pk'] = pd.to_numeric(df['Game'], errors='coerce').fillna(0).astype(int)
        logging.info("Assigned 'game_pk' from 'Game'; %d unique values", df['game_pk'].nunique())
    else:
        df['game_pk'] = 0
        logging.info("No 'Game' column; initialized game_pk to 0")

    # 5) Fallback via schedule API
    game_pks = [pk for pk in df['game_pk'].unique() if pk > 0]
    if not game_pks:
        today = datetime.now().strftime("%Y-%m-%d")
        sched_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
        try:
            res = requests.get(sched_url, timeout=10)
            res.raise_for_status()
            games = res.json().get('dates', [])[0].get('games', [])
            logging.info("Schedule API returned %d games", len(games))
        except Exception as e:
            logging.warning("Schedule API error: %s", e)
            games = []

        pk_map = {}
        for g in games:
            pk = g.get('gamePk')
            for side in ('home', 'away'):
                full = g['teams'][side]['team']['name'].lower()
                code = NAME_TO_CODE.get(full)
                if code:
                    pk_map.setdefault(code, []).append(pk)
        df['game_pk'] = df['team_standardized'].map(lambda t: pk_map.get(t, [0])[0])
        game_pks = [pk for pk in df['game_pk'].unique() if pk > 0]
        logging.info("Fallback: found %d game_pks via schedule API", len(game_pks))

    # 6) Fetch weather per game_pk
    weather_records = []
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
        except Exception as e:
            logging.warning("Error fetching meta for %d: %s", pk, e)
            continue

        w = get_weather(lat, lon)
        weather_records.append({'game_pk': pk, **w})
        time.sleep(1)

    # 7) Save
    if weather_records:
        pd.DataFrame(weather_records).to_csv(OUTPUT_FILE, index=False)
        logging.info("💾 Weather data saved to %s", OUTPUT_FILE)
    else:
        logging.warning("No weather data to save.")


if __name__ == '__main__':
    main()
