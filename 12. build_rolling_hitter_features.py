import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INPUT_PATH = "../data/hitter_boxscores_full.csv"
OUTPUT_PATH = "../data/hitter_rolling_5game_features.csv"

# Load hitter game logs
logging.info(f" Loading hitter box scores from {INPUT_PATH}")
df = pd.read_csv(INPUT_PATH)

# Ensure correct date format and sort
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df = df.dropna(subset=["player_id", "date"])
df = df.sort_values(by=["player_id", "date"])

# Define potential rolling columns and check which exist
all_rolling_cols = [
    "atBats", "hits", "homeRuns", "rbi", "runs", "baseOnBalls", "strikeOuts",
    "stolenBases", "caughtStealing", "totalBases", "hitByPitch", "sacFlies",
    "doubles", "triples", "team", "opponent", "sacBunts"
]
rolling_cols = [col for col in all_rolling_cols if col in df.columns]

# Log missing columns if any
missing = set(all_rolling_cols) - set(rolling_cols)
if missing:
    logging.warning(f"WARNING: Missing columns excluded from rolling stats: {missing}")

# Ensure numeric and clean
for col in rolling_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Compute 5-game rolling averages
rolling = (
    df.groupby("player_id")[rolling_cols]
    .rolling(window=5, min_periods=1)
    .mean()
    .reset_index()
)

# Restore date and name
rolling["date"] = df["date"].values
rolling["name"] = df["name"].values

# Save
rolling = rolling[["player_id", "name", "date"] + rolling_cols]
rolling.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved rolling 5-game averages  {OUTPUT_PATH} with {len(rolling)} rows")
