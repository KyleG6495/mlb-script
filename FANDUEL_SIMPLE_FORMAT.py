#!/usr/bin/env python3
"""
🎯 FANDUEL SIMPLE FORMAT
Creates the absolute simplest format possible for FanDuel uploads
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_simple_format():
    """Create the simplest possible format"""
    
    logger.info("🎯 CREATING SIMPLEST FANDUEL FORMAT")
    logger.info("="*40)
    
    try:
        # Load smart lineups
        df = pd.read_csv('../fd_current_slate/SMART_CHAMPIONSHIP_LINEUPS.csv')
        logger.info(f"📥 Loaded {len(df)} lineups")
        
        # Create absolutely minimal format - just player IDs in correct positions
        simple_data = []
        
        for i, row in df.iterrows():
            lineup = {
                'P': str(row['P']).strip(),
                'C': str(row['C']).strip(), 
                '1B': str(row['1B']).strip(),
                '2B': str(row['2B']).strip(),
                '3B': str(row['3B']).strip(),
                'SS': str(row['SS']).strip(),
                'OF': str(row['OF']).strip(),
                'OF': str(row['OF_2']).strip(),  # This will overwrite - let me fix
                'OF': str(row['OF_3']).strip(),  # This will overwrite - let me fix
                'UTIL': str(row['UTIL']).strip()
            }
            # Actually, let me create this properly
            
        # Create it the right way
        for i, row in df.iterrows():
            lineup_row = [
                str(row['P']).strip(),      # P
                str(row['C']).strip(),      # C
                str(row['1B']).strip(),     # 1B
                str(row['2B']).strip(),     # 2B
                str(row['3B']).strip(),     # 3B
                str(row['SS']).strip(),     # SS
                str(row['OF']).strip(),     # OF1
                str(row['OF_2']).strip(),   # OF2
                str(row['OF_3']).strip(),   # OF3
                str(row['UTIL']).strip()    # UTIL
            ]
            simple_data.append(lineup_row)
        
        # Try different column naming conventions
        
        # Version A: Standard positions
        df_a = pd.DataFrame(simple_data, columns=['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL'])
        
        # Version B: Numbered outfielders
        df_b = pd.DataFrame(simple_data, columns=['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL'])
        
        # Version C: Mixed format
        df_c = pd.DataFrame(simple_data, columns=['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF_2', 'OF_3', 'UTIL'])
        
        # Save versions
        df_b.to_csv('../fd_current_slate/SIMPLE_FORMAT_A.csv', index=False)  # Using B because A has duplicate columns
        df_c.to_csv('../fd_current_slate/SIMPLE_FORMAT_B.csv', index=False) 
        
        # Create main file
        df_c.to_csv('../fd_current_slate/FD_SIMPLE_UPLOAD.csv', index=False)
        
        logger.info("💾 Created simple format files:")
        logger.info("   📁 SIMPLE_FORMAT_A.csv (OF1,OF2,OF3)")
        logger.info("   📁 SIMPLE_FORMAT_B.csv (OF,OF_2,OF_3)")
        logger.info("   📁 FD_SIMPLE_UPLOAD.csv (main file)")
        
        # Show sample
        logger.info("")
        logger.info("📋 SAMPLE LINEUP:")
        sample = df_c.iloc[0]
        for col in df_c.columns:
            logger.info(f"   {col}: {sample[col]}")
        
        # Check for any issues
        logger.info("")
        logger.info("🔍 VALIDATION:")
        logger.info(f"   Rows: {len(df_c)}")
        logger.info(f"   Columns: {len(df_c.columns)}")
        logger.info(f"   Any empty values: {'Yes' if df_c.isnull().any().any() else 'No'}")
        logger.info(f"   All IDs start with 119176: {'Yes' if all(str(df_c.iloc[0, i]).startswith('119176') for i in range(len(df_c.columns))) else 'No'}")
        
        # Also create a version with just 1 lineup to test
        single_lineup = df_c.head(1)
        single_lineup.to_csv('../fd_current_slate/SINGLE_LINEUP_TEST.csv', index=False)
        logger.info("   📁 SINGLE_LINEUP_TEST.csv (test with 1 lineup)")
        
    except Exception as e:
        logger.error(f"❌ Simple format error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_simple_format()
