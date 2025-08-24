import pandas as pd
import requests
import logging
import time
from datetime import datetime

# Import centralized configuration
from config import (
    OPENWEATHER_API_KEY,
    TEAM_COORDINATES, 
    TEAM_NAME_TO_CODE,
    FilePaths,
    WeatherDefaults,
    LoggingConfig
)

# Setup logging from config
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LEVEL),
    format=LoggingConfig.FORMAT,
    datefmt=LoggingConfig.DATE_FORMAT
)

# File paths from configuration
HITTER_FILE = FilePaths.HITTER_FEATURES_ENRICHED
OUTPUT_FILE = FilePaths.WEATHER_TODAY


def get_weather(lat: float, lon: float) -> dict:
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=imperial"
    )
    try:
        res = requests.get(url, timeout=WeatherDefaults.API_TIMEOUT)
        res.raise_for_status()
        js = res.json()
        return {
            'temperature': js['main']['temp'],
            'wind_speed': js['wind']['speed'],
            'condition': js['weather'][0]['description'].title()
        }
    except requests.RequestException as e:
        logging.warning(f"Weather API failed for {lat},{lon}: {e}")
        return {
            'temperature': WeatherDefaults.TEMPERATURE, 
            'wind_speed': WeatherDefaults.WIND_SPEED, 
            'condition': WeatherDefaults.CONDITION
        }


def main():
    # 1) Load data
    logging.info("📄 Loading hitter data from %s", HITTER_FILE)
    df = pd.read_csv(HITTER_FILE)
    logging.info("✅ Hitters loaded: %d rows", len(df))

    # 2) Ensure name_key exists
    if 'name_key' not in df.columns and {'First Name', 'Last Name'}.issubset(df.columns):
        df['name_key'] = df['First Name'].astype(str).str.strip() + ' ' + df['Last Name'].astype(str).str.strip()
        logging.info("Created 'name_key'")

    # 3) Standardize team column to abbreviations
    if 'Team' in df.columns:
        df['team_standardized'] = df['Team'].astype(str).str.strip().str.upper()
    elif 'team' in df.columns:
        df['team_standardized'] = df['team'].astype(str).str.strip().str.upper()
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
                code = TEAM_NAME_TO_CODE.get(full)
                if code:
                    pk_map.setdefault(code, []).append(pk)
        df['game_pk'] = df['team_standardized'].map(lambda t: pk_map.get(t, [0])[0])
        game_pks = [pk for pk in df['game_pk'].unique() if pk > 0]
        logging.info("Fallback: found %d game_pks via schedule API", len(game_pks))

    # 6) Fetch weather per game_pk
    weather_records = []
    for pk in game_pks:
        try:
            meta = requests.get(f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live", timeout=WeatherDefaults.API_TIMEOUT)
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
        time.sleep(WeatherDefaults.API_DELAY_SECONDS)

    # 7) Save
    if weather_records:
        pd.DataFrame(weather_records).to_csv(OUTPUT_FILE, index=False)
        logging.info("💾 Weather data saved to %s", OUTPUT_FILE)
    else:
        logging.warning("No weather data to save.")


if __name__ == '__main__':
    main()
