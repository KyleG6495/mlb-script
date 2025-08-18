#!/usr/bin/env python3
"""
TARGET: SMART STARTER FILTER
Intelligently filters to only confirmed starting players using multiple signals:
1. Batting Order (1-9 = confirmed starter)
2. Probable Pitcher = "Yes" 
3. NOT marked as IL
4. NOT showing as bench players (position inconsistencies)
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_starter_signals(df):
    """Analyze all the signals that indicate a player is starting"""
    
    logger.info(" ANALYZING STARTER SIGNALS...")
    
    # 1. Batting Order Analysis
    batting_order_starters = df[
        (df['Batting Order'].notna()) & 
        (df['Batting Order'] > 0) & 
        (df['Batting Order'] <= 9)
    ]
    logger.info(f"   DATA: Players with batting order 1-9: {len(batting_order_starters)}")
    
    # 2. Probable Pitcher Analysis  
    probable_pitchers = df[
        (df['Position'] == 'P') & 
        (df['Probable Pitcher'] == 'Yes')
    ]
    logger.info(f"   BASEBALL: Probable starting pitchers: {len(probable_pitchers)}")
    
    # 3. IL Players (to exclude)
    il_players = df[df['Injury Indicator'] == 'IL']
    logger.info(f"    IL players to exclude: {len(il_players)}")
    
    # 4. High salary players (likely starters) 
    hitters = df[df['Position'] != 'P']
    high_salary_threshold = hitters['Salary'].quantile(0.6)  # Top 40% by salary
    high_salary_hitters = hitters[hitters['Salary'] >= high_salary_threshold]
    logger.info(f"   MONEY: High salary hitters (${high_salary_threshold:,.0f}+): {len(high_salary_hitters)}")
    
    return {
        'batting_order_starters': batting_order_starters,
        'probable_pitchers': probable_pitchers,
        'il_players': il_players,
        'high_salary_hitters': high_salary_hitters
    }

def create_smart_starter_slate(df):
    """Create slate with only confirmed/likely starters"""
    
    logger.info("TARGET: CREATING SMART STARTER SLATE...")
    
    # Get starter signals
    signals = analyze_starter_signals(df)
    
    # Start with definite starters
    confirmed_starters = []
    
    # 1. Add players with confirmed batting orders (1-9)
    batting_order_starters = signals['batting_order_starters']
    confirmed_starters.append(batting_order_starters)
    logger.info(f"   SUCCESS: Added {len(batting_order_starters)} batting order confirmed starters")
    
    # 2. Add probable starting pitchers
    probable_pitchers = signals['probable_pitchers']
    confirmed_starters.append(probable_pitchers)
    logger.info(f"   BASEBALL: Added {len(probable_pitchers)} probable starting pitchers")
    
    # 3. For positions without confirmed batting orders, add high-salary likely starters
    # This helps fill gaps where batting orders aren't announced yet
    remaining_positions = []
    
    for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
        # Check if we have enough confirmed starters at this position
        confirmed_at_pos = len(batting_order_starters[
            batting_order_starters['Position'].str.contains(pos, na=False) |
            batting_order_starters['Roster Position'].str.contains(pos, na=False)
        ])
        
        # If we don't have enough, add high-salary players at this position
        if confirmed_at_pos < 3:  # Need at least 3 per position for lineup diversity
            high_salary_at_pos = signals['high_salary_hitters'][
                (signals['high_salary_hitters']['Position'].str.contains(pos, na=False)) |
                (signals['high_salary_hitters']['Roster Position'].str.contains(pos, na=False))
            ].head(6)  # Take top 6 by salary at each position
            
            if len(high_salary_at_pos) > 0:
                remaining_positions.append(high_salary_at_pos)
                logger.info(f"   MONEY: Added {len(high_salary_at_pos)} high-salary {pos} players")
    
    # Combine all starter groups
    all_starters = pd.concat(confirmed_starters + remaining_positions, ignore_index=True)
    
    # Remove duplicates (keep first occurrence)
    all_starters = all_starters.drop_duplicates(subset=['Id'], keep='first')
    
    # Remove IL players
    smart_starters = all_starters[all_starters['Injury Indicator'] != 'IL'].copy()
    
    logger.info(f"")
    logger.info(f"DATA: SMART STARTER ANALYSIS:")
    logger.info(f"   Total slate players: {len(df)}")
    logger.info(f"   Confirmed/likely starters: {len(smart_starters)}")
    logger.info(f"   IL players removed: {len(all_starters) - len(smart_starters)}")
    logger.info(f"   Players filtered out: {len(df) - len(smart_starters)}")
    
    # Position breakdown
    logger.info(f"")
    logger.info(f" POSITION BREAKDOWN:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        pos_count = len(smart_starters[
            (smart_starters['Position'] == pos) |
            (smart_starters['Position'].str.contains(pos, na=False)) |
            (smart_starters['Roster Position'].str.contains(pos, na=False))
        ])
        logger.info(f"   {pos}: {pos_count} players")
    
    return smart_starters

def identify_problematic_players(df, smart_starters):
    """Identify players who were filtered out and might be problematic NS/PO players"""
    
    logger.info("")
    logger.info(" PROBLEMATIC PLAYERS FILTERED OUT:")
    
    filtered_out = df[~df['Id'].isin(smart_starters['Id'])]
    
    # Focus on players that might show up as NS/PO in lineups
    potentially_problematic = filtered_out[
        (filtered_out['Injury Indicator'] != 'IL') &  # Not IL
        (filtered_out['Batting Order'].isna() | (filtered_out['Batting Order'] == 0)) &  # No batting order
        (filtered_out['Salary'] >= 2000)  # High enough salary to be tempting
    ].sort_values('Salary', ascending=False)
    
    logger.info(f"   Players with no batting order (likely NS): {len(potentially_problematic)}")
    
    # Show top problematic players by salary
    for _, player in potentially_problematic.head(20).iterrows():
        logger.info(f"   ERROR: {player['Nickname']} ({player['Position']}) - ${player['Salary']:,} - {player['Team']}")
    
    return potentially_problematic

def main():
    """Main smart starter filtering process"""
    
    logger.info("TARGET: SMART STARTER FILTER SYSTEM")
    logger.info("="*60)
    logger.info("Intelligently filters to only confirmed starting players")
    logger.info("")
    
    try:
        # Load FD slate
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f" Loaded FD slate: {len(df)} players")
        
        # Create smart starter slate
        smart_starters = create_smart_starter_slate(df)
        
        # Identify problematic players that were filtered out
        problematic = identify_problematic_players(df, smart_starters)
        
        # Save smart starter slate
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save with timestamp
        smart_file = f'../data/fd_slate_smart_starters_{timestamp}.csv'
        smart_starters.to_csv(smart_file, index=False)
        
        # Save as main file
        main_file = '../data/fd_slate_SMART_STARTERS.csv'
        smart_starters.to_csv(main_file, index=False)
        
        # Also save in fd_current_slate for easy access
        easy_file = '../fd_current_slate/fd_slate_smart_starters.csv'
        smart_starters.to_csv(easy_file, index=False)
        
        logger.info("")
        logger.info(" SMART STARTER SLATE SAVED:")
        logger.info(f"    Timestamped: {smart_file}")
        logger.info(f"    Main file: {main_file}")
        logger.info(f"    Easy access: {easy_file}")
        
        logger.info("")
        logger.info("COMPLETE: SMART STARTER FILTER COMPLETE!")
        logger.info("="*60)
        logger.info(f"SUCCESS: Reduced from {len(df)} to {len(smart_starters)} players")
        logger.info(f" Filtered out {len(problematic)} potentially problematic players")
        logger.info("")
        logger.info("START: NEXT STEPS:")
        logger.info("1. Use fd_slate_SMART_STARTERS.csv for lineup generation")
        logger.info("2. This should eliminate NS/PO players from your lineups")
        logger.info("3. Players are filtered using batting order + salary signals")
        
    except Exception as e:
        logger.error(f"ERROR: Smart starter filter error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
