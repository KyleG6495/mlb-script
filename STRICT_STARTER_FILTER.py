#!/usr/bin/env python3
"""
🔒 STRICT STARTER FILTER
ONLY includes players with confirmed batting orders (1-9) or confirmed probable pitchers
NO salary thresholds - ONLY confirmed information
This is the most restrictive filter to eliminate ALL non-starters
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_strict_starter_slate():
    """Create slate with ONLY confirmed starters - no guessing based on salary"""
    
    logger.info("🔒 CREATING STRICT STARTER SLATE")
    logger.info("="*50)
    logger.info("ONLY confirmed batting orders (1-9) + confirmed probable pitchers")
    logger.info("NO salary-based guessing - CONFIRMED STARTERS ONLY")
    logger.info("")
    
    try:
        # Load original slate
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📥 Loaded original slate: {len(df)} players")
        
        # STRICT CONFIRMED STARTERS ONLY
        strict_starters = df[
            # Hitters with batting orders 1-9 (confirmed starters)
            ((df['Batting Order'].notna()) & 
             (df['Batting Order'] >= 1) & 
             (df['Batting Order'] <= 9) &
             (df['Position'] != 'P')) |
            # Probable starting pitchers ONLY
            ((df['Position'] == 'P') & 
             (df['Probable Pitcher'] == 'Yes'))
        ].copy()
        
        # Remove IL players
        strict_starters = strict_starters[strict_starters['Injury Indicator'] != 'IL'].copy()
        
        logger.info(f"✅ Strict confirmed starters: {len(strict_starters)}")
        
        # VERIFY NO NOLAN GORMAN
        gorman_check = strict_starters[strict_starters['Nickname'].str.contains('Gorman', na=False)]
        if len(gorman_check) > 0:
            logger.error(f"❌ NOLAN GORMAN FOUND IN STRICT SLATE!")
            logger.error(f"Gorman entries: {gorman_check[['Nickname', 'Team', 'Batting Order', 'Position']].to_dict('records')}")
        else:
            logger.info("✅ VERIFIED: No Nolan Gorman in strict slate")
        
        # Position breakdown
        logger.info("")
        logger.info("🏟️ STRICT POSITION BREAKDOWN:")
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            if pos == 'OF':
                pos_count = len(strict_starters[
                    (strict_starters['Position'] == pos) |
                    (strict_starters['Position'].str.contains(pos, na=False)) |
                    (strict_starters['Roster Position'].str.contains(pos, na=False))
                ])
            else:
                pos_count = len(strict_starters[
                    (strict_starters['Position'] == pos) |
                    (strict_starters['Position'].str.contains(pos, na=False)) |
                    (strict_starters['Roster Position'].str.contains(pos, na=False))
                ])
            logger.info(f"   {pos}: {pos_count} players")
        
        # Check minimum requirements for lineups
        positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        logger.info("")
        logger.info("📋 LINEUP FEASIBILITY CHECK:")
        lineup_possible = True
        
        for pos, needed in positions_needed.items():
            if pos == 'OF':
                available = len(strict_starters[
                    (strict_starters['Position'] == pos) |
                    (strict_starters['Position'].str.contains(pos, na=False)) |
                    (strict_starters['Roster Position'].str.contains(pos, na=False))
                ])
            else:
                available = len(strict_starters[
                    (strict_starters['Position'] == pos) |
                    (strict_starters['Position'].str.contains(pos, na=False)) |
                    (strict_starters['Roster Position'].str.contains(pos, na=False))
                ])
            
            status = "✅" if available >= needed else "❌"
            logger.info(f"   {pos}: {available} available (need {needed}) {status}")
            
            if available < needed:
                lineup_possible = False
        
        if lineup_possible:
            logger.info("✅ Lineups are possible with strict starters")
        else:
            logger.warning("⚠️ May not have enough players for full lineups")
        
        # Save strict starter slate
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save with timestamp
        strict_file = f'../data/fd_slate_strict_starters_{timestamp}.csv'
        strict_starters.to_csv(strict_file, index=False)
        
        # Save as main file
        main_file = '../data/fd_slate_STRICT_STARTERS.csv'
        strict_starters.to_csv(main_file, index=False)
        
        # Also save in fd_current_slate for easy access
        easy_file = '../fd_current_slate/fd_slate_strict_starters.csv'
        strict_starters.to_csv(easy_file, index=False)
        
        logger.info("")
        logger.info("💾 STRICT STARTER SLATE SAVED:")
        logger.info(f"   📁 Timestamped: {strict_file}")
        logger.info(f"   📁 Main file: {main_file}")
        logger.info(f"   📁 Easy access: {easy_file}")
        
        logger.info("")
        logger.info("🎉 STRICT STARTER FILTER COMPLETE!")
        logger.info("="*50)
        logger.info(f"✅ {len(strict_starters)} CONFIRMED STARTERS ONLY")
        logger.info("🔒 NO salary-based guessing - batting orders + probable pitchers ONLY")
        logger.info("🚫 ZERO chance of NS/PO players in lineups")
        
        return strict_starters
        
    except Exception as e:
        logger.error(f"❌ Strict starter filter error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_strict_starter_slate()
