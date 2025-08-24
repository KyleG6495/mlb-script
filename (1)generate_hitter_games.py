
# (1) generate_hitter_games.py — Fixed Version with Proper player_id Parsing

import pandas as pd
import os
from config import FilePaths

# ── Paths from Configuration ──
BASE_DIR    = FilePaths.BASE_DIR
SLATE_FILE  = FilePaths.FD_SLATE_TODAY
DATA_DIR    = FilePaths.DATA_DIR
OUTPUT_FILE = FilePaths.HITTER_GAMES

os.makedirs(DATA_DIR, exist_ok=True)

# ── 1) Load & filter the FanDuel slate ──
df = pd.read_csv(SLATE_FILE)
hitters = df[df["Roster Position"].str.upper() != "P"].copy()

# ── 2) Generate target_name and extract player_id from Id column ──
hitters["target_name"] = hitters["First Name"].str.strip() + " " + hitters["Last Name"].str.strip()
hitters["player_id"] = hitters["Id"].astype(str).str.split("-").str[-1].astype(int)

# ── 3) Save only target_name and player_id ──
out_df = hitters[["target_name", "player_id"]].drop_duplicates()
out_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ hitter_games.csv saved → {OUTPUT_FILE} ({len(out_df)} rows)")
