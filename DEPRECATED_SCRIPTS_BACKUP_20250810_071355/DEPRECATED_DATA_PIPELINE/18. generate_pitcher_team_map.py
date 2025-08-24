#!/usr/bin/env python3
import logging
import pandas as pd
import sys
from pathlib import Path
import unicodedata

# ┌──────────────────────────────────────────────────────────────────────────┐
# │            CONFIGURE YOUR FILE PATHS HERE                               │
# └──────────────────────────────────────────────────────────────────────────┘
DATA_DIR = Path(__file__).parent.parent / "data"
SLATE_DIR = Path(__file__).parent.parent / "fd_current_slate"

STATS_FILE = DATA_DIR / "pitcher_features_merged.csv"
SLATE_FILE = SLATE_DIR / "fd_slate_today.csv"
MAP_FILE = DATA_DIR / "pitcher_games_with_game_pk.csv"
OUT_FILE = DATA_DIR / "pitcher_team_map.csv"

# ┌──────────────────────────────────────────────────────────────────────────┐
# │            LOGGING SETUP                                               │
# └──────────────────────────────────────────────────────────────────────────┘
logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s", datefmt="%Y%m%d %H:%M:%S", level=logging.INFO
)

def normalize_name(s) -> str:
    if pd.notna(s) and str(s).strip():
        # Normalize accents and decompose Unicode characters
        s = unicodedata.normalize('NFKD', str(s)).encode('ASCII', 'ignore').decode('ASCII')
        # Remove punctuation, suffixes, and extra spaces
        return (
            s.strip()
            .lower()
            .replace(".", "")
            .replace(",", "")
            .replace(" jr", "")
            .replace(" sr", "")
            .replace("'", "")
            .replace("-", " ")
            .replace("  ", " ")
            .replace(" iii", "")
            .replace(" ii", "")
        )
    return ""

def main():
    # 1) Load stats
    logging.info(f"📥 Loading stats from {STATS_FILE}")
    df_stats = pd.read_csv(STATS_FILE, parse_dates=False)
    logging.info(f"✅ Loaded {len(df_stats)} pitcher‐feature rows")

    # Ensure there's no leftover game_pk from a previous run
    if "game_pk" in df_stats.columns:
        logging.info("✂️  Dropping old game_pk column")
        df_stats = df_stats.drop(columns=["game_pk"])

    # Make sure IDs are strings
    df_stats["player_id"] = df_stats["player_id"].astype(str).str.strip()

    # Check name column
    logging.info(f"ℹ️ Name column dtype: {df_stats['name'].dtype}")
    logging.info(f"Sample names in df_stats: {df_stats['name'].head().tolist()}")
    logging.info(f"ℹ️ {df_stats['name'].isna().sum()} rows with NaN names")

    # 2) Load FD slate and parse the 'Id' field
    logging.info(f"📥 Loading FD slate from {SLATE_FILE}")
    df_slate = pd.read_csv(SLATE_FILE)
    df_slate[["site_prefix", "player_id"]] = (
        df_slate["Id"]
        .astype(str)
        .str.split("-", n=1, expand=True)
    )
    df_slate["player_id"] = df_slate["player_id"].str.strip()
    logging.info(f"✅ Parsed {len(df_slate)} slate rows; sample IDs: {df_slate['player_id'].tolist()[:5]}")
    logging.info(f"ℹ️ {len(df_stats)} stats rows, {len(df_slate)} slate rows")
    logging.info(f"Sample Nicknames in df_slate: {df_slate['Nickname'].head().tolist()}")

    # Filter df_slate for pitchers if Position column exists
    if "Position" in df_slate.columns:
        logging.info(f"Unique positions in df_slate: {df_slate['Position'].unique()}")
        df_slate = df_slate[df_slate["Position"].str.contains("P", na=False)]
        logging.info(f"ℹ️ Filtered df_slate to {len(df_slate)} pitcher rows")
        logging.info(f"Sample pitcher Nicknames in df_slate: {df_slate['Nickname'].head().tolist()}")

    # Merge Nickname from df_slate to replace invalid names
    logging.info("🔄 Merging Nickname from df_slate to df_stats")
    df_stats = df_stats.merge(
        df_slate[["player_id", "Nickname", "Position"]],
        how="left",
        on="player_id",
        validate="many_to_one",  # Changed from "one_to_one"
        suffixes=("", "_slate")
    )
    # Use Nickname where name is NaN or non-string
    df_stats["name"] = df_stats.apply(
        lambda row: row["Nickname"] if pd.isna(row["name"]) or not isinstance(row["name"], str) else row["name"],
        axis=1
    )
    df_stats = df_stats.drop(columns=["Nickname"], errors="ignore")
    logging.info(f"Sample names after merge: {df_stats['name'].head().tolist()}")

    # Filter df_stats for pitchers based on Position
    if "Position" in df_stats.columns:
        logging.info(f"Unique positions in df_stats: {df_stats['Position'].unique()}")
        df_stats = df_stats[df_stats["Position"].str.contains("P", na=False)]
        logging.info(f"ℹ️ Filtered df_stats to {len(df_stats)} pitcher rows")
        logging.info(f"Sample pitcher names in df_stats: {df_stats['name'].head().tolist()}")

    # Create name_key
    df_stats["name_key"] = df_stats["name"].apply(normalize_name)
    logging.info(f"ℹ️ {df_stats['name_key'].nunique()} unique name_keys in df_stats")
    logging.info(f"Sample name_keys in df_stats: {df_stats['name_key'].head().tolist()}")

    # Log missing or empty names
    missing_names = df_stats["name"].isna() | (df_stats["name"].str.strip() == "")
    logging.info(f"⚠️ {missing_names.sum()} rows in df_stats have missing/empty names after merge")

    # Check for duplicate name_keys
    duplicate_names = df_stats[df_stats["name_key"].duplicated(keep=False)]["name_key"].unique()
    if len(duplicate_names) > 0:
        logging.info(f"⚠️ Found {len(duplicate_names)} duplicate name_keys in df_stats: {duplicate_names[:5]}")

    # 3) Load mapping of pitcher → game_pk
    logging.info(f"📥 Loading map from {MAP_FILE}")
    map_df = pd.read_csv(MAP_FILE, dtype={"player_id": str})
    map_df["player_id"] = map_df["player_id"].str.strip()
    logging.info(f"✅ Loaded {len(map_df)} map‐rows; columns: {map_df.columns.tolist()}")

    # Deduplicate map: keep first game_pk per player_id
    map_df = map_df.drop_duplicates(subset=["player_id"], keep="first")
    logging.info(f"✂️  Deduplicated map to {len(map_df)} unique player_id mappings")

    # Create name_key for map_df
    map_df["name_key"] = map_df["target_name"].apply(normalize_name)

    # Log sample data for debugging
    logging.info(f"Sample player_ids in df_stats: {df_stats['player_id'].head().tolist()}")
    logging.info(f"Sample player_ids in map_df: {map_df['player_id'].head().tolist()}")
    logging.info(f"Sample name_keys in map_df: {map_df['name_key'].head().tolist()}")

    # Check for common name_keys
    common_name_keys = set(df_stats["name_key"]) & set(map_df["name_key"])
    logging.info(f"ℹ️ {len(common_name_keys)} common name_keys between df_stats and map_df")
    if len(common_name_keys) > 0:
        logging.info(f"Sample common name_keys: {list(common_name_keys)[:5]}")

    # 4) Merge onto stats by player_id
    logging.info("🔄 Merging stats ← map on player_id")
    df_out = df_stats.merge(
        map_df[["player_id", "game_pk"]],
        how="left",
        on="player_id",
        validate="many_to_one",  # Changed from "one_to_one"
        suffixes=("", "_map"),
    )

    got = int(df_out["game_pk"].notna().sum())
    total = len(df_out)
    logging.info(f"📊 After merge: {got}/{total} rows have game_pk, {total - got} missing")

    # 5) Fallback merge on name if needed
    if got < total:
        logging.info("🔄 Attempting fallback merge on normalized name")
        # Ensure game_pk from previous merge is preserved
        df_out = df_out.rename(columns={"game_pk": "game_pk_id"}, errors="ignore")
        df_out = df_out.merge(
            map_df[["name_key", "game_pk"]],
            how="left",
            on="name_key",
            validate="many_to_one",
            suffixes=("", "_name")
        )
        # Combine game_pk from both merges
        df_out["game_pk"] = df_out["game_pk_id"].fillna(df_out["game_pk"])
        df_out = df_out.drop(columns=["game_pk_id", "game_pk_name"], errors="ignore")
        
        # Debug matched rows
        matched = df_out[df_out["game_pk"].notna()]
        logging.info(f"ℹ️ {len(matched)} rows matched on name_key")
        if len(matched) > 0:
            logging.info(f"Sample matched rows: {matched[['name_key', 'game_pk']].head().to_dict('records')}")
        
        # Debug unmatched rows
        unmatched = df_out[df_out["game_pk"].isna()]
        logging.info(f"℮️ {len(unmatched)} unmatched rows")
        if len(unmatched) > 0:
            logging.info(f"Sample unmatched name_keys (up to 20): {unmatched['name_key'].head(20).tolist()}")
            logging.info(f"Sample unmatched raw names: {unmatched['name'].head(20).tolist()}")

        got2 = int(df_out["game_pk"].notna().sum())
        logging.info(f"📊 After name merge: {got2}/{len(df_out)} rows have game_pk, {len(df_out) - got2} missing")

    # 6) Save
    logging.info(f"✅ Saving → {OUT_FILE} with {len(df_out)} rows")
    df_out.to_csv(OUT_FILE, index=False)
    logging.info(f"🎉 Done.")

if __name__ == "__main__":
    main()