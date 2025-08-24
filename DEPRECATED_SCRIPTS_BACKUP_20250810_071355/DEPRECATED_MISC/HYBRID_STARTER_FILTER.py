#!/usr/bin/env python3
"""
🎯 HYBRID STARTER FILTER
Uses confirmed starters PLUS likely starters (removes only obvious bench/IL players)
Balances avoiding NS/PO players while keeping enough players for FanDuel validation
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_hybrid_starter_slate():
    """Create slate with confirmed starters + likely starters"""
    
    logger.info("🎯 CREATING HYBRID STARTER SLATE")
    logger.info("="*50)
    logger.info("Keeps confirmed starters + likely starters, removes obvious non-starters")
    logger.info("")
    
    try:
        # Load original slate
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📥 Loaded original slate: {len(df)} players")
        
        # CONFIRMED STARTERS (batting order 1-9 or probable pitcher)
        confirmed_starters = df[
            # Hitters with batting orders
            ((df['Batting Order'].notna()) & 
             (df['Batting Order'] > 0) & 
             (df['Batting Order'] <= 9)) |
            # Probable starting pitchers
            ((df['Position'] == 'P') & 
             (df['Probable Pitcher'] == 'Yes'))
        ].copy()
        
        logger.info(f"✅ Confirmed starters: {len(confirmed_starters)}")
        
        # LIKELY STARTERS (high salary players without confirmed batting orders)
        remaining_players = df[~df['Id'].isin(confirmed_starters['Id'])].copy()
        
        # For hitters: Use salary thresholds by position
        hitters = remaining_players[remaining_players['Position'] != 'P'].copy()
        
        likely_hitters = []
        
        # Position-based salary thresholds for likely starters
        position_thresholds = {
            'C': 2200,    # Catchers $2200+
            '1B': 2400,   # First base $2400+
            '2B': 2200,   # Second base $2200+
            '3B': 2400,   # Third base $2400+
            'SS': 2400,   # Shortstop $2400+
            'OF': 2300    # Outfield $2300+
        }
        
        for pos, threshold in position_thresholds.items():
            pos_players = hitters[
                (hitters['Position'].str.contains(pos, na=False)) |
                (hitters['Roster Position'].str.contains(pos, na=False))
            ]
            
            # Take top players by salary at each position
            pos_likely = pos_players[
                (pos_players['Salary'] >= threshold) &
                (pos_players['Injury Indicator'] != 'IL')  # Not on IL
            ].nlargest(15, 'Salary')  # Top 15 by salary per position
            
            likely_hitters.append(pos_likely)
            logger.info(f"   {pos}: {len(pos_likely)} likely starters (${threshold}+)")
        
        # For pitchers: Include higher salary pitchers even without "Probable" status
        pitchers = remaining_players[remaining_players['Position'] == 'P'].copy()
        likely_pitchers = pitchers[
            (pitchers['Salary'] >= 7000) &  # $7000+ pitchers
            (pitchers['Injury Indicator'] != 'IL')
        ].nlargest(25, 'Salary')  # Top 25 pitchers by salary
        
        logger.info(f"   P: {len(likely_pitchers)} likely starting pitchers ($7000+)")
        
        # Combine all likely starters
        all_likely_hitters = pd.concat(likely_hitters, ignore_index=True) if likely_hitters else pd.DataFrame()
        
        # Remove duplicates from likely starters
        if len(all_likely_hitters) > 0:
            all_likely_hitters = all_likely_hitters.drop_duplicates(subset=['Id'], keep='first')
        
        # Combine confirmed + likely starters
        hybrid_starters = pd.concat([
            confirmed_starters,
            all_likely_hitters,
            likely_pitchers
        ], ignore_index=True)
        
        # Remove duplicates (keep confirmed starters first)
        hybrid_starters = hybrid_starters.drop_duplicates(subset=['Id'], keep='first')
        
        # Remove IL players
        hybrid_starters = hybrid_starters[hybrid_starters['Injury Indicator'] != 'IL'].copy()
        
        logger.info("")
        logger.info("📊 HYBRID STARTER ANALYSIS:")
        logger.info(f"   Original slate: {len(df)} players")
        logger.info(f"   Confirmed starters: {len(confirmed_starters)}")
        logger.info(f"   Likely starters added: {len(hybrid_starters) - len(confirmed_starters)}")
        logger.info(f"   Total hybrid slate: {len(hybrid_starters)}")
        logger.info(f"   Players filtered out: {len(df) - len(hybrid_starters)}")
        
        # Position breakdown
        logger.info("")
        logger.info("🏟️ POSITION BREAKDOWN:")
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            if pos == 'OF':
                pos_count = len(hybrid_starters[
                    (hybrid_starters['Position'] == pos) |
                    (hybrid_starters['Position'].str.contains(pos, na=False)) |
                    (hybrid_starters['Roster Position'].str.contains(pos, na=False))
                ])
            else:
                pos_count = len(hybrid_starters[
                    (hybrid_starters['Position'] == pos) |
                    (hybrid_starters['Position'].str.contains(pos, na=False)) |
                    (hybrid_starters['Roster Position'].str.contains(pos, na=False))
                ])
            logger.info(f"   {pos}: {pos_count} players")
        
        # Save hybrid starter slate
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save with timestamp
        hybrid_file = f'../data/fd_slate_hybrid_starters_{timestamp}.csv'
        hybrid_starters.to_csv(hybrid_file, index=False)
        
        # Save as main file
        main_file = '../data/fd_slate_HYBRID_STARTERS.csv'
        hybrid_starters.to_csv(main_file, index=False)
        
        # Also save in fd_current_slate for easy access
        easy_file = '../fd_current_slate/fd_slate_hybrid_starters.csv'
        hybrid_starters.to_csv(easy_file, index=False)
        
        logger.info("")
        logger.info("💾 HYBRID STARTER SLATE SAVED:")
        logger.info(f"   📁 Timestamped: {hybrid_file}")
        logger.info(f"   📁 Main file: {main_file}")
        logger.info(f"   📁 Easy access: {easy_file}")
        
        logger.info("")
        logger.info("🎉 HYBRID STARTER FILTER COMPLETE!")
        logger.info("="*50)
        logger.info(f"✅ Expanded from {len(confirmed_starters)} to {len(hybrid_starters)} players")
        logger.info("🎯 Prioritizes confirmed starters but includes likely starters")
        logger.info("📊 Should work with FanDuel while reducing NS/PO risk")
        
        return hybrid_starters
        
    except Exception as e:
        logger.error(f"❌ Hybrid starter filter error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_hybrid_starter_slate()
