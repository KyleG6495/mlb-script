import pandas as pd
import logging
import os

#  Setup logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#  Paths 
PROJ_PATH   = "../data/hitter_projections.csv"        # must contain columns: player_id, proj_points
SLATE_PATH  = "../fd_current_slate/fd_slate_today.csv" # raw FD slate
OUTPUT_PATH = "../data/fd_hitter_features_today.csv"   # enriched slate

# 1) Load projections
if not os.path.exists(PROJ_PATH):
    raise FileNotFoundError(f"Couldnt find projections at {PROJ_PATH}")
proj = pd.read_csv(PROJ_PATH, dtype=str)
if not {"player_id","proj_points"}.issubset(proj.columns):
    raise KeyError("Projections file must include 'player_id' and 'proj_points'")
proj = proj[["player_id","proj_points"]].drop_duplicates()
proj["proj_points"] = pd.to_numeric(proj["proj_points"], errors="coerce")
proj["player_id"]   = proj["player_id"].astype(str)
logging.info(f"SUCCESS: Loaded projections: {len(proj)} unique player_ids")

# 2) Load the raw FanDuel slate
if not os.path.exists(SLATE_PATH):
    raise FileNotFoundError(f"Couldnt find slate at {SLATE_PATH}")
slate = pd.read_csv(SLATE_PATH, dtype=str)
logging.info(f"SUCCESS: Loaded raw FD slate: {len(slate)} rows; columns: {list(slate.columns)}")

# 3) Extract MLB player_id from FD 'Id' column
if "Id" not in slate.columns:
    raise KeyError("Slate missing 'Id' column")

# split on '-' and take the second part ("H-660271"  ["H","660271"]  "660271")
slate["player_id"] = (
    slate["Id"]
         .astype(str)
         .str.split("-", n=1).str[1]
         .astype(str)
)

logging.info(f" Parsed {slate['player_id'].nunique()} unique player_ids in slate")
logging.info(f"Raw sample Ids: {slate['Id'].head(5).tolist()}")
logging.info(f"Parsed player_ids: {slate['player_id'].head(5).tolist()}")

# 4) Merge projections onto the slate by player_id
merged = pd.merge(
    slate,
    proj,
    on="player_id",
    how="left",
    validate="many_to_one",
    indicator=True
)
matched = (merged["_merge"] == "both").sum()
logging.info(f" Merged projections: {matched}/{len(merged)} hitters got proj_points")

# Log any missing projections
missing_ids = merged.loc[merged["_merge"] != "both", "player_id"].unique()
if len(missing_ids):
    logging.warning("WARNING: These player_ids have no proj_points:")
    logging.warning(", ".join(missing_ids.astype(str)))

# 5) Clean up and save
merged.drop(columns=["_merge"], inplace=True)

# 6) Write enriched slate
merged.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved enriched FD slate  {OUTPUT_PATH}")
