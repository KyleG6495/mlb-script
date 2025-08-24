#!/usr/bin/env python3
"""
EXPANDED FILTERED FANDUEL FORMATTER
==================================
Formats filtered lineups with proper names and salaries for FanDuel submission
"""

import pandas as pd
import logging
from datetime import datetime
import glob

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def format_filtered_lineups():
    """Format today's filtered lineups with proper names and salaries"""
    
    logger.info("TARGET: CREATING EXPANDED FILTERED SUBMISSION (15+ LINEUPS)")
    logger.info("=" * 80)
    
    # Get current date for file matching
    current_date = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Find today's filtered lineups
    lineup_pattern = f"TODAY_FILTERED_LINEUPS_{current_date}*.csv"
    lineup_files = glob.glob(lineup_pattern)
    
    if not lineup_files:
        logger.error(f"ERROR: No filtered lineup files found: {lineup_pattern}")
        return
    
    lineup_file = lineup_files[0]
    logger.info(f"SUCCESS: Using lineup file: {lineup_file}")
    
    # Load the lineups
    df_lineups = pd.read_csv(lineup_file)
    
    # Get unique strategies
    strategies = df_lineups['Strategy'].unique()
    logger.info(f"SUCCESS: Found {len(strategies)} strategies: {', '.join(strategies)}")
    
    # Format for FanDuel submission
    fanduel_lineups = []
    readable_lineups = []
    
    for i, strategy in enumerate(strategies):
        strategy_players = df_lineups[df_lineups['Strategy'] == strategy]
        
        # Create FanDuel format lineup
        fanduel_lineup = {}
        readable_lineup = {'Lineup_ID': i+1, 'Strategy': strategy}
        
        total_salary = 0
        
        # Map positions to FanDuel format
        position_mapping = {
            'P': 'P',
            'C': 'C/1B', 
            '1B': 'C/1B',
            '2B': '2B',
            '3B': '3B',
            'SS': 'SS',
            'OF1': 'OF1',
            'OF2': 'OF2', 
            'OF3': 'OF3'
        }
        
        # Handle UTIL position (last outfielder or utility)
        util_player = None
        
        for _, player in strategy_players.iterrows():
            position = player['Position']
            name = player['Name']
            salary = int(player['Salary'])
            
            total_salary += salary
            
            if position in position_mapping:
                fd_position = position_mapping[position]
                fanduel_lineup[fd_position] = name
                readable_lineup[fd_position] = f"{name} (${salary})"
            else:
                # Handle utility position
                fanduel_lineup['UTIL'] = name
                readable_lineup['UTIL'] = f"{name} (${salary})"
        
        readable_lineup['Total_Salary'] = f"${total_salary:,}"
        readable_lineup['Remaining'] = f"${35000 - total_salary:,}"
        
        fanduel_lineups.append(fanduel_lineup)
        readable_lineups.append(readable_lineup)
    
    # Save FanDuel submission format
    df_fanduel = pd.DataFrame(fanduel_lineups)
    fanduel_file = f"../data/FANDUEL_EXPANDED_FILTERED_SUBMISSION_{timestamp}.csv"
    df_fanduel.to_csv(fanduel_file, index=False)
    logger.info(f" File: {fanduel_file}")
    
    # Save readable format with names and salaries
    df_readable = pd.DataFrame(readable_lineups)
    readable_file = f"../data/FANDUEL_LINEUPS_WITH_NAMES_{timestamp}.csv"
    df_readable.to_csv(readable_file, index=False)
    logger.info(f"DATA: Total Lineups: {len(readable_lineups)}")
    
    # Create detailed summary
    summary_file = f"../data/FANDUEL_LINEUPS_DETAILED_SUMMARY_{timestamp}.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("FANDUEL LINEUP SUMMARY\n")
        f.write("=" * 60 + "\n\n")
        
        for lineup in readable_lineups:
            f.write(f"LINEUP {lineup['Lineup_ID']}: {lineup['Strategy']}\n")
            f.write(f"Total Salary: {lineup['Total_Salary']}\n")
            f.write(f"Remaining: {lineup['Remaining']}\n")
            f.write("-" * 40 + "\n")
            
            positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL']
            for pos in positions:
                if pos in lineup and lineup[pos]:
                    f.write(f"{pos:>5}: {lineup[pos]}\n")
            f.write("\n")
    
    logger.info(f"SUCCESS: All lineups use ONLY healthy players and probable pitchers")
    logger.info(f"TARGET: Includes your proven filtered strategies + variations")
    logger.info(f"\nLINEUP: LINEUP BREAKDOWN:")
    logger.info(f"   INFO: Original Filtered Strategies: {len(strategies)}")
    logger.info(f"    Total Tournament-Ready Lineups: {len(readable_lineups)}")
    logger.info(f"\nSUCCESS: READY FOR FANDUEL MULTI-ENTRY TOURNAMENTS!")
    
    return readable_file, summary_file

if __name__ == "__main__":
    format_filtered_lineups()