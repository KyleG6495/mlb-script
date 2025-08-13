
# (2) generate_pitcher_games.py — Fixed Version with Proper player_id Parsing

import pandas as pd
import os

# ── Paths ──
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SLATE_FILE  = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_starters_only.csv"
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "pitcher_games.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# ── 1) Load confirmed starters only (pre-filtered) ──
df = pd.read_csv(SLATE_FILE)
pitchers = df[df["Roster Position"].str.upper() == "P"].copy()

# ── 2) Build target_name and extract player_id ──
pitchers["target_name"] = pitchers["First Name"].str.strip() + " " + pitchers["Last Name"].str.strip()
pitchers["player_id"] = pitchers["Id"].astype(str).str.split("-").str[-1].astype(int)

# ── 3) Save only target_name and player_id ──
out_df = pitchers[["target_name", "player_id"]].drop_duplicates()
out_df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ pitcher_games.csv saved → {OUTPUT_FILE} ({len(out_df)} rows)")
