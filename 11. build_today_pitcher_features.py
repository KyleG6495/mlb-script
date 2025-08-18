import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BOXSCORES_PATH = "../data/pitcher_boxscores_earned_runs.csv"  # Use the detailed pitcher data
FDSLATE_PATH = "C:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/fd_slate_today.csv"
OUTPUT_PATH = "../data/today_pitcher_features.csv"

# Load boxscores and FanDuel slate
logging.info(" Filtering only today's pitchers based on player_id match")
df_box = pd.read_csv(BOXSCORES_PATH)
df_slate = pd.read_csv(FDSLATE_PATH)

# Strip whitespace and normalize names
df_slate["Nickname"] = df_slate["Nickname"].str.strip()
df_box["name"] = df_box["name"].str.strip()

# Merge on name (FanDuel uses "Nickname")
df_merged = df_box.merge(df_slate, left_on="name", right_on="Nickname", how="inner")
df_merged = df_merged.dropna(subset=["player_id"])

# Save result
df_merged.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved  {OUTPUT_PATH} with {len(df_merged)} rows")
