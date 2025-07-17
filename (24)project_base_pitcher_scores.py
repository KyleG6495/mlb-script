import pandas as pd
import logging
import os

# (24) project_base_pitcher_scores.py

# ── Setup logging ──
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ── File paths ──
FULL_PATH    = "../data/pitcher_boxscores_full.csv"
EARNED_PATH  = "../data/pitcher_boxscores_with_earned.csv"
MAPPING_PATH = "../data/pitcher_games.csv"
OUT_PATH     = "../data/base_pitcher_scores.csv"

# ── 1) Load the full boxscore stats ──
logging.info(f"📥 Loading full boxscores from {FULL_PATH}")
full_df = pd.read_csv(FULL_PATH)
logging.info(f"Columns in full_df: {full_df.columns.tolist()}")

# ── 2) Load the earned‐runs data ──
logging.info(f"📥 Loading earned‐runs from {EARNED_PATH}")
earned_df = pd.read_csv(EARNED_PATH)

# ── 3) Merge on player_id + date ──
logging.info("🔄 Merging full stats with earned runs")
df = pd.merge(
    full_df,
    earned_df[['player_id', 'date', 'earned_run']],
    on=['player_id', 'date'],
    how='left'
)

# ── 4) Merge in game_pk from mapping file (if available) ──
if os.path.exists(MAPPING_PATH):
    logging.info(f"📥 Loading game_pk mapping from {MAPPING_PATH}")
    map_df = pd.read_csv(MAPPING_PATH)
    if 'date' in map_df.columns:
        df = pd.merge(df, map_df[['player_id', 'date', 'game_pk']], on=['player_id', 'date'], how='left')
    else:
        df = pd.merge(df, map_df[['player_id', 'game_pk']], on='player_id', how='left')
    logging.info("→ Merged game_pk from mapping")
else:
    logging.warning(f"Mapping file {MAPPING_PATH} not found; skipping game_pk merge")

# ── 5) Compute innings pitched from outs ──
if 'outs' in df.columns:
    df['inningPitched'] = df['outs'] / 3.0
    logging.info("→ Computed 'inningPitched' from 'outs'")

# ── 6) Rename columns ──
# S → win, L → loss
if "S" in df.columns and "win" not in df.columns:
    df.rename(columns={"S": "win"}, inplace=True)
    logging.info("→ Renamed 'S' to 'win'")
if "L" in df.columns and "loss" not in df.columns:
    df.rename(columns={"L": "loss"}, inplace=True)
    logging.info("→ Renamed 'L' to 'loss'")

# earnedRuns → earned_run (if accidentally still present)
if "earnedRuns" in df.columns and "earned_run" not in df.columns:
    df.rename(columns={"earnedRuns": "earned_run"}, inplace=True)
    logging.info("→ Renamed 'earnedRuns' to 'earned_run'")

# ── 7) Verify required columns ──
required = ["player_id", "game_pk", "win", "loss", "earned_run", "strikeOuts", "inningPitched"]
missing = [c for c in required if c not in df.columns]
if missing:
    logging.error(f"Missing required columns after merge: {missing}")
    raise ValueError(f"Missing required columns: {missing}")

# ── 8) Compute base_score ──
WIN_POINTS   = 5
LOSS_POINTS  = -3
K_POINTS     = 1
ER_POINTS    = -2
IP_POINTS    = 1

df["base_score"] = (
      df["win"]            * WIN_POINTS
    + df["loss"]           * LOSS_POINTS
    + df["strikeOuts"]     * K_POINTS
    + df["earned_run"].fillna(0) * ER_POINTS
    + df["inningPitched"]  * IP_POINTS
)

# ── 9) Save results ──
df.to_csv(OUT_PATH, index=False)
logging.info(f"✅ Saved base pitcher scores → {OUT_PATH}")
