#!/usr/bin/env python3
"""
FANDUEL EXACT FORMAT REPLACER
============================
Creates the EXACT format FanDuel expects with our ULTIMATE lineups
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_exact_fanduel_format():
    """Create the EXACT format FanDuel expects"""
    
    logger.info("TARGET: CREATING EXACT FANDUEL FORMAT")
    logger.info("=" * 50)
    
    # Load current FanDuel template
    df_fanduel = pd.read_csv("../fd_current_slate/Lineups.csv")
    
    # Load our ULTIMATE lineups
    df_ultimate = pd.read_csv("../data/ULTIMATE_FANDUEL_LINEUPS_20250812_181717.csv")
    
    logger.info(f"SUCCESS: Loaded FanDuel template: {len(df_fanduel)} rows")
    logger.info(f"SUCCESS: Loaded ULTIMATE lineups: {len(df_ultimate)} lineups")
    
    # Find rows with entry_id (actual lineup entries)
    lineup_rows = df_fanduel[df_fanduel['entry_id'].notna()]
    
    logger.info(f"INFO: Found {len(lineup_rows)} existing lineup entries")
    
    # Replace the first 5 lineup entries with our ULTIMATE lineups
    for i in range(min(5, len(lineup_rows), len(df_ultimate))):
        row_idx = lineup_rows.index[i]
        ultimate_lineup = df_ultimate.iloc[i]
        
        # Replace ONLY the player positions, keep all other FanDuel data
        df_fanduel.loc[row_idx, 'P'] = ultimate_lineup['P']
        df_fanduel.loc[row_idx, 'C/1B'] = ultimate_lineup['C/1B']
        df_fanduel.loc[row_idx, '2B'] = ultimate_lineup['2B']
        df_fanduel.loc[row_idx, '3B'] = ultimate_lineup['3B']
        df_fanduel.loc[row_idx, 'SS'] = ultimate_lineup['SS']
        
        # Handle the OF columns (FanDuel has OF, OF, OF but our file has OF, OF.1, OF.2)
        df_fanduel.loc[row_idx, df_fanduel.columns[9]] = ultimate_lineup['OF']      # First OF column
        df_fanduel.loc[row_idx, df_fanduel.columns[10]] = ultimate_lineup['OF.1']   # Second OF column  
        df_fanduel.loc[row_idx, df_fanduel.columns[11]] = ultimate_lineup['OF.2']   # Third OF column
        
        df_fanduel.loc[row_idx, 'UTIL'] = ultimate_lineup['UTIL']
        
        logger.info(f"SWAP: Replaced lineup entry {i+1}")
    
    # Save the corrected file
    output_file = "../fd_current_slate/FANDUEL_EXACT_FORMAT_CORRECTED.csv"
    df_fanduel.to_csv(output_file, index=False)
    
    logger.info(f"\n EXACT FanDuel format saved: {output_file}")
    logger.info(f"INFO: This file has:")
    logger.info(f"   SUCCESS: All original FanDuel headers and contest info")
    logger.info(f"   SUCCESS: Your 5 ULTIMATE optimized lineups")
    logger.info(f"   SUCCESS: All player reference data intact")
    
    logger.info(f"\nTARGET: UPLOAD INSTRUCTIONS:")
    logger.info(f"1. Use this file: {output_file}")
    logger.info(f"2. Upload to FanDuel CSV import")
    logger.info(f"3. Your lineups are now ULTIMATE optimized!")
    
    return output_file

if __name__ == "__main__":
    create_exact_fanduel_format()
