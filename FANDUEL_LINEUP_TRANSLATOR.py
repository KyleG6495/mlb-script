#!/usr/bin/env python3
"""
FANDUEL LINEUP TRANSLATOR
========================
Shows our ULTIMATE lineups with actual player names for manual entry
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def translate_lineups_to_names():
    """Translate our ULTIMATE lineups to player names"""
    
    logger.info(" TRANSLATING ULTIMATE LINEUPS TO PLAYER NAMES")
    logger.info("=" * 60)
    
    # Load FanDuel slate for player lookup
    df_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # Load our ULTIMATE lineups
    df_ultimate = pd.read_csv("../data/ULTIMATE_FANDUEL_LINEUPS_20250812_181717.csv")
    
    # Load our summary for strategy names
    df_summary = pd.read_csv("../data/ULTIMATE_FANDUEL_SUMMARY_20250812_181717.csv")
    
    lineup_names = []
    
    for i, (_, lineup) in enumerate(df_ultimate.iterrows()):
        strategy = df_summary.iloc[i]['Strategy']
        projection = df_summary.iloc[i]['ULTIMATE_Projection']
        salary = df_summary.iloc[i]['Total_Salary']
        
        logger.info(f"\nLINEUP: LINEUP {i+1}: {strategy} Strategy")
        logger.info(f"DATA: Projection: {projection} FPPG | MONEY: Salary: ${salary:,}")
        logger.info("-" * 50)
        
        lineup_data = {}
        
        for pos in ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']:
            player_id = lineup[pos]
            
            # Find player in slate
            player_match = df_slate[df_slate['Id'] == player_id]
            if len(player_match) > 0:
                player = player_match.iloc[0]
                player_name = player['Nickname']
                player_salary = player['Salary']
                player_team = player['Team']
                
                logger.info(f"  {pos:>5}: {player_name:<20} | ${player_salary:<5} | {player_team}")
                
                lineup_data[pos] = {
                    'name': player_name,
                    'id': player_id,
                    'salary': player_salary,
                    'team': player_team
                }
            else:
                logger.warning(f"  {pos:>5}: Player ID {player_id} not found!")
                lineup_data[pos] = {'name': 'NOT FOUND', 'id': player_id}
        
        lineup_names.append(lineup_data)
    
    # Create manual entry guide
    logger.info(f"\nINFO: MANUAL ENTRY GUIDE:")
    logger.info("=" * 60)
    logger.info("Copy these lineups into FanDuel manually:")
    
    for i, lineup in enumerate(lineup_names):
        strategy = df_summary.iloc[i]['Strategy']
        logger.info(f"\nTARGET: LINEUP {i+1} ({strategy}):")
        
        for pos in ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']:
            if pos in lineup:
                player_name = lineup[pos]['name']
                logger.info(f"  {pos}: {player_name}")
    
    return lineup_names

if __name__ == "__main__":
    translate_lineups_to_names()
