import pandas as pd
import numpy as np
import logging
from datetime import date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Compute current year and today string
current_year = date.today().year
today_str = date.today().isoformat()  # 'YYYY-MM-DD'

# File paths - Use the file that actually contains batting statistics
INPUT_PATH = "../data/hitter_rolling_5game_features.csv"  # This file has real MLB batting stats
OUTPUT_PATH = f"../data/aggregated_hitter_features_{current_year}.csv"

# Load hitter data with batting statistics
logging.info(f"📥 Loading hitter batting data from {INPUT_PATH}")
try:
    df = pd.read_csv(INPUT_PATH)
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter to recent data only (last 60 days) to get current season stats
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=60)
    df = df[df['date'] >= cutoff_date]
    
    logging.info(f"✅ Loaded {len(df)} recent batting records for {df['name'].nunique()} players")
    
    # Check for required columns
    required_cols = ['player_id', 'name', 'atBats', 'hits', 'homeRuns']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logging.error(f"❌ Missing required columns: {missing_cols}")
        raise ValueError(f"Required columns missing: {missing_cols}")
        
except FileNotFoundError:
    logging.error(f"❌ Input file not found: {INPUT_PATH}")
    raise
OUTPUT_PATH = f"../data/aggregated_hitter_features_{current_year}.csv"

# Load hitter data
logging.info(f" Loading hitter data from {INPUT_PATH}")
df = pd.read_csv(INPUT_PATH)

# Drop rows missing key fields
df = df.dropna(subset=["player_id", "atBats"])

# Convert numeric fields safely
numeric_cols = [
    "atBats", "hits", "doubles", "triples", "homeRuns", "baseOnBalls", "hitByPitch", "sacFlies"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Compute totalBases from component hits
df["singles"] = df["hits"] - df["doubles"] - df["triples"] - df["homeRuns"]
df["totalBases"] = (
    df["singles"]
    + 2 * df["doubles"]
    + 3 * df["triples"]
    + 4 * df["homeRuns"]
)

# Group and aggregate
agg = df.groupby(["player_id", "name"]).agg({
    "atBats": "sum",
    "hits": "sum",
    "doubles": "sum",
    "triples": "sum",
    "homeRuns": "sum",
    "baseOnBalls": "sum",
    "hitByPitch": "sum",
    "sacFlies": "sum",
    "totalBases": "sum"
}).reset_index()

# Attach date and season columns
agg["date"] = today_str
agg["Season"] = current_year

# Compute advanced stats
agg["AVG"] = agg["hits"] / agg["atBats"].replace({0: np.nan})
agg["OBP"] = (agg["hits"] + agg["baseOnBalls"] + agg["hitByPitch"]) / (
    agg["atBats"] + agg["baseOnBalls"] + agg["hitByPitch"] + agg["sacFlies"]
).replace({0: np.nan})
agg["SLG"] = agg["totalBases"] / agg["atBats"].replace({0: np.nan})
agg["OPS"] = agg["OBP"] + agg["SLG"]

# Reorder columns
final_cols = [
    "player_id", "name", "date", "Season", "AVG", "OBP", "SLG", "OPS",
    "atBats", "hits", "doubles", "triples", "homeRuns", "baseOnBalls", "hitByPitch", "sacFlies", "totalBases"
]
df_final = agg[final_cols]

# Save
logging.info(f" Saving aggregated hitter features  {OUTPUT_PATH}")
df_final.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved hitter features with {len(df_final)} rows")
