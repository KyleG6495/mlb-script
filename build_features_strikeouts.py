import pandas as pd
import os

#  Paths 
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_FILE = os.path.join(DATA_DIR, "pitcher_boxscores_full.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "features_strikeouts.csv")

#  Load Data 
try:
    df = pd.read_csv(INPUT_FILE)
except FileNotFoundError:
    raise FileNotFoundError(f"ERROR: File not found: {INPUT_FILE}")

if df.empty:
    raise ValueError(" Input data is empty!")

#  Clean 
df = df.dropna(subset=["strikeOuts", "inningsPitched", "battersFaced", "earnedRuns", "hits", "baseOnBalls"])
df["game_pk"] = df["game_pk"].astype(str)

#  Compute Rolling Stats 
df["game_date"] = pd.to_datetime(df["game_pk"].str[:8], errors="coerce")  # crude, can improve
df = df.sort_values(["target_name", "game_date"])

grouped = df.groupby("target_name")
rolling_df = grouped[["strikeOuts", "inningsPitched", "battersFaced", "earnedRuns", "hits", "baseOnBalls"]].rolling(5).mean().reset_index()
rolling_df = rolling_df.rename(columns={
    "strikeOuts": "K_rolling5",
    "inningsPitched": "IP_rolling5",
    "battersFaced": "BF_rolling5",
    "earnedRuns": "ER_rolling5",
    "hits": "H_rolling5",
    "baseOnBalls": "BB_rolling5"
})

#  Merge back 
final_df = pd.merge(df, rolling_df, on=["level_1"], how="left")
final_df["ERA_rolling5"] = (final_df["ER_rolling5"] * 9) / final_df["IP_rolling5"]
final_df["WHIP_rolling5"] = (final_df["H_rolling5"] + final_df["BB_rolling5"]) / final_df["IP_rolling5"]

#  Output Features 
features = final_df[[
    "target_name", "game_pk", "K_rolling5", "IP_rolling5", "BF_rolling5",
    "ERA_rolling5", "WHIP_rolling5", "strikeOuts"
]].dropna()

features = features.rename(columns={
    "strikeOuts": "target"  # This is what we want to predict
})

features.to_csv(OUTPUT_FILE, index=False)
print(f"SUCCESS: Saved strikeout features  {OUTPUT_FILE} ({len(features)} rows)")
