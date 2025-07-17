# (27) project_pitcher_scores.py

import pandas as pd
import logging
import os

# ── Setup logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ── Paths ──
BASE_PROJ_PATH      = "../data/base_pitcher_scores.csv"
SLATE_PROBABLE_PATH = "../data/pitcher_features_probables.csv"
OUTPUT_PATH         = "../data/fd_pitcher_scores.csv"

# ── 1) Load base per-game pitcher scores ──
logging.info(f"📥 Loading base pitcher scores from {BASE_PROJ_PATH}")
if not os.path.exists(BASE_PROJ_PATH):
    raise FileNotFoundError(f"Run step (24) first to generate {BASE_PROJ_PATH}")

base_df = pd.read_csv(BASE_PROJ_PATH)
logging.info(f"Columns in base_df: {base_df.columns.tolist()}")

# ── 1a) Ensure we have the key columns ──
if not {"player_id", "date", "base_score"}.issubset(base_df.columns):
    raise KeyError(f"Expected ['player_id','date','base_score'] in {BASE_PROJ_PATH}")

# ── 1b) Deduplicate on (player_id, date) ──
dupe_mask = base_df.duplicated(subset=["player_id", "date"], keep=False)
if dupe_mask.any():
    dupes = base_df[dupe_mask][["player_id", "date", "base_score"]]
    logging.warning(f"Found {len(dupes)} duplicate rows for same (player_id, date); dropping extras")
    base_df = base_df.drop_duplicates(subset=["player_id", "date"], keep="first")

# ── 2) Load probable-pitchers slate ──
logging.info(f"📥 Loading probable pitchers slate from {SLATE_PROBABLE_PATH}")
if not os.path.exists(SLATE_PROBABLE_PATH):
    raise FileNotFoundError(f"Need {SLATE_PROBABLE_PATH} (from filter_probable_pitchers.py)")
slate = pd.read_csv(SLATE_PROBABLE_PATH)
logging.info(f"Columns in slate: {slate.columns.tolist()}")

# ── 2a) Ensure slate has 'player_id' and 'date' ──
if "player_id" not in slate.columns:
    if "Id" in slate.columns:
        slate.rename(columns={"Id": "player_id"}, inplace=True)
        logging.info("→ Renamed slate 'Id' to 'player_id'")
    else:
        raise KeyError("'player_id' missing from probable-pitchers slate")

if "date" not in slate.columns:
    raise KeyError("'date' missing from probable-pitchers slate")

# ── 3) Merge in base_score on both player_id & date ──
logging.info("🔄 Merging base_score onto slate by [player_id, date]…")
merged = slate.merge(
    base_df[["player_id", "date", "base_score"]],
    on=["player_id", "date"],
    how="left",
    validate="many_to_one"
)

# ── 4) Save the result ──
merged.to_csv(OUTPUT_PATH, index=False)
logging.info(f"✅ Saved pitcher scores → {OUTPUT_PATH}")
