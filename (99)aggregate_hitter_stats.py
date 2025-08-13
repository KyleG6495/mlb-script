#!/usr/bin/env python3
"""
(5) aggregate_hitter_stats.py
Enrich today’s FanDuel hitter slate with the correct game_pk (via name_key & fallback player_id),
weather, and park factors.
"""

import logging
from pathlib import Path
import pandas as pd

# ----------------------------
# Configuration
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent / "data"

INPUT_FD_SLATE = BASE_DIR / "fd_hitter_features_today.csv"
INPUT_ID_MAP   = BASE_DIR / "hitter_games_with_gamepk.csv"
INPUT_WEATHER  = BASE_DIR / "weather_today.csv"
INPUT_PARK     = BASE_DIR / "merged_weather_park.csv"  # adjust if needed
OUTPUT_FILE    = BASE_DIR / "fd_hitter_features_enriched.csv"

# ----------------------------
# Setup logging
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def normalize_name(s: pd.Series) -> pd.Series:
    return s.str.lower().str.strip()

def main():
    # 1) Load FD hitters
    logging.info(f"📄 Loading FD hitters → {INPUT_FD_SLATE}")
    df = pd.read_csv(INPUT_FD_SLATE, dtype={"player_id": str})
    logging.info(f"✅ Loaded {len(df)} rows")

    # 2) Drop any pitchers
    if "Position" in df.columns:
        before = len(df)
        df = df[~df["Position"].str.upper().str.startswith("P")].reset_index(drop=True)
        logging.info(f"✅ Filtered to hitters only: {len(df)} rows (dropped {before - len(df)})")

    # 3) Build name_key for merge
    df["name_key"] = normalize_name(df["First Name"] + " " + df["Last Name"])

    # 4) Load ID map and prepare
    logging.info(f"🔄 Loading ID map → {INPUT_ID_MAP}")
    id_map = pd.read_csv(INPUT_ID_MAP, dtype={"player_id": str})
    id_map["name_key"] = normalize_name(id_map["target_name"])
    id_map = id_map[["player_id", "name_key", "game_pk"]].drop_duplicates()

    # 5) First merge on name_key
    df = df.merge(
        id_map[["name_key", "game_pk"]],
        on="name_key",
        how="left",
        validate="many_to_one"
    )
    # 6) Fallback merge on player_id for any still-missing
    missing = df["game_pk"].isna()
    if missing.any():
        logging.info(f"ℹ️ {missing.sum()} rows missing after name_key merge; doing fallback on player_id")
        fallback = id_map.drop(columns="name_key").drop_duplicates(subset=["player_id"])
        df = df.merge(
            fallback,
            on="player_id",
            how="left",
            suffixes=("","_pid"),
            validate="many_to_one"
        )
        # fill in missing from fallback
        df.loc[df["game_pk"].isna(), "game_pk"] = df.loc[missing, "game_pk_pid"]
        df.drop(columns="game_pk_pid", inplace=True)

    # 7) Final missing check
    still_missing = df["game_pk"].isna().sum()
    if still_missing:
        logging.warning(f"⚠️ {still_missing}/{len(df)} rows STILL missing game_pk")
    else:
        logging.info("✅ All rows have a game_pk")

    # 8) Merge weather
    logging.info(f"🔄 Merging weather → {INPUT_WEATHER}")
    weather = pd.read_csv(INPUT_WEATHER)[["game_pk", "temperature", "wind_speed", "condition"]]
    df = df.merge(weather, on="game_pk", how="left", validate="many_to_one")

    # 9) Merge park factors
    logging.info(f"🔄 Merging park factors → {INPUT_PARK}")
    park_cols = ["game_pk","park_factor","1B","2B","3B","HR","SO","BB","GB","FB","LD","IFFB","FIP"]
    park = pd.read_csv(INPUT_PARK)[park_cols]
    df = df.merge(park, on="game_pk", how="left", validate="many_to_one")

    # 10) Mirror team_standardized if present
    if "team_standardized" in df.columns:
        df["team_standardized_weather"] = df["team_standardized"]
        df["Team_weather"] = df["team_standardized"]

    # 11) Save
    logging.info(f"✅ Saving enriched hitters → {OUTPUT_FILE}")
    df.to_csv(OUTPUT_FILE, index=False)
    logging.info("🎉 Enrichment complete.")

if __name__ == "__main__":
    main()
