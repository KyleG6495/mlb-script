#!/usr/bin/env python3
"""
Show winning lineup details with player names
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def show_winning_lineups():
    """Show the winning lineup details"""
    
    # Load the winning lineups
    lineups = pd.read_csv('../data/WINNING_LINEUPS.csv')
    
    # Load player data for names
    players = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
    
    logger.info("LINEUP: WINNING LINEUP DETAILS")
    logger.info("="*50)
    
    for idx, lineup in lineups.iterrows():
        lineup_num = idx + 1
        logger.info(f"")
        logger.info(f"LINEUP: LINEUP {lineup_num} - ${lineup['Salary']:,} | {lineup['FPPG']:.1f} FPPG")
        
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL']
        
        for pos in positions:
            player_id = lineup[pos]
            if player_id and player_id != '':
                player_info = players[players['Id'] == player_id]
                if len(player_info) > 0:
                    player = player_info.iloc[0]
                    pos_display = pos.replace('C/1B', 'C').replace('OF1', 'OF').replace('OF2', 'OF').replace('OF3', 'OF')
                    logger.info(f"   {pos_display:4}: {player['Nickname']} ({player['Team']}) - ${player['Salary']} | {player['FPPG']:.1f} FPPG")
    
    logger.info("")
    logger.info("="*50)
    logger.info(f"DATA: {len(lineups)} WINNING LINEUPS CREATED")
    logger.info(f"MONEY: Salary range: ${lineups['Salary'].min():,} - ${lineups['Salary'].max():,}")
    logger.info(f"PROGRESS: FPPG range: {lineups['FPPG'].min():.1f} - {lineups['FPPG'].max():.1f}")

if __name__ == "__main__":
    show_winning_lineups()
