#!/usr/bin/env python3
"""
FANDUEL CLEAN MINIMAL UPLOADER
==============================
Creates the cleanest possible format for FanDuel upload
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_minimal_clean_format():
    """Create the minimal clean format for FanDuel"""
    
    logger.info("🧹 CREATING MINIMAL CLEAN FORMAT")
    logger.info("=" * 50)
    
    # Load original to get entry info
    df_original = pd.read_csv("../fd_current_slate/Lineups.csv")
    
    # Load our ULTIMATE lineups
    df_ultimate = pd.read_csv("../data/ULTIMATE_FANDUEL_LINEUPS_20250812_181717.csv")
    
    # Get the first 5 actual lineup entries (with entry_id)
    lineup_entries = df_original[df_original['entry_id'].notna()].head(5)
    
    # Create clean data with ONLY the essential columns
    clean_data = []
    
    for i, (_, entry) in enumerate(lineup_entries.iterrows()):
        if i < len(df_ultimate):
            ultimate_lineup = df_ultimate.iloc[i]
            
            clean_entry = {
                'entry_id': int(float(entry['entry_id'])),  # Remove decimal
                'contest_id': entry['contest_id'],
                'contest_name': entry['contest_name'],
                'entry_fee': entry['entry_fee'],
                'P': ultimate_lineup['P'],
                'C/1B': ultimate_lineup['C/1B'],
                '2B': ultimate_lineup['2B'],
                '3B': ultimate_lineup['3B'],
                'SS': ultimate_lineup['SS'],
                'OF': ultimate_lineup['OF'],
                'OF.1': ultimate_lineup['OF.1'],
                'OF.2': ultimate_lineup['OF.2'],
                'UTIL': ultimate_lineup['UTIL']
            }
            clean_data.append(clean_entry)
    
    # Create DataFrame with clean data
    df_clean = pd.DataFrame(clean_data)
    
    # Save minimal clean file
    output_file = "../fd_current_slate/FANDUEL_MINIMAL_CLEAN.csv"
    df_clean.to_csv(output_file, index=False)
    
    logger.info(f"✅ Minimal clean format saved: {output_file}")
    logger.info(f"📊 Contains {len(clean_data)} lineups")
    
    # Also create an even simpler version with just player IDs
    simple_data = []
    for _, lineup in df_ultimate.iterrows():
        simple_data.append([
            lineup['P'],
            lineup['C/1B'],
            lineup['2B'],
            lineup['3B'],
            lineup['SS'],
            lineup['OF'],
            lineup['OF.1'],
            lineup['OF.2'],
            lineup['UTIL']
        ])
    
    df_simple = pd.DataFrame(simple_data, columns=['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL'])
    simple_file = "../fd_current_slate/FANDUEL_SUPER_SIMPLE.csv"
    df_simple.to_csv(simple_file, index=False)
    
    logger.info(f"✅ Super simple format saved: {simple_file}")
    
    return output_file, simple_file

def show_manual_entry_option():
    """Show manual entry as backup"""
    
    logger.info(f"\n🖱️ MANUAL ENTRY BACKUP OPTION:")
    logger.info("If CSV upload still fails, manually enter these lineups:")
    
    # Load our summary
    try:
        df_summary = pd.read_csv("../data/ULTIMATE_FANDUEL_SUMMARY_20250812_181717.csv")
        
        logger.info(f"\n🏆 TOP RECOMMENDATION - LINEUP 1 (BALANCED):")
        logger.info(f"📊 Projection: {df_summary.iloc[0]['ULTIMATE_Projection']} FPPG")
        logger.info(f"💰 Salary: ${df_summary.iloc[0]['Total_Salary']:,}")
        logger.info("📋 Players:")
        logger.info("   P: Shane Bieber")
        logger.info("   C/1B: Braxton Fulford")
        logger.info("   2B: Thairo Estrada")
        logger.info("   3B: Kyle Karros")
        logger.info("   SS: Ezequiel Tovar")
        logger.info("   OF: Everson Pereira")
        logger.info("   OF: Wyatt Langford")
        logger.info("   OF: Daulton Varsho")
        logger.info("   UTIL: Rowdy Tellez")
        
    except Exception as e:
        logger.warning(f"Could not load summary: {e}")

if __name__ == "__main__":
    minimal_file, simple_file = create_minimal_clean_format()
    show_manual_entry_option()
    
    logger.info(f"\n🎯 TRY THESE OPTIONS:")
    logger.info(f"1. Upload: {minimal_file}")
    logger.info(f"2. Upload: {simple_file}")
    logger.info(f"3. Manual entry (see above)")
    logger.info(f"4. Copy-paste individual player IDs")
