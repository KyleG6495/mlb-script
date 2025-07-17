#!/usr/bin/env python3
import pandas as pd
import logging
import os
import datetime
import requests

# ── Setup logging ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── Paths & URLs ──
HITTER_FEATURES_PATH = "../data/fd_hitter_features_today.csv"
OUTPUT_PATH          = "../data/fd_hitter_features_with_game_pk.csv"
SCHEDULE_URL         = "https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}"

def fetch_schedule(date_str: str) -> pd.DataFrame:
    """Fetch today’s schedule and return a DataFrame with one row per (game_pk, team, date)."""
    url = SCHEDULE_URL.format(date=date_str)
    resp = requests.get(url)
    resp.raise_for_status()
    data = resp.json()

    rows = []
    for day in data.get("dates", []):
        for g in day.get("games", []):
            gp = g.get("gamePk")
            # MLB API v1 sometimes uses 'abbreviation' or 'triCode'
            away = g["teams"]["away"]["team"].get("abbreviation") or g["teams"]["away"]["team"].get("triCode")
            home = g["teams"]["home"]["team"].get("abbreviation") or g["teams"]["home"]["team"].get("triCode")
            rows.append({"game_pk": gp, "team": away, "date": date_str})
            rows.append({"game_pk": gp, "team": home, "date": date_str})

    sched = pd.DataFrame(rows)
    logging.info(f"📅 Fetched {len(sched)} schedule rows for {date_str}")
    # If a team has a doubleheader, it will appear twice; drop duplicates so merge is many→one
    dedup = sched.drop_duplicates(subset=["team", "date"])
    dropped = len(sched) - len(dedup)
    if dropped:
        logging.info(f"🗂 Dropped {dropped} duplicate team/date rows (doubleheaders)")
    return dedup

def main():
    # 1) Load hitters
    if not os.path.exists(HITTER_FEATURES_PATH):
        raise FileNotFoundError(f"Missing hitters features at {HITTER_FEATURES_PATH}")
    hitters = pd.read_csv(HITTER_FEATURES_PATH, dtype=str)
    logging.info(f"✅ Loaded hitters: {len(hitters)} rows; columns: {list(hitters.columns)}")

    # 2) Parse out player_id if needed
    if "player_id" not in hitters.columns and "Id" in hitters.columns:
        hitters["player_id"] = hitters["Id"].str.split("-", n=1).str[0]
        logging.info("ℹ️ Parsed 'player_id' from FD 'Id'")
    elif "player_id" in hitters.columns:
        logging.info("ℹ️ Using existing 'player_id'")
    else:
        raise KeyError("No 'player_id' or 'Id' column found in hitters features")

    # 3) Annotate today’s date
    today_str = datetime.date.today().isoformat()
    hitters["date"] = today_str

    # 4) Fetch & dedupe schedule
    sched = fetch_schedule(today_str)

    # 5) Standardize FD team codes → MLB triCodes
    if "Team" not in hitters.columns:
        raise KeyError("Hitters features missing 'Team' column")
    hitters["team_standardized"] = hitters["Team"]
    # If FD codes differ, you can apply a mapping:
    # fd2mlb = {"KC":"KCR","WSH":"WSN", ...}
    # hitters["team_standardized"] = hitters["Team"].map(fd2mlb).fillna(hitters["Team"])

    # 6) Merge schedule onto hitters
    merged = hitters.merge(
        sched,
        left_on=["team_standardized", "date"],
        right_on=["team", "date"],
        how="left",
        validate="many_to_one",
    )
    matched = merged["game_pk"].notna().sum()
    logging.info(f"🧮 game_pk matched: {matched}/{len(merged)} rows")

    # 7) Fill missing game_pk with -1 and cast to int
    merged["game_pk"] = merged["game_pk"].fillna(-1).astype(int)

    # 8) Save
    merged.to_csv(OUTPUT_PATH, index=False)
    logging.info(f"✅ Saved with game_pk → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
