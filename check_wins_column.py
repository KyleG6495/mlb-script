#!/usr/bin/env python3
"""Check for wins column in data files"""

import pandas as pd
import os

data_dir = "../data"
files_to_check = [
    "hitter_boxscores_full.csv",
    "pitcher_boxscores_full.csv",
    "hitter_rolling_5game_features.csv", 
    "pitcher_rolling_5game_features.csv"
]

print("Checking for 'wins' column in data files:")
for file in files_to_check:
    path = os.path.join(data_dir, file)
    if os.path.exists(path):
        try:
            df = pd.read_csv(path, nrows=1)
            has_wins = 'wins' in df.columns
            print(f"  {file}: {'YES' if has_wins else 'NO'}")
            if has_wins:
                df_full = pd.read_csv(path)
                print(f"    Sample wins values: {df_full['wins'].head().tolist()}")
        except Exception as e:
            print(f"  {file}: ERROR - {e}")
    else:
        print(f"  {file}: FILE NOT FOUND")
