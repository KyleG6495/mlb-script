
# (1) generate_hitter_games.py  Fixed Version with Proper player_id Parsing

import pandas as pd
import os

#  Paths 
BASE_DIR    = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SLATE_FILE  = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "hitter_games.csv")

os.makedirs(DATA_DIR, exist_ok=True)

#  1) Load FD slate with batting orders 
df = pd.read_csv(SLATE_FILE)
hitters = df[df["Position"] != "P"].copy()

#  2) Generate target_name and extract player_id from Id column 
# Use Nickname (which is actually the display name) instead of duplicated names
hitters["target_name"] = hitters["Nickname"].str.strip()

# Extract player_id from Id column (format: player_id-position or just player_id)
if "Id" in hitters.columns:
    hitters["player_id"] = hitters["Id"].astype(str).str.split("-").str[-1].astype(int)
else:
    # If no Id column, set to None - will be filled by assign_hitter_ids.py
    hitters["player_id"] = None

#  3) Include batting order information if available
columns_to_save = ["target_name", "player_id"]
if "Order" in hitters.columns:
    columns_to_save.append("Order")
    print("✅ Including batting order information from Rotowire lineups")

#  4) Save with batting orders if available
out_df = hitters[columns_to_save].drop_duplicates()
out_df.to_csv(OUTPUT_FILE, index=False)

print(f"SUCCESS: hitter_games.csv saved to {OUTPUT_FILE} ({len(out_df)} rows)")
if "Order" in out_df.columns:
    players_with_orders = out_df[out_df["Order"].notna()]
    print(f"✅ {len(players_with_orders)} players have batting order information")
else:
    print("⚠️ No batting order information available - check Rotowire lineup extraction")
