# (7)build_rolling_pitcher_features.py

import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INPUT_PATH = "../data/pitcher_boxscores_earned_runs.csv"  # Fix filename
OUTPUT_PATH = "../data/pitcher_rolling_5game_features.csv"

# Load pitcher game logs
logging.info(f" Loading pitcher box scores from {INPUT_PATH}")
df = pd.read_csv(INPUT_PATH)

# Ensure correct date format and sort
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["player_id", "date"])
df = df.sort_values(by=["player_id", "date"])

# Columns to average
rolling_cols = [
    "strikeOuts", "baseOnBalls", "hits", "doubles", "triples", "homeRuns", "outs",
    "hitByPitch", "sacFlies", "sacBunts", "wildPitches", "passedBall", "earned_run"
]

# Ensure all columns are numeric
for col in rolling_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Compute rolling averages over the last 5 games
rolling = (
    df.groupby("player_id")[rolling_cols]
    .rolling(window=5, min_periods=1)
    .mean()
    .reset_index()
)

# Add back player name and date
rolling["date"] = df["date"].values
rolling["name"] = df["name"].values

# Reorder columns for clarity
rolling = rolling[["player_id", "name", "date"] + rolling_cols]

# Save result
rolling.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved rolling 5-game averages  {OUTPUT_PATH} with {len(rolling)} rows")
