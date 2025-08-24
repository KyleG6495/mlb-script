# MLB DFS SYSTEM - CRITICAL PATH CONFIGURATION
# =============================================
# This file documents the CORRECT file paths that must be used
# DO NOT CHANGE THESE PATHS WITHOUT UPDATING ALL SCRIPTS

# CRITICAL: FanDuel Slate Directory
# The fd_current_slate directory contains the ACTIVE slate for the current contest
FD_CURRENT_SLATE_DIR = "C:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate"

# CRITICAL: Active Slate File
# This file is updated for each new slate/contest
ACTIVE_SLATE_FILE = "fd_slate_today.csv"

# CRITICAL: Starting Pitcher Identification
# Starting pitchers are identified by column O "Probable Pitcher" = "Yes"
STARTING_PITCHER_COLUMN = "Probable Pitcher"
STARTING_PITCHER_VALUE = "Yes"

# DANGER ZONE: These old paths should NOT be used
# These files in the data directory are often STALE and should be DELETED
DEPRECATED_PATHS = [
    "../data/fd_slate_today.csv",           # OLD - often stale
    "../data/fd_slate_starters_only.csv",   # OLD - DELETED - was causing stale data issues
    "../data/fd_hitter_features_final.csv", # OLD - often stale
    "../data/fd_pitcher_features_final.csv" # OLD - often stale
]

# IMPROVEMENT: fd_slate_starters_only.csv has been DELETED to prevent stale data usage

# CORRECT USAGE PATTERN:
# Always use: FD_SLATE_DIR / "fd_slate_today.csv"
# Never use: BASE_DIR / "fd_slate_starters_only.csv"

# TEAMS IN CURRENT SLATE (August 17, 2025):
# ATH, LAA, LAD, SD, SF, TB (6 teams total)
