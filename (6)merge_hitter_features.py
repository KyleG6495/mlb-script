#!/usr/bin/env python
import logging
import os
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y%m%d %H:%M:%S"
)

SCRIPT_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(SCRIPT_DIR, "..", "data")


def main():
    # 1) Load season‐level features (now fd_hitter_features_enriched.csv)
    season_fn = os.path.join(DATA_DIR, "fd_hitter_features_enriched.csv")
    logging.info(f"📂 Season features: loading {season_fn}")
    season = pd.read_csv(season_fn)
    logging.info(f" → {len(season):,} rows")

    # 2) Load rolling‐5 game features
    rolling_fn = os.path.join(DATA_DIR, "hitter_rolling_5game_features.csv")
    logging.info(f"📂 Rolling 5-game features: loading {rolling_fn}")
    rolling = pd.read_csv(rolling_fn)
    logging.info(f" → {len(rolling):,} rows")

    # 3) Load daily features
    daily_fn = os.path.join(DATA_DIR, "fd_hitter_features_today.csv")
    logging.info(f"📂 Daily features: loading {daily_fn}")
    daily = pd.read_csv(daily_fn)
    logging.info(f" → {len(daily):,} rows")

    # Coerce all date columns to datetime
    for df, name in [(season, "season"), (rolling, "rolling5"), (daily, "daily")]:
        if "date" in df.columns:
            logging.info(f"🔄 Coercing {name}.date to datetime")
            df["date"] = pd.to_datetime(df["date"])

    # 4) Merge season → rolling on player_id & date
    logging.info("🔗 Merging season → rolling on ['player_id','date']")
    merged = rolling.merge(
        season,
        on=["player_id", "date"],
        how="left",
        suffixes=("", "_season")
    )
    logging.info(f" → After season merge: {merged.shape}")

    # 5) Merge that result → daily on player_id & date
    logging.info("🔗 Merging above → daily on ['player_id','date']")
    final = daily.merge(
        merged,
        on=["player_id", "date"],
        how="left",
        suffixes=("", "_roll")
    )
    logging.info(f" → After rolling merge: {final.shape}")

    # 6) Save
    out_fn = os.path.join(DATA_DIR, "today_hitter_features_merged.csv")
    logging.info(f"💾 Saving merged dataframe → {out_fn}")
    final.to_csv(out_fn, index=False)

    logging.info("🎉 Done.")


if __name__ == "__main__":
    main()
