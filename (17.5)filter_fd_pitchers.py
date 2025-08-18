import pandas as pd
import logging
import os

#  Setup logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#  Paths 
PROJ_PATH   = "../data/hitter_projections.csv"         # must contain columns: player_id, proj_points
SLATE_PATH  = "../fd_current_slate/fd_slate_today.csv" # raw FD slate
OUTPUT_PATH = "../data/fd_hitter_features_today.csv"   # enriched slate

#  1) Load projections 
if not os.path.exists(PROJ_PATH):
    raise FileNotFoundError(f"Couldnt find projections at {PROJ_PATH}")
proj = pd.read_csv(PROJ_PATH, dtype=str)
if not {"player_id", "proj_points"}.issubset(proj.columns):
    raise KeyError(f"Projection file must contain 'player_id' and 'proj_points' columns")
proj["player_id"] = proj["player_id"].astype(int)
logging.info(f"SUCCESS: Loaded {len(proj)} proj rows; sample IDs: {proj['player_id'].unique()[:5].tolist()}")

#  2) Load FanDuel slate 
if not os.path.exists(SLATE_PATH):
    raise FileNotFoundError(f"Couldnt find FD slate at {SLATE_PATH}")
slate = pd.read_csv(SLATE_PATH, dtype=str)
logging.info(f"SUCCESS: Loaded FD slate: {len(slate)} rows; columns: {slate.columns.tolist()}")

#  3) Extract MLB player_id from the FD 'Id' column 
if "Id" not in slate.columns:
    raise KeyError("FD slate is missing the 'Id' column")

# Split on '-' and take the second part, then convert to int
# e.g. "118469-198625"  ["118469","198625"]  198625
slate["player_id"] = (
    slate["Id"]
      .astype(str)
      .str.split("-", n=1).str[1]
      .astype(int)
)
logging.info(f" Parsed {slate['player_id'].nunique()} unique player_ids from 'Id'")
logging.info(f"Raw sample Ids: {slate['Id'].head(5).tolist()}")
logging.info(f"Parsed player_ids: {slate['player_id'].head(5).tolist()}")

#  4) Merge projections onto slate 
merged = slate.merge(
    proj,
    on="player_id",
    how="left",
    indicator=True
)
matched = (merged["_merge"] == "both").sum()
logging.info(f" Merged projections: {matched}/{len(merged)} hitters got proj_points")

#  5) Log any missing projections 
missing_ids = merged.loc[merged["_merge"] != "both", "player_id"].unique()
if len(missing_ids):
    logging.warning("WARNING: These player_ids have no proj_points:")
    logging.warning(", ".join(str(i) for i in missing_ids))

#  6) Clean up and save 
merged.drop(columns=["_merge"], inplace=True)
merged.to_csv(OUTPUT_PATH, index=False)
logging.info(f"SUCCESS: Saved enriched FD slate  {OUTPUT_PATH}")
