import pandas as pd
import requests
from tqdm import tqdm
import time
import logging
from datetime import date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
INPUT_FILE = "../data/pitcher_games.csv"
OUTPUT_FILE = "../data/pitcher_boxscores_earned_runs.csv"

# Date range for scraping
START_DATE = "2025-03-27"  # Season start
END_DATE = date.today().strftime("%Y-%m-%d")  # Up to today

# Load pitcher names and IDs
logging.info(" Loading pitcher names and IDs...")
df = pd.read_csv(INPUT_FILE)
pitchers = df.dropna(subset=["target_name", "player_id"]).drop_duplicates(subset=["player_id"])
logging.info(f"SUCCESS: Loaded {len(pitchers)} pitchers")

# Define stat fields to extract
REQUIRED_STATS = [
    'strikeOuts', 'baseOnBalls', 'hits', 'doubles', 'triples', 'homeRuns',
    'atBats', 'outs', 'hitByPitch', 'sacFlies', 'sacBunts', 'wildPitches',
    'passedBall', 'wins', 'losses', 'noDecisions', 'earnedRuns'
]

# Helper to fetch pitcher game logs
def get_pitcher_game_logs(player_id, start_date=START_DATE, end_date=END_DATE):
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
        f"?stats=gameLog&group=pitching&sportId=1"
        f"&startDate={start_date}&endDate={end_date}"
    )
    try:
        res = requests.get(url)
        if res.status_code != 200:
            logging.warning(f"Failed to fetch data for player_id {player_id}: HTTP {res.status_code}")
            return None
        stats = res.json().get("stats", [])
        if not stats or not stats[0]["splits"]:
            logging.warning(f"No game logs for player_id {player_id}")
            return None
        return stats[0]["splits"]
    except Exception as e:
        logging.error(f"Error fetching game logs for player_id {player_id}: {str(e)}")
        return None

# Main loop
all_logs = []
for _, row in tqdm(pitchers.iterrows(), total=len(pitchers), desc="Fetching pitcher logs"):
    player_id = row["player_id"]
    name = row["target_name"]

    game_logs = get_pitcher_game_logs(player_id, START_DATE, END_DATE)
    if not game_logs:
        continue

    for entry in game_logs:
        raw = entry["stat"]
        record = {
            "name": name,
            "player_id": player_id,
            "date": entry["date"],
            "team": entry["team"]["name"],
            "opponent": entry["opponent"]["name"],
        }
        for field in REQUIRED_STATS:
            # Map API fields to desired output column names
            output_field = 'win' if field == 'wins' else \
                          'loss' if field == 'losses' else \
                          'no_decision' if field == 'noDecisions' else \
                          'earned_run' if field == 'earnedRuns' else field
            record[output_field] = raw.get(field, 0)
        all_logs.append(record)

    time.sleep(0.5)  # To avoid rate limiting

# Save to CSV
if all_logs:
    df_out = pd.DataFrame(all_logs)
    df_out.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"SUCCESS: Saved pitcher boxscores  {OUTPUT_FILE} ({len(df_out)} rows)")
else:
    logging.warning("WARNING: No data scraped.")