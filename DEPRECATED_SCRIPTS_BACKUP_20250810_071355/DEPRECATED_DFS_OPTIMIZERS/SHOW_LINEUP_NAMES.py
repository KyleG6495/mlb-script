#!/usr/bin/env python3
"""
📋 LINEUP SUMMARY GENERATOR
Shows exactly who is in each lineup with names and positions
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def show_lineup_summary():
    """Show detailed summary of all lineups"""
    
    logger.info("📋 CURRENT LINEUP SUMMARY")
    logger.info("="*80)
    
    try:
        # Load the lineups
        df = pd.read_csv('../fd_current_slate/SMART_CHAMPIONSHIP_LINEUPS.csv')
        
        for i, row in df.iterrows():
            lineup_num = i + 1
            logger.info(f"")
            logger.info(f"🏆 LINEUP {lineup_num} - ${row['Salary']:,} | {row['FPPG']:.1f} FPPG")
            logger.info(f"   P:    {row['P_Name']}")
            logger.info(f"   C:    {row['C_Name']}")
            logger.info(f"   1B:   {row['1B_Name']}")
            logger.info(f"   2B:   {row['2B_Name']}")
            logger.info(f"   3B:   {row['3B_Name']}")
            logger.info(f"   SS:   {row['SS_Name']}")
            logger.info(f"   OF1:  {row['OF_Name']}")
            logger.info(f"   OF2:  {row['OF_2_Name']}")
            logger.info(f"   OF3:  {row['OF_3_Name']}")
            logger.info(f"   UTIL: {row['UTIL_Name']}")
        
        logger.info("")
        logger.info("="*80)
        logger.info(f"📊 SUMMARY: {len(df)} lineups created")
        logger.info(f"💰 Salary range: ${df['Salary'].min():,} - ${df['Salary'].max():,}")
        logger.info(f"📈 FPPG range: {df['FPPG'].min():.1f} - {df['FPPG'].max():.1f}")
        
    except Exception as e:
        logger.error(f"❌ Error reading lineups: {e}")

if __name__ == "__main__":
    show_lineup_summary()
