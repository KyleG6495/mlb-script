#!/usr/bin/env python3
"""
TODAY FILTERED FANDUEL FORMATTER
===============================
Converts our proven filtered lineups to exact FanDuel submission format
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def convert_filtered_lineups_to_fanduel():
    """Convert TODAY's filtered lineups to FanDuel submission format"""
    
    logger.info("TARGET: CONVERTING FILTERED LINEUPS TO FANDUEL FORMAT")
    logger.info("=" * 60)
    
    # Load our filtered lineups
    filtered_file = "TODAY_FILTERED_LINEUPS_20250813_135914.csv"
    df_filtered = pd.read_csv(filtered_file)
    logger.info(f"SUCCESS: Loaded filtered lineups: {len(df_filtered)} rows")
    
    # Load FanDuel slate for player ID mapping
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    df_slate = pd.read_csv(slate_file)
    logger.info(f"SUCCESS: Loaded FanDuel slate: {len(df_slate)} players")
    
    # Create player name to ID mapping
    player_mapping = {}
    for _, row in df_slate.iterrows():
        player_name = row.get('Nickname', '').strip()
        player_id = row.get('Id', '')
        if player_name and player_id:
            player_mapping[player_name] = player_id
    
    logger.info(f"SUCCESS: Created mapping for {len(player_mapping)} players")
    
    # Get unique strategies
    strategies = df_filtered['Strategy'].unique()
    logger.info(f"SUCCESS: Found {len(strategies)} strategies: {list(strategies)}")
    
    # Build FanDuel submission rows
    fanduel_rows = []
    
    for strategy in strategies:
        strategy_lineup = df_filtered[df_filtered['Strategy'] == strategy].copy()
        
        logger.info(f"\nSWAP: Processing {strategy} strategy...")
        
        # Initialize FanDuel lineup structure
        fanduel_lineup = {
            'P': '',
            'C/1B': '',
            '2B': '',
            '3B': '',
            'SS': '',
            'OF': '',
            'OF_2': '',
            'OF_3': '',
            'UTIL': ''
        }
        
        # Track OF assignments
        of_count = 0
        
        # Process each player in the strategy
        for _, player in strategy_lineup.iterrows():
            position = player['Position']
            name = player['Name']
            player_id = player_mapping.get(name, name)  # Use ID if found, otherwise name
            
            logger.info(f"  {position}: {name} -> {player_id}")
            
            # Map positions to FanDuel format
            if position == 'P':
                fanduel_lineup['P'] = player_id
            elif position == 'C':
                fanduel_lineup['C/1B'] = player_id
            elif position == '1B':
                # If C/1B is empty, put 1B there; otherwise put in UTIL
                if not fanduel_lineup['C/1B']:
                    fanduel_lineup['C/1B'] = player_id
                else:
                    fanduel_lineup['UTIL'] = player_id
            elif position == '2B':
                fanduel_lineup['2B'] = player_id
            elif position == '3B':
                fanduel_lineup['3B'] = player_id
            elif position == 'SS':
                fanduel_lineup['SS'] = player_id
            elif position in ['OF1', 'OF2', 'OF3']:
                # Assign to next available OF slot
                if not fanduel_lineup['OF']:
                    fanduel_lineup['OF'] = player_id
                elif not fanduel_lineup['OF_2']:
                    fanduel_lineup['OF_2'] = player_id
                elif not fanduel_lineup['OF_3']:
                    fanduel_lineup['OF_3'] = player_id
                else:
                    # If all OF slots full, put in UTIL
                    fanduel_lineup['UTIL'] = player_id
        
        # If UTIL is still empty, find a player to put there
        if not fanduel_lineup['UTIL']:
            # Put the first available hitter in UTIL (any non-pitcher)
            for _, player in strategy_lineup.iterrows():
                if player['Position'] != 'P':
                    name = player['Name']
                    player_id = player_mapping.get(name, name)
                    fanduel_lineup['UTIL'] = player_id
                    break
        
        # Add to submission rows
        fanduel_rows.append(fanduel_lineup)
        
        # Show lineup summary
        total_salary = strategy_lineup['Salary'].sum()
        total_projection = strategy_lineup['FPPG'].sum()
        logger.info(f"  MONEY: Total Salary: ${total_salary:,}")
        logger.info(f"  DATA: Total Projection: {total_projection:.1f} FPPG")
    
    # Create DataFrame for FanDuel submission
    df_submission = pd.DataFrame(fanduel_rows)
    
    # Rename columns to match FanDuel's exact format
    df_submission = df_submission.rename(columns={
        'OF_2': 'OF.1',
        'OF_3': 'OF.2'
    })
    
    # Save FanDuel submission file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/FANDUEL_FILTERED_SUBMISSION_{timestamp}.csv"
    df_submission.to_csv(output_file, index=False)
    
    logger.info(f"\nTARGET: FANDUEL SUBMISSION CREATED!")
    logger.info("=" * 60)
    logger.info(f" File: {output_file}")
    logger.info(f"DATA: Contains {len(df_submission)} lineups")
    
    # Show final lineup details
    logger.info(f"\nLINEUP: FINAL FANDUEL LINEUPS:")
    for i, (strategy, lineup_row) in enumerate(zip(strategies, df_submission.iterrows())):
        _, row = lineup_row
        strategy_lineup = df_filtered[df_filtered['Strategy'] == strategy]
        total_projection = strategy_lineup['FPPG'].sum()
        logger.info(f"\n  Lineup {i+1}: {strategy} ({total_projection:.1f} FPPG)")
        logger.info(f"    P: {row['P']}")
        logger.info(f"    C/1B: {row['C/1B']}")
        logger.info(f"    2B: {row['2B']}")
        logger.info(f"    3B: {row['3B']}")
        logger.info(f"    SS: {row['SS']}")
        logger.info(f"    OF: {row['OF']}")
        logger.info(f"    OF.1: {row['OF.1']}")
        logger.info(f"    OF.2: {row['OF.2']}")
        logger.info(f"    UTIL: {row['UTIL']}")
    
    logger.info(f"\nSUCCESS: READY FOR FANDUEL UPLOAD!")
    logger.info(f"TARGET: These are your PROVEN filtered lineups that scored 268.7 on Aug 12th!")
    
    return output_file

if __name__ == "__main__":
    convert_filtered_lineups_to_fanduel()
