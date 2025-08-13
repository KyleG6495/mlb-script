#!/usr/bin/env python3
"""
CLEAN FANDUEL UPLOADER
=====================
Creates a clean upload file with just our ULTIMATE lineups
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_clean_upload():
    """Create a clean upload file with just ULTIMATE lineups"""
    
    # Load our ULTIMATE lineups
    ultimate_file = "../data/ULTIMATE_FANDUEL_LINEUPS_20250812_181717.csv"
    df_ultimate = pd.read_csv(ultimate_file)
    
    # Create clean upload format
    upload_data = []
    
    # Add header
    upload_data.append({
        'P': 'P',
        'C/1B': 'C/1B', 
        '2B': '2B',
        '3B': '3B',
        'SS': 'SS',
        'OF': 'OF',
        'OF.1': 'OF.1',
        'OF.2': 'OF.2',
        'UTIL': 'UTIL'
    })
    
    # Add each ULTIMATE lineup
    for _, lineup in df_ultimate.iterrows():
        upload_data.append({
            'P': lineup['P'],
            'C/1B': lineup['C/1B'],
            '2B': lineup['2B'],
            '3B': lineup['3B'],
            'SS': lineup['SS'],
            'OF': lineup['OF'],
            'OF.1': lineup['OF.1'],
            'OF.2': lineup['OF.2'],
            'UTIL': lineup['UTIL']
        })
    
    # Save clean upload file
    df_upload = pd.DataFrame(upload_data)
    upload_file = "../fd_current_slate/CLEAN_ULTIMATE_UPLOAD.csv"
    df_upload.to_csv(upload_file, index=False)
    
    logger.info(f"✅ Clean upload file created: {upload_file}")
    logger.info(f"📋 Contains {len(df_ultimate)} ULTIMATE optimized lineups")
    logger.info(f"🎯 Ready for FanDuel upload!")
    
    return upload_file

if __name__ == "__main__":
    create_clean_upload()
