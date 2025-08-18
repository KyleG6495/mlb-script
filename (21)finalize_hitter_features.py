import pandas as pd
import numpy as np
import logging
from datetime import date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Compute current year and today string
current_year = date.today().year
today_str = date.today().isoformat()  # 'YYYY-MM-DD'

# File paths
INPUT_PATH = "../data/today_hitter_features.csv"
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
