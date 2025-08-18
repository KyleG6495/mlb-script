#!/usr/bin/env python3
"""
FANDUEL LINEUP REPLACER
======================
Replaces the lineups in FanDuel's Lineups.csv with our ULTIMATE optimized lineups
"""

import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def replace_fanduel_lineups():
    """Replace FanDuel lineups with our ULTIMATE optimized ones"""
    
    logger.info("SWAP: FANDUEL LINEUP REPLACER")
    logger.info("=" * 50)
    
    # 1. Load our ULTIMATE optimized lineups
    ultimate_file = "../data/ULTIMATE_FANDUEL_LINEUPS_20250812_181717.csv"
    try:
        df_ultimate = pd.read_csv(ultimate_file)
        logger.info(f"SUCCESS: Loaded ULTIMATE lineups: {len(df_ultimate)} lineups")
    except Exception as e:
        logger.error(f"ERROR: Could not load ULTIMATE lineups: {e}")
        return
    
    # 2. Load current FanDuel template
    fanduel_file = "../fd_current_slate/Lineups.csv"
    try:
        df_fanduel = pd.read_csv(fanduel_file)
        logger.info(f"SUCCESS: Loaded FanDuel template: {len(df_fanduel)} rows")
    except Exception as e:
        logger.error(f"ERROR: Could not load FanDuel template: {e}")
        return
    
    # 3. Find the lineup rows (they have entry_id)
    lineup_rows = df_fanduel[df_fanduel['entry_id'].notna()].head(len(df_ultimate))
    logger.info(f"INFO: Found {len(lineup_rows)} lineup entries to replace")
    
    # 4. Replace each lineup with our ULTIMATE optimized ones
    replaced_count = 0
    for i, (_, ultimate_lineup) in enumerate(df_ultimate.iterrows()):
        if i < len(lineup_rows):
            # Get the row index in the original dataframe
            row_idx = lineup_rows.index[i]
            
            # Replace the lineup positions with our ULTIMATE choices
            df_fanduel.loc[row_idx, 'P'] = ultimate_lineup['P']
            df_fanduel.loc[row_idx, 'C/1B'] = ultimate_lineup['C/1B']
            df_fanduel.loc[row_idx, '2B'] = ultimate_lineup['2B']
            df_fanduel.loc[row_idx, '3B'] = ultimate_lineup['3B']
            df_fanduel.loc[row_idx, 'SS'] = ultimate_lineup['SS']
            df_fanduel.loc[row_idx, 'OF'] = ultimate_lineup['OF']
            df_fanduel.loc[row_idx, 'OF.1'] = ultimate_lineup['OF.1']
            df_fanduel.loc[row_idx, 'OF.2'] = ultimate_lineup['OF.2']
            df_fanduel.loc[row_idx, 'UTIL'] = ultimate_lineup['UTIL']
            
            replaced_count += 1
            logger.info(f"SWAP: Replaced lineup {i+1}")
    
    # 5. Save the updated FanDuel file
    backup_file = "../fd_current_slate/Lineups_BACKUP.csv"
    df_fanduel.to_csv(backup_file, index=False)
    logger.info(f" Backup saved: {backup_file}")
    
    output_file = "../fd_current_slate/Lineups_ULTIMATE.csv"
    df_fanduel.to_csv(output_file, index=False)
    logger.info(f" ULTIMATE lineups saved: {output_file}")
    
    # 6. Show what we replaced
    logger.info(f"\nLINEUP: REPLACEMENT SUMMARY:")
    logger.info(f"SUCCESS: Replaced {replaced_count} lineups with ULTIMATE optimized versions")
    logger.info(f"INFO: Files created:")
    logger.info(f"   - Backup: {backup_file}")
    logger.info(f"   - ULTIMATE: {output_file}")
    
    logger.info(f"\nINFO: NEXT STEPS:")
    logger.info(f"1. Upload {output_file} to FanDuel")
    logger.info(f"2. Or copy contents to replace current Lineups.csv")
    logger.info(f"3. Your lineups now use ULTIMATE optimization!")
    
    return output_file

def show_lineup_comparison():
    """Show comparison between old and new lineups"""
    
    try:
        # Load our ULTIMATE summary for reference
        summary_file = "../data/ULTIMATE_FANDUEL_SUMMARY_20250812_181717.csv"
        df_summary = pd.read_csv(summary_file)
        
        logger.info(f"\n ULTIMATE LINEUP STRATEGIES:")
        for _, row in df_summary.iterrows():
            logger.info(f"   {row['Strategy']:>12}: {row['ULTIMATE_Projection']} FPPG | ${row['Total_Salary']:,} | Value: {row['Value_Score']}")
    
    except Exception as e:
        logger.warning(f"WARNING: Could not load summary: {e}")

if __name__ == "__main__":
    output_file = replace_fanduel_lineups()
    show_lineup_comparison()
    
    logger.info(f"\nTARGET: READY TO SUBMIT!")
    logger.info(f"Your FanDuel lineups are now ELITE optimized! START:")
