#!/usr/bin/env python3
"""
(3) assign_pitcher_game_pk.py
Map each pitcher to their most recent MLB game_pk using the MLB Stats API.
"""

import logging
from pathlib import Path
import pandas as pd
import datetime
import requests
from tqdm import tqdm
import json
from config import FilePaths, MLBApiConfig

# ----------------------------
# Configuration from config.py
# ----------------------------
DATA_DIR        = FilePaths.DATA_DIR
PITCHERS_FILE   = FilePaths.PITCHER_GAMES
OUTPUT_MAP      = FilePaths.PITCHER_GAMES_WITH_GAMEPK
FAILED_IDS_FILE = DATA_DIR / "failed_pitcher_ids.json"

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def fetch_game_pk(player_id: str, season: int) -> int | None:
    """
    Query MLB Stats API via /stats?stats=gameLog for a players pitching logs in the given season,
    return the gamePk for their most recent game (if any).
    """
    try:
        pid = str(int(float(player_id)))
    except Exception:
        logging.error(f"Invalid player_id '{player_id}'; skipping.")
        return None

    url = (
        f"{MLBApiConfig.BASE_URL}/people/{pid}/stats"
        f"?stats=gameLog&season={season}"  # Remove &group=pitching
    )
    resp = requests.get(url, timeout=MLBApiConfig.TIMEOUT)
    if resp.status_code != 200:
        logging.error(f"{resp.status_code} for player {pid}; skipping.")
        return None

    data = resp.json()
    stats = data.get("stats", [])
    if not stats or not stats[0].get("splits"):
        return None

    splits = stats[0]["splits"]
    if not splits:
        return None

    latest = splits[-1]
    # Check for gamePk in either stats or game dict
    if "stats" in latest and "gamePk" in latest["stats"]:
        return latest["stats"]["gamePk"]
    return latest.get("game", {}).get("gamePk")


def main():
    # 1) Load pitchers list
    pitchers = pd.read_csv(PITCHERS_FILE, dtype={"player_id": str})
    logging.info(f" Loaded {len(pitchers)} rows from {PITCHERS_FILE}")
    logging.info(f" Columns: {pitchers.columns.tolist()}")

    # Drop any rows lacking a player_id
    pitchers = pitchers.dropna(subset=["player_id"])
    logging.info(f" Dropped rows with missing player_id; {len(pitchers)} remaining")

    # 2) Determine season
    # always use current year to get this season's games
    season = 2024  # Use 2024 season data instead
    logging.info(f" Using season {season}")

    # 3) Fetch game_pks
    rows, failed = [], []
    logging.info(f"SWAP: Fetching most recent game_pk for {len(pitchers)} pitchers")
    for _, row in tqdm(pitchers.iterrows(), total=len(pitchers)):
        gp = fetch_game_pk(row["player_id"], season)
        if gp:
            rows.append({
                "target_name": row.get("target_name", ""),
                "player_id": str(int(float(row["player_id"]))),
                "game_pk": gp
            })
        else:
            failed.append(row["player_id"])

    # 4) Save failures
    logging.info(f"WARNING: {len(failed)} pitchers have no game_pk")
    if failed:
        logging.info(f" Saving failed IDs to {FAILED_IDS_FILE}")
        with open(FAILED_IDS_FILE, "w") as f:
            json.dump(failed, f, indent=2)

    # 5) Write mapping CSV
    pd.DataFrame(rows).to_csv(OUTPUT_MAP, index=False)
    logging.info(f"SUCCESS: Saved {len(rows)} rows to {OUTPUT_MAP}")


if __name__ == "__main__":
    main()

# Team Abbreviations Mapping
team_abbrev_mapping = {
    'ATH': 'OAK',
    'bluejays': 'TOR'
}
