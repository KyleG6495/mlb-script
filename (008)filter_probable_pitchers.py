import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Paths
MERGED_FEATURES_PATH = "../data/pitcher_features_merged.csv"
FD_SLATE_PATH = "../fd_current_slate/fd_slate_today.csv"
OUTPUT_PATH = "../data/pitcher_features_probables.csv"

# Load data
logging.info(f" Loading merged pitcher features from {MERGED_FEATURES_PATH}")
df_merged = pd.read_csv(MERGED_FEATURES_PATH)

logging.info(f" Loading FanDuel slate from {FD_SLATE_PATH}")
df_slate = pd.read_csv(FD_SLATE_PATH)

# Filter to probable pitchers
df_slate["Probable Pitcher"] = df_slate["Probable Pitcher"].fillna("").str.strip().str.lower()
probable_pitchers = df_slate[df_slate["Probable Pitcher"] == "yes"].copy()

# Normalize names
df_merged["name_key"] = df_merged["name"].str.lower().str.strip()
probable_pitchers["name_key"] = probable_pitchers["Nickname"].str.lower().str.strip()

# Merge by normalized name
df_probables = pd.merge(df_merged, probable_pitchers, how="inner", on="name_key")

# Drop duplicates and save
df_probables = df_probables.drop_duplicates(subset="name_key")
df_probables.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved filtered probable pitchers  {OUTPUT_PATH} with {len(df_probables)} rows")
