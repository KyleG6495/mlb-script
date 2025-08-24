import pandas as pd
import requests
import time

# Import centralized configuration
from config import FilePaths, MLB_STATS_API_BASE, LoggingConfig
from player_data_config import ALL_HITTER_MANUAL_IDS, load_player_ids_from_file
import logging

# Setup logging
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LEVEL),
    format=LoggingConfig.FORMAT,
    datefmt=LoggingConfig.DATE_FORMAT
)

INPUT_FILE = FilePaths.HITTER_GAMES
OUTPUT_FILE = FilePaths.HITTER_GAMES

# Load hitter list
logging.info("📄 Loading hitter data from %s", INPUT_FILE)
df = pd.read_csv(INPUT_FILE)
unique_names = df["target_name"].dropna().unique()
logging.info("🔍 Found %d unique hitter names to process", len(unique_names))

# Try to load additional manual IDs from file if it exists
additional_ids_file = FilePaths.DATA_DIR / "manual_hitter_ids.json"
additional_manual_ids = load_player_ids_from_file(additional_ids_file)

# Combine built-in and external manual IDs
manual_ids = {**ALL_HITTER_MANUAL_IDS, **additional_manual_ids}
logging.info("📋 Loaded %d manual ID mappings", len(manual_ids))

# Fetch all active MLB players once
url = f"{MLB_STATS_API_BASE}/sports/1/players"
logging.info("🔄 Fetching active MLB player list from API...")
res = requests.get(url)
players = res.json().get("people", [])
logging.info("✅ Retrieved %d active MLB players", len(players))

# Create mapping of full name to ID
name_to_id = {
    p["fullName"].lower(): p["id"]
    for p in players if "fullName" in p
}

# Automatically assign IDs
id_map = {}
for name in unique_names:
    pid = name_to_id.get(name.lower())
    id_map[name] = pid
    status = "✅ " + str(pid) if pid else "❌ Not found"
    logging.info("%s → %s", name, status)
    time.sleep(0.05)

# Apply manual overrides
logging.info("🔧 Applying %d manual ID overrides", len(manual_ids))
id_map.update(manual_ids)

# Update original file
df["player_id"] = df["target_name"].map(id_map)
df.to_csv(OUTPUT_FILE, index=False)
logging.info("✅ Updated %s with player_id column (including manual overrides)", OUTPUT_FILE)
