#!/usr/bin/env python
import logging
import os
import pandas as pd
from config import FilePaths

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y%m%d %H:%M:%S"
)

# Using configuration paths
DATA_DIR = FilePaths.DATA_DIR


def main():
    # 1) Load season‐level features (now fd_hitter_features_enriched.csv)
    season_fn = FilePaths.FD_HITTER_FEATURES_ENRICHED
    logging.info(f"📂 Season features: loading {season_fn}")
    season = pd.read_csv(season_fn)
    logging.info(f" → {len(season):,} rows")

    # 2) Load rolling‐5 game features
    rolling_fn = FilePaths.HITTER_ROLLING_5GAME_FEATURES
    logging.info(f"📂 Rolling 5-game features: loading {rolling_fn}")
    rolling = pd.read_csv(rolling_fn)
    logging.info(f" → {len(rolling):,} rows")

    # 3) Load daily features
    daily_fn = FilePaths.FD_HITTER_FEATURES_TODAY
    logging.info(f"📂 Daily features: loading {daily_fn}")
    daily = pd.read_csv(daily_fn)
    logging.info(f" → {len(daily):,} rows")

    # Coerce all date columns to datetime
    for df, name in [(season, "season"), (rolling, "rolling5"), (daily, "daily")]:
        if "date" in df.columns:
            logging.info(f"🔄 Coercing {name}.date to datetime")
            df["date"] = pd.to_datetime(df["date"])
        else:
            logging.info(f"⚠️ No 'date' column in {name} data. Available columns: {list(df.columns)}")

    # 4) Merge season → rolling on player_id & date (if both have date column)
    logging.info("🔗 Merging season → rolling")
    if "date" in season.columns and "date" in rolling.columns:
        logging.info("Merging on ['player_id','date']")
        merged = rolling.merge(
            season,
            on=["player_id", "date"],
            how="left",
            suffixes=("", "_season")
        )
    elif "player_id" in season.columns and "player_id" in rolling.columns:
        logging.info("Merging on ['player_id'] only (no date available)")
        merged = rolling.merge(
            season,
            on=["player_id"],
            how="left",
            suffixes=("", "_season")
        )
    else:
        logging.warning("⚠️ Cannot merge season and rolling data - no common columns")
        merged = rolling.copy()
    logging.info(f" → After season merge: {merged.shape}")

    # 5) Merge that result → daily on player_id & date (if available)
    logging.info("🔗 Merging above → daily")
    if "date" in daily.columns and "date" in merged.columns:
        logging.info("Merging on ['player_id','date']")
        final = daily.merge(
            merged,
            on=["player_id", "date"],
            how="left",
            suffixes=("", "_roll")
        )
    elif "player_id" in daily.columns and "player_id" in merged.columns:
        logging.info("Merging on ['player_id'] only (no date available)")
        final = daily.merge(
            merged,
            on=["player_id"],
            how="left",
            suffixes=("", "_roll")
        )
    else:
        logging.warning("⚠️ Cannot merge daily and merged data - no common columns")
        final = daily.copy()
    logging.info(f" → After rolling merge: {final.shape}")

    # 6) Save
    out_fn = os.path.join(DATA_DIR, "today_hitter_features_merged.csv")
    logging.info(f"💾 Saving merged dataframe → {out_fn}")
    final.to_csv(out_fn, index=False)

    logging.info("🎉 Done.")


if __name__ == "__main__":
    main()
