#!/usr/bin/env python3
"""
UPDATE DATA PIPELINE FOR CONFIRMED STARTERS
==========================================
Updates all data pipeline scripts to use starting_lineups.csv instead of fd_slate_today.csv
This ensures we only pull historical data, weather, park factors for confirmed starters.
"""

import os
import re
from pathlib import Path

def update_script_for_starters(script_path, backup=True):
    """Update a script to use confirmed starters instead of full slate"""
    
    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        return False
    
    # Create backup if requested
    if backup:
        backup_path = f"{script_path}.backup"
        if not os.path.exists(backup_path):
            with open(script_path, 'r', encoding='utf-8') as f:
                with open(backup_path, 'w', encoding='utf-8') as backup_f:
                    backup_f.write(f.read())
            print(f"INFO: Created backup: {backup_path}")
    
    with open(script_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Update path references to use starters-only file
    content = re.sub(
        r'fd_current_slate[\\/]fd_slate_today\.csv',
        r'data/fd_slate_starters_only.csv',
        content
    )
    
    # Update data directory references 
    content = re.sub(
        r'data[\\/]fd_slate_today\.csv',
        r'data/fd_slate_starters_only.csv',
        content
    )
    
    # Update raw string paths
    content = re.sub(
        r'r"[^"]*fd_current_slate[\\/]fd_slate_today\.csv"',
        r'r"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\fd_slate_starters_only.csv"',
        content
    )
    
    # Update comments to reflect change
    content = re.sub(
        r'# Load & filter the FanDuel slate',
        r'# Load confirmed starters only (pre-filtered)',
        content
    )
    
    content = re.sub(
        r'Load & filter the FanDuel slate',
        r'Load confirmed starters only (pre-filtered)',
        content
    )
    
    # Add comment about confirmed starters
    if 'SLATE_FILE' in content and 'confirmed starters' not in content:
        content = re.sub(
            r'(SLATE_FILE\s*=.*)',
            r'# Using confirmed starters only - no bench players\n\\1',
            content
        )
    
    if content != original_content:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SUCCESS: Updated: {os.path.basename(script_path)}")
        return True
    else:
        print(f" No changes needed: {os.path.basename(script_path)}")
        return False

def main():
    """Update all data pipeline scripts"""
    
    print("SWAP: UPDATING DATA PIPELINE TO USE CONFIRMED STARTERS")
    print("=" * 60)
    print()
    
    # Check if master file exists
    master_file = "../data/starting_lineups.csv"
    starters_file = "../data/fd_slate_starters_only.csv"
    
    if not os.path.exists(master_file):
        print("ERROR: starting_lineups.csv not found!")
        print("ERROR: Please run create_starting_lineups.py first")
        return
    
    if not os.path.exists(starters_file):
        print("ERROR: fd_slate_starters_only.csv not found!")
        print("ERROR: Please run prepare_starters_for_existing_scripts.py first")
        return
    
    print(f"SUCCESS: Master file found: {master_file}")
    print(f"SUCCESS: Starters file found: {starters_file}")
    print()
    
    # Scripts that need to be updated (data pipeline scripts)
    scripts_to_update = [
        "1. generate_hitter_games.py",
        "4. generate_pitcher_games.py",
        "filter_todays_pitchers.py",
        "filter_todays_pitchers_simple.py",
        "19. build_weather_today.py",
        "SLATE_BASED_FILTER.py",
        "fix_slate_scheduling.py",
        "MY_DAILY_PROPS.py",
        "automated_betting_system.py",
        "proper_backtest_analysis.py"
    ]
    
    updated_count = 0
    
    for script in scripts_to_update:
        script_path = f"./{script}"
        if update_script_for_starters(script_path):
            updated_count += 1
    
    print()
    print("=" * 60)
    print(f"COMPLETE: PIPELINE UPDATE COMPLETE!")
    print(f"DATA: Updated {updated_count} scripts to use confirmed starters")
    print()
    print("Benefits:")
    print("SUCCESS: Only confirmed starters get historical data pulled")
    print("SUCCESS: Only confirmed starters get weather/park factors")
    print("SUCCESS: Faster pipeline execution (less data to process)")
    print("SUCCESS: No more bench players in analysis")
    print()
    print("Next: Run 1_DATA_PIPELINE.bat to test the updated pipeline")

if __name__ == "__main__":
    main()
