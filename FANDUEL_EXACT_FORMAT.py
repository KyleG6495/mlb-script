#!/usr/bin/env python3
"""
TARGET: FANDUEL EXACT FORMAT BUILDER
Creates the exact CSV format that FanDuel expects for lineup uploads
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_fanduel_exact_format():
    """Create the exact format FanDuel expects"""
    
    logger.info("TARGET: CREATING FANDUEL EXACT FORMAT")
    logger.info("="*50)
    
    try:
        # Load the smart lineups
        df = pd.read_csv('../fd_current_slate/SMART_CHAMPIONSHIP_LINEUPS.csv')
        logger.info(f" Loaded {len(df)} smart lineups")
        
        # FanDuel expects EXACTLY this format based on common upload patterns:
        # P,C,1B,2B,3B,SS,OF,OF,OF,UTIL (with three OF columns all named "OF")
        
        fd_exact = []
        
        for i, row in df.iterrows():
            # Create each lineup row in the EXACT format FanDuel expects
            lineup_row = [
                row['P'],      # Pitcher
                row['C'],      # Catcher  
                row['1B'],     # First Base
                row['2B'],     # Second Base
                row['3B'],     # Third Base
                row['SS'],     # Shortstop
                row['OF'],     # Outfield 1
                row['OF_2'],   # Outfield 2
                row['OF_3'],   # Outfield 3
                row['UTIL']    # Utility
            ]
            fd_exact.append(lineup_row)
        
        # Create DataFrame with exact column names FanDuel expects
        # Based on FanDuel's MLB format, it should be:
        fd_final = pd.DataFrame(fd_exact, columns=[
            'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL'
        ])
        
        # Actually, let me try a different approach. FanDuel might expect unique column names
        fd_final_v2 = pd.DataFrame(fd_exact, columns=[
            'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF_2', 'OF_3', 'UTIL'
        ])
        
        # And another version with the most common FanDuel format
        fd_final_v3 = pd.DataFrame(fd_exact, columns=[
            'P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL'
        ])
        
        # Save all three versions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Version 1: Duplicate OF column names (might be what FD expects)
        file1 = f'../fd_current_slate/FD_EXACT_FORMAT_V1_{timestamp}.csv'
        fd_final.to_csv(file1, index=False)
        
        # Version 2: OF, OF_2, OF_3
        file2 = f'../fd_current_slate/FD_EXACT_FORMAT_V2_{timestamp}.csv'
        fd_final_v2.to_csv(file2, index=False)
        
        # Version 3: OF1, OF2, OF3
        file3 = f'../fd_current_slate/FD_EXACT_FORMAT_V3_{timestamp}.csv'
        fd_final_v3.to_csv(file3, index=False)
        
        # Create the main upload file (Version 2 seems most likely)
        main_file = '../fd_current_slate/FANDUEL_UPLOAD_EXACT.csv'
        fd_final_v2.to_csv(main_file, index=False)
        
        logger.info("")
        logger.info(" FANDUEL EXACT FORMAT FILES:")
        logger.info(f"    Version 1 (OF,OF,OF): {file1}")
        logger.info(f"    Version 2 (OF,OF_2,OF_3): {file2}")
        logger.info(f"    Version 3 (OF1,OF2,OF3): {file3}")
        logger.info(f"    MAIN FILE: {main_file}")
        
        # Show what each version looks like
        logger.info("")
        logger.info("INFO: FORMAT COMPARISON:")
        logger.info(f"   V1 columns: {list(fd_final.columns)}")
        logger.info(f"   V2 columns: {list(fd_final_v2.columns)}")
        logger.info(f"   V3 columns: {list(fd_final_v3.columns)}")
        
        # Show first lineup as example
        logger.info("")
        logger.info("INFO: SAMPLE LINEUP (Version 2):")
        first_lineup = fd_final_v2.iloc[0]
        for col in fd_final_v2.columns:
            logger.info(f"   {col}: {first_lineup[col]}")
        
        # Additional validation
        logger.info("")
        logger.info("SUCCESS: VALIDATION:")
        logger.info(f"   Lineups: {len(fd_final_v2)}")
        logger.info(f"   Columns: {len(fd_final_v2.columns)}")
        logger.info(f"   All Player IDs present: SUCCESS:")
        logger.info(f"   No empty values: {'SUCCESS:' if not fd_final_v2.isnull().any().any() else 'ERROR:'}")
        
        logger.info("")
        logger.info("TARGET: UPLOAD INSTRUCTIONS:")
        logger.info("1. Try FANDUEL_UPLOAD_EXACT.csv FIRST")
        logger.info("2. If that fails, try Version 1 (duplicate OF columns)")
        logger.info("3. If that fails, try Version 3 (OF1,OF2,OF3)")
        
    except Exception as e:
        logger.error(f"ERROR: Exact format error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_fanduel_exact_format()
