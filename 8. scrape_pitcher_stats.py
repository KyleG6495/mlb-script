import pandas as pd
import requests
from tqdm import tqdm
import time
from datetime import date

INPUT_FILE = "../data/pitcher_games.csv"
OUTPUT_FILE = "../data/pitcher_boxscores_full.csv"

# Define the date range for scraping
START_DATE = "2025-03-27"  # Approximate 2025 season start
END_DATE = date.today().strftime("%Y-%m-%d")  # Always up to today

# Load pitcher names and IDs
df = pd.read_csv(INPUT_FILE)
pitchers = df.dropna(subset=["target_name", "player_id"]).drop_duplicates(subset=["player_id"])

# Define stat fields to extract
REQUIRED_STATS = [
    'strikeOuts', 'baseOnBalls', 'hits', 'doubles', 'triples', 'homeRuns',
    'atBats', 'outs', 'hitByPitch', 'sacFlies', 'sacBunts', 'wildPitches',
    'passedBalls', 'wins', 'losses', 'noDecisions'
]

# Helper to fetch pitcher game logs
def get_pitcher_game_logs(player_id, start_date=START_DATE, end_date=END_DATE):
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
        f"?stats=gameLog&group=pitching&sportId=1"
        f"&startDate={start_date}&endDate={end_date}"
    )
    res = requests.get(url)
    if res.status_code != 200:
        return None
    stats = res.json().get("stats", [])
    if not stats or not stats[0]["splits"]:
        return None
    return stats[0]["splits"]

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
            record[field] = raw.get(field, 0)
        all_logs.append(record)

    time.sleep(0.5)  # To avoid rate limiting

# Save to CSV
if all_logs:
    df_out = pd.DataFrame(all_logs)
    df_out.to_csv(OUTPUT_FILE, index=False)
    print(f"SUCCESS: Saved pitcher boxscores  {OUTPUT_FILE} ({len(df_out)} rows)")
else:
    print("WARNING: No data scraped.")