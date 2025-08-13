import pandas as pd
import requests
from tqdm import tqdm
import time
import logging
from datetime import date

# ─── Configuration ───
INPUT_FILE  = "../data/hitter_games.csv"
OUTPUT_FILE = "../data/hitter_boxscores_full.csv"
START_DATE  = "2024-09-01"                        # your initial scrape start date
END_DATE    = date.today().strftime("%Y-%m-%d")   # dynamically set to today's date

# ─── Logging setup ───
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info(f"📅 Scrape hitter logs from {START_DATE} to {END_DATE}")

# ─── Load hitters ───
df = pd.read_csv(INPUT_FILE)
hitters = df.dropna(subset=["target_name", "player_id"]) \
            .drop_duplicates(subset=["player_id"])
logging.info(f"📋 Found {len(hitters)} unique hitters to scrape")

# ─── Stats fields ───
REQUIRED_STATS = [
    'strikeOuts','baseOnBalls','hits','doubles','triples','homeRuns',
    'atBats','runs','rbi','stolenBases','caughtStealing',
    'hitByPitch','sacFlies','sacBunts'
]

# ─── Fetch helper ───
def get_hitter_game_logs(player_id, start_date=START_DATE, end_date=END_DATE):
    url = (
        f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
        f"?stats=gameLog&group=hitting&sportId=1"
        f"&startDate={start_date}&endDate={end_date}"
    )
    logging.debug(f"GET {url}")
    r = requests.get(url)
    if r.status_code != 200:
        logging.warning(f"→ {player_id} returned HTTP {r.status_code}")
        return []
    stats = r.json().get("stats", [])
    if not stats or not stats[0].get("splits"):
        return []
    return stats[0]["splits"]

# ─── Main scraping loop ───
all_logs = []
for _, row in tqdm(hitters.iterrows(), total=len(hitters), desc="Scraping hitters"):
    pid  = int(row["player_id"])
    name = row["target_name"]

    splits = get_hitter_game_logs(pid)
    if not splits:
        continue

    for entry in splits:
        rec = {
            "name":       name,
            "player_id":  pid,
            "date":       entry["date"],
            "team":       entry["team"]["name"],
            "opponent":   entry["opponent"]["name"],
        }
        for f in REQUIRED_STATS:
            rec[f] = entry["stat"].get(f, 0)
        all_logs.append(rec)

    time.sleep(0.3)  # slight delay to be polite

# ─── Save results ───
if all_logs:
    out_df = pd.DataFrame(all_logs)
    out_df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"✅ Saved {len(out_df)} rows → {OUTPUT_FILE}")
else:
    logging.error("⚠️ No data scraped. Check debug logs for URL and response issues.")
