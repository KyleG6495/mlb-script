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
    logging.info(f"Season columns: {list(season.columns)}")

    # 2) Load rolling‐5 game features
    rolling_fn = os.path.join(DATA_DIR, "hitter_rolling_5game_features.csv")
    logging.info(f"📂 Rolling 5-game features: loading {rolling_fn}")
    rolling = pd.read_csv(rolling_fn)
    logging.info(f" → {len(rolling):,} rows")
    logging.info(f"Rolling columns: {list(rolling.columns)}")

    # 3) Load daily features
    daily_fn = os.path.join(DATA_DIR, "fd_hitter_features_today.csv")
    logging.info(f"📂 Daily features: loading {daily_fn}")
    daily = pd.read_csv(daily_fn)
    logging.info(f" → {len(daily):,} rows")
    logging.info(f"Daily columns: {list(daily.columns)}")

    # Check what columns are available for merging
    common_season_rolling = set(season.columns) & set(rolling.columns)
    common_daily_rolling = set(daily.columns) & set(rolling.columns)
    
    logging.info(f"Common columns (season ∩ rolling): {common_season_rolling}")
    logging.info(f"Common columns (daily ∩ rolling): {common_daily_rolling}")
    
    # Determine merge keys based on available columns
    if 'player_id' in common_season_rolling and 'date' in common_season_rolling:
        season_merge_keys = ['player_id', 'date']
    elif 'player_id' in common_season_rolling:
        season_merge_keys = ['player_id']
    else:
        logging.error("❌ No common merge keys found between season and rolling data")
        return
        
    logging.info(f"Using merge keys for season: {season_merge_keys}")

    # Coerce all date columns to datetime
    for df, name in [(season, "season"), (rolling, "rolling5"), (daily, "daily")]:
        if "date" in df.columns:
            logging.info(f"🔄 Coercing {name}.date to datetime")
            df["date"] = pd.to_datetime(df["date"])

    # 4) Merge season → rolling based on available keys
    logging.info(f"🔗 Merging season → rolling on {season_merge_keys}")
    merged = rolling.merge(
        season,
        on=season_merge_keys,
        how="left",
        suffixes=("", "_season")
    )
    logging.info(f" → After season merge: {merged.shape}")

    # 5) Determine merge keys for daily merge
    if 'player_id' in common_daily_rolling and 'date' in common_daily_rolling:
        daily_merge_keys = ['player_id', 'date']
    elif 'player_id' in common_daily_rolling:
        daily_merge_keys = ['player_id']
    else:
        logging.error("❌ No common merge keys found between daily and rolling data")
        return
        
    logging.info(f"Using merge keys for daily: {daily_merge_keys}")

    # 6) Merge that result → daily based on available keys
    logging.info(f"🔗 Merging above → daily on {daily_merge_keys}")
    final = daily.merge(
        merged,
        on=daily_merge_keys,
        how="left",
        suffixes=("", "_roll")
    )
    logging.info(f" → After rolling merge: {final.shape}")

    # 7) Save
    out_fn = os.path.join(DATA_DIR, "today_hitter_features_merged.csv")
    logging.info(f"💾 Saving merged dataframe → {out_fn}")
    final.to_csv(out_fn, index=False)

    logging.info("🎉 Done.")


if __name__ == "__main__":
    main()
