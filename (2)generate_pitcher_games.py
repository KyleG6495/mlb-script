
# (2) generate_pitcher_games.py — Fixed Version with Proper player_id Parsing

import pandas as pd
import os
from config import FilePaths

# ── Paths from Configuration ──
BASE_DIR    = FilePaths.BASE_DIR
SLATE_FILE  = FilePaths.FD_SLATE_TODAY
DATA_DIR    = FilePaths.DATA_DIR
OUTPUT_FILE = FilePaths.PITCHER_GAMES

os.makedirs(DATA_DIR, exist_ok=True)

# ── 1) Load & filter the FanDuel slate ──
df = pd.read_csv(SLATE_FILE)
pitchers = df[df["Roster Position"].str.upper() == "P"].copy()

# ── 2) Build target_name and extract player_id ──
pitchers["target_name"] = pitchers["First Name"].str.strip() + " " + pitchers["Last Name"].str.strip()
pitchers["player_id"] = pitchers["Id"].astype(str).str.split("-").str[-1].astype(int)

# ── 3) Save only target_name and player_id ──
out_df = pitchers[["target_name", "player_id"]].drop_duplicates()
out_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ pitcher_games.csv saved → {OUTPUT_FILE} ({len(out_df)} rows)")
