import pandas as pd
import logging
from datetime import date

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# File paths
INPUT_PATH = "../data/fd_hitter_features_enriched.csv"
OUTPUT_PATH = "../data/fd_hitter_features_final.csv"

logging.info(f" Loading enriched hitter features from {INPUT_PATH}")
# Read enriched hitter features
df = pd.read_csv(INPUT_PATH)
logging.info(f"SUCCESS: Loaded {len(df)} rows with {len(df.columns)} columns")

# Compute current season year dynamically
current_year = date.today().year

# Ensure Season column is present and default missing to current_year
df['Season'] = df.get('Season', pd.Series(dtype=int)).fillna(current_year).astype(int)

# Identify weather- and park-related columns to drop
weather_keywords = ["temperature", "wind_speed", "condition", "park_name"]
weather_cols = [col for col in df.columns if any(kw in col.lower() for kw in weather_keywords)]
park_cols = [col for col in ["park_factor", "park_1B", "park_2B", "park_3B", "park_HR", "park_SO", "park_BB", "park_GB", "park_FB", "park_LD", "park_IFFB", "park_FIP"] if col in df.columns]

to_drop = weather_cols + park_cols
logging.info(f" Dropping columns: {to_drop}")

# Drop and produce final DataFrame
df_final = df.drop(columns=to_drop)
logging.info(f"SUCCESS: df_final shape: {df_final.shape}")

# Save the cleaned DataFrame
df_final.to_csv(OUTPUT_PATH, index=False)
logging.info(f" Saved final hitter features  {OUTPUT_PATH}")
