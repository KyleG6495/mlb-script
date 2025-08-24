#!/usr/bin/env python3
"""
FANDUEL LINEUP NAME TRANSLATOR
=============================
Converts FanDuel player IDs to actual player names for easy reading
"""

import pandas as pd
import logging
from datetime import datetime
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def translate_lineup_names():
    """Convert FanDuel lineup files from IDs to player names"""
    
    logger.info("INFO: CREATING READABLE LINEUP NAMES")
    logger.info("=" * 60)
    
    # Get current date for file matching
    current_date = datetime.now().strftime("%Y%m%d")
    
    # Find today's FanDuel slate file
    slate_pattern = f"../fd_current_slate/fd_slate_today.csv"
    try:
        df_slate = pd.read_csv(slate_pattern)
        logger.info(f"SUCCESS: Loaded slate: {slate_pattern}")
    except FileNotFoundError:
        # Try alternate pattern
        slate_files = glob.glob("../fd_current_slate/fd_slate*.csv")
        if slate_files:
            df_slate = pd.read_csv(slate_files[0])
            logger.info(f"SUCCESS: Loaded slate: {slate_files[0]}")
        else:
            logger.error("ERROR: No FanDuel slate file found!")
            return
    
    # Create player mapping
    player_mapping = {}
    for _, player in df_slate.iterrows():
        player_id = str(player['Id'])
        player_name = player['Nickname']
        player_salary = int(player['Salary'])
        player_mapping[player_id] = {
            'name': player_name,
            'salary': player_salary
        }
    
    logger.info(f"SUCCESS: Created name mapping for {len(player_mapping)} players")
    
    # Find today's lineup files to convert
    lineup_files = [
        f"../data/FANDUEL_EXPANDED_FILTERED_SUBMISSION_{current_date}*.csv",
        f"../data/FANDUEL_LINEUPS_WITH_NAMES_{current_date}*.csv"
    ]
    
    files_converted = 0
    
    for pattern in lineup_files:
        matching_files = glob.glob(pattern)
        for file_path in matching_files:
            try:
                logger.info(f"SWAP: Converting: {file_path}")
                
                # Read the lineup file
                df_lineups = pd.read_csv(file_path)
                
                # Convert each lineup
                converted_lineups = []
                
                for i, row in df_lineups.iterrows():
                    converted_lineup = {}
                    total_salary = 0
                    
                    # Strategy name (if exists)
                    if 'Strategy' in row:
                        converted_lineup['Strategy'] = row['Strategy']
                    else:
                        converted_lineup['Strategy'] = f"Lineup {i+1}"
                    
                    # Convert each position
                    position_columns = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
                    
                    for pos in position_columns:
                        if pos in row and pd.notna(row[pos]):
                            player_id_full = str(row[pos])
                            
                            # Extract just the player ID (remove the format like "119424-82618")
                            if '-' in player_id_full:
                                player_id = player_id_full.split('-')[1]
                            else:
                                player_id = player_id_full
                            
                            # Look up player name and salary
                            if player_id in player_mapping:
                                player_info = player_mapping[player_id]
                                player_name = player_info['name']
                                player_salary = player_info['salary']
                                converted_lineup[pos] = f"{player_name} (${player_salary})"
                                total_salary += player_salary
                            else:
                                converted_lineup[pos] = f"Unknown ({player_id_full})"
                                logger.warning(f"ERROR: Player ID not found: {player_id}")
                    
                    converted_lineup['Total_Salary'] = f"${total_salary:,}"
                    converted_lineup['Remaining'] = f"${35000 - total_salary:,}"
                    converted_lineups.append(converted_lineup)
                
                # Save converted file
                base_name = file_path.split('\\')[-1].replace('.csv', '')
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"../data/{base_name}_READABLE_{timestamp}.csv"
                
                df_converted = pd.DataFrame(converted_lineups)
                df_converted.to_csv(output_file, index=False)
                logger.info(f"SUCCESS: Saved readable lineups: {output_file}")
                
                # Also create a detailed summary
                summary_file = f"../data/{base_name}_SUMMARY_{timestamp}.txt"
                with open(summary_file, 'w') as f:
                    f.write("LINEUP: FANDUEL LINEUP SUMMARY\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, lineup in enumerate(converted_lineups):
                        f.write(f"LINEUP {i+1}: {lineup['Strategy']}\n")
                        f.write(f"Total Salary: {lineup['Total_Salary']}\n")
                        f.write(f"Remaining: {lineup['Remaining']}\n")
                        f.write("-" * 30 + "\n")
                        
                        for pos in position_columns:
                            if pos in lineup:
                                f.write(f"{pos:>5}: {lineup[pos]}\n")
                        f.write("\n")
                
                logger.info(f"SUCCESS: Saved summary: {summary_file}")
                files_converted += 1
                
            except Exception as e:
                logger.error(f"ERROR: Error converting {file_path}: {e}")
    
    if files_converted > 0:
        logger.info(f"\nCOMPLETE: SUCCESS! Converted {files_converted} lineup files")
        logger.info("INFO: Check the _READABLE_ and _SUMMARY_ files for easy-to-read lineups!")
    else:
        logger.warning("WARNING: No lineup files found to convert")

if __name__ == "__main__":
    translate_lineup_names()
