import pandas as pd
import numpy as np
import logging
from datetime import date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Compute current year and today string
current_year = date.today().year
today_str = date.today().isoformat()  # 'YYYY-MM-DD'

# File paths - Use the file that actually contains pitcher statistics
INPUT_PATH = "../data/pitcher_rolling_5game_features.csv"  # This file has real MLB pitcher stats
OUTPUT_PATH = f"../data/aggregated_pitcher_features_{current_year}.csv"

# Load pitcher data with pitching statistics
logging.info(f"Loading pitcher data from {INPUT_PATH}")
try:
    df = pd.read_csv(INPUT_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter to recent data only (last 60 days) to get current season stats
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=60)
    df = df[df['date'] >= cutoff_date]
    
    logging.info(f"Loaded {len(df)} recent pitching records for {df['name'].nunique()} pitchers")
    
except FileNotFoundError:
    logging.error(f"Input file not found: {INPUT_PATH}")
    raise

# Drop rows missing key fields
df = df.dropna(subset=["player_id", "innings"])

# Convert numeric fields safely
numeric_cols = [
    "innings", "strikeOuts", "walks", "hits", "homeRuns", "earnedRuns"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Group and aggregate
agg_dict = {
    "innings": "sum",
    "strikeOuts": "sum", 
    "walks": "sum",
    "hits": "sum",
    "homeRuns": "sum",
    "earnedRuns": "sum"
}

# Only aggregate columns that exist
agg_dict = {k: v for k, v in agg_dict.items() if k in df.columns}

agg = df.groupby(["player_id", "name"]).agg(agg_dict).reset_index()

# Attach date and season columns
agg["date"] = today_str
agg["Season"] = current_year

# Compute advanced pitcher stats
agg["ERA"] = (agg["earnedRuns"] * 9) / agg["innings"].replace({0: np.nan})
if "walks" in agg.columns:
    agg["WHIP"] = (agg["walks"] + agg["hits"]) / agg["innings"].replace({0: np.nan})
    agg["BB_rate"] = agg["walks"] / agg["innings"].replace({0: np.nan})
agg["K_rate"] = agg["strikeOuts"] / agg["innings"].replace({0: np.nan})

# Reorder columns
final_cols = [
    "player_id", "name", "date", "Season", "ERA", "WHIP", "K_rate", "BB_rate",
    "innings", "strikeOuts", "walks", "hits", "homeRuns", "earnedRuns"
]

# Only use columns that exist
final_cols = [col for col in final_cols if col in agg.columns]
df_final = agg[final_cols]

# Save
logging.info(f"Saving aggregated pitcher features → {OUTPUT_PATH}")
df_final.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved pitcher features with {len(df_final)} rows")
