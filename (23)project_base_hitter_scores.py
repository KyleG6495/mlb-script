import pandas as pd
import logging
import os
from datetime import date
import glob

#  Setup logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#  Paths 
SLATE_PATH = "../fd_current_slate/fd_slate_today.csv"
DATA_DIR   = "../data"
OUTPUT     = "../data/projected_fd_hitter_scores.csv"

# 1) Load FanDuel slate
if not os.path.exists(SLATE_PATH):
    raise FileNotFoundError(f"Couldnt find FD slate at {SLATE_PATH}")
slate = pd.read_csv(SLATE_PATH, dtype=str)
logging.info(f"SUCCESS: Loaded FD slate: {len(slate)} rows; columns: {slate.columns.tolist()}")

# 2) Parse every Id  player_id
slate['player_id'] = (
    slate['Id']
      .astype(str)
      .str.extract(r'-(\d+)$', expand=False)
)
if slate['player_id'].isna().any():
    logging.warning("Some Ids failed to parse; falling back to first run of digits")
    slate['player_id'] = slate['Id'].str.extract(r'(\d+)', expand=False)
slate['player_id'] = slate['player_id'].astype(int)
logging.info(f" Parsed {slate['player_id'].nunique()} unique player_ids")

# 3) Stamp on todays date
today = date.today()
slate['date'] = pd.to_datetime(today)
logging.info(f" Added 'date' = {today}")

# 4) Locate your historical hitter scores file
# Prefer the one named base_hitter_scores.csv
bh_path = os.path.join(DATA_DIR, "base_hitter_scores.csv")
if os.path.exists(bh_path):
    BASE_CSV = bh_path
else:
    # fallback: pick any file in data/ with "hitter_scores" in the name
    candidates = glob.glob(os.path.join(DATA_DIR, "*hitter_scores.csv"))
    candidates = [c for c in candidates if "base" in os.path.basename(c)]
    if candidates:
        BASE_CSV = candidates[0]
    else:
        logging.error("No base_hitter_scores.csv found in data/. You need your pergame hitter scores file.")
        logging.error("Available CSVs: " + str(glob.glob(os.path.join(DATA_DIR,"*.csv"))))
        raise FileNotFoundError("Couldnt locate your base_hitter_scores.csv")

logging.info(f" Using hitterscores history file: {os.path.basename(BASE_CSV)}")

# 5) Load and prepare that table
base = pd.read_csv(BASE_CSV, parse_dates=['date'])
if 'player_id' not in base.columns or 'base_score' not in base.columns:
    raise KeyError(f"{BASE_CSV} must contain 'player_id' and 'base_score'")
base['player_id'] = base['player_id'].astype(int)
logging.info(f"DATA: Loaded {len(base)} historical base_score rows")

# Dedupe to one row per (player_id, date)
base_agg = base[['player_id','date','base_score']].drop_duplicates()
logging.info(f" Aggregated to {len(base_agg)} unique (player_id, date) rows")

# 6) Merge slate + base_score
merged = slate.merge(
    base_agg,
    on=['player_id','date'],
    how='left',
    indicator=True
)
matched = (merged['_merge']=='both').sum()
logging.info(f" Merged in base_score: {matched}/{len(merged)} matched")

missing = merged.loc[merged['_merge']!='both','player_id'].unique()
if len(missing):
    logging.warning("WARNING: These player_ids had no base_score for today:")
    logging.warning(", ".join(str(i) for i in missing))

# 7) Save results
merged.drop(columns=['_merge'], inplace=True)
merged.to_csv(OUTPUT, index=False)
logging.info(f"SUCCESS: Saved projected FD hitter scores  {OUTPUT}")
