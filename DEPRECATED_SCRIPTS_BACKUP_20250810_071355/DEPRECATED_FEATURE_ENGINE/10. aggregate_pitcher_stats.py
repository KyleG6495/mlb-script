import pandas as pd
import numpy as np
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

INPUT_PATH = "../data/pitcher_boxscores_earned_runs.csv"  # Fix input filename
OUTPUT_PATH = "../data/pitcher_features_aggregated.csv"   # Different output name

# Load pitcher data
logging.info(f"📥 Loading pitcher data from {INPUT_PATH}")
df = pd.read_csv(INPUT_PATH)

# Rename columns for consistency
rename_map = {
    "strikeOuts": "strikeout",
    "baseOnBalls": "walk",
    "hits": "hit",
    "doubles": "double",
    "triples": "triple",
    "homeRuns": "home_run",
    "outs": "outs_recorded",
    "hitByPitch": "hit_by_pitch",
    "sacFlies": "sac_fly",
    "sacBunts": "sac_bunt",
    "wildPitches": "wild_pitch",
    "passedBall": "passed_ball"
}
df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

# Ensure necessary columns are present
required_cols = [
    "player_id", "name", "earned_run", "strikeout", "walk", "hit", "double", "triple", "home_run",
    "outs_recorded", "hit_by_pitch", "sac_fly", "sac_bunt", "wild_pitch", "passed_ball"
]
missing = [col for col in required_cols if col not in df.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")

# Drop rows missing key fields
df = df.dropna(subset=["player_id", "earned_run", "outs_recorded"])

# Convert columns to numeric where necessary
for col in required_cols[2:]:  # Skip player_id and name
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

# Aggregate stats by player
agg = df.groupby(["player_id", "name"]).agg({
    "earned_run": "sum",
    "strikeout": "mean",
    "walk": "mean",
    "hit": "mean",
    "double": "mean",
    "triple": "mean",
    "home_run": "mean",
    "outs_recorded": "sum",  # Needed for correct innings calculation
    "hit_by_pitch": "mean",
    "sac_fly": "mean",
    "sac_bunt": "mean",
    "wild_pitch": "mean",
    "passed_ball": "mean"
}).reset_index()

# Calculate innings and advanced stats
agg["innings"] = agg["outs_recorded"] / 3
agg["ERA"] = (agg["earned_run"] / agg["innings"]) * 9
agg["WHIP"] = (agg["walk"] + agg["hit"]) / agg["innings"]
agg["FIP"] = ((13 * agg["home_run"] + 3 * agg["walk"] - 2 * agg["strikeout"]) / agg["innings"]) + 3.2

agg["starter_K_rate"] = agg["strikeout"] / agg["innings"]
agg["starter_BB_rate"] = agg["walk"] / agg["innings"]
agg["avg_innings"] = agg["innings"]

# Final output
final_cols = [
    "player_id", "name", "ERA", "WHIP", "FIP", "starter_K_rate", "starter_BB_rate", "avg_innings",
    "strikeout", "walk", "hit", "double", "triple", "home_run", "outs_recorded",
    "hit_by_pitch", "sac_fly", "sac_bunt", "wild_pitch", "passed_ball"
]
df_final = agg[final_cols]

# Save output
df_final.to_csv(OUTPUT_PATH, index=False)
logging.info(f"✅ Saved pitcher features → {OUTPUT_PATH} with {len(df_final)} rows")
