#!/usr/bin/env python3
import logging
from pathlib import Path
import pandas as pd
import requests
import time

# Configure logging
time_format = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt=time_format)

# File paths
data_dir = Path(__file__).resolve().parent / ".." / "data"
hitter_map_file = data_dir / "hitter_team_map.csv"
pitcher_map_file = data_dir / "pitcher_team_map.csv"
schedule_output_file = data_dir / "game_schedules.csv"

# MLB Stats API endpoint for schedules
API_URL = "https://statsapi.mlb.com/api/v1/schedule"


def load_game_pks():
    """
    Load and combine all game_pk values from hitter and pitcher maps.
    Convert to string game_pk without decimal, drop duplicates.
    """
    logging.info(f"Loading game_pks from maps: {hitter_map_file.name}, {pitcher_map_file.name}")
    df_hit = pd.read_csv(hitter_map_file)
    df_pit = pd.read_csv(pitcher_map_file)

    # Concatenate and drop NaNs
    all_pks = pd.concat([df_hit, df_pit], axis=0)["game_pk"].dropna()

    # Convert float strings like '777169.0' to '777169'
    cleaned = all_pks.map(lambda x: str(int(float(x))) if not pd.isna(x) else None)
    unique_pks = sorted(set(cleaned.dropna()))
    logging.info(f"Found {len(unique_pks)} unique game_pks")
    return unique_pks


def fetch_schedule(game_pk: str) -> dict | None:
    """
    Fetch schedule details for a single game_pk from the MLB Stats API.
    Returns a dict with game_pk, game_date, home_team, away_team, venue.
    """
    params = {"sportId": 1, "gamePk": game_pk}
    try:
        resp = requests.get(API_URL, params=params, timeout=10)  # Add 10 second timeout
        resp.raise_for_status()
        data = resp.json()

        dates = data.get("dates", [])
        if not dates:
            return None
        games = dates[0].get("games", [])
        if not games:
            return None

        game = games[0]
        game_date = game.get("gameDate")
        teams = game.get("teams", {})
        home = teams.get("home", {}).get("team", {}).get("name")
        away = teams.get("away", {}).get("team", {}).get("name")
        venue = game.get("venue", {}).get("name")

        return {
            "game_pk": game_pk,
            "game_date": game_date,
            "home_team": home,
            "away_team": away,
            "venue": venue,
        }
    except requests.exceptions.Timeout:
        logging.error(f"Timeout fetching schedule for game_pk={game_pk}")
        return None
    except Exception as e:
        logging.error(f"Error fetching schedule for game_pk={game_pk}: {e}")
        return None


def main():
    # Load all game_pks to fetch
    game_pks = load_game_pks()

    schedules = []
    for pk in game_pks:
        try:
            sched = fetch_schedule(pk)
            if sched:
                schedules.append(sched)
            else:
                logging.warning(f"No schedule entry for game_pk={pk}")
        except Exception as e:
            logging.error(f"Error fetching schedule for {pk}: {e}")
        
        # Add rate limiting to avoid overwhelming the API
        time.sleep(0.5)  # 500ms delay between requests

    # Build DataFrame and save
    df_schedules = pd.DataFrame(schedules)
    df_schedules.to_csv(schedule_output_file, index=False)
    logging.info(f"Saved {len(df_schedules)} game schedules to {schedule_output_file}")


if __name__ == "__main__":
    main()
