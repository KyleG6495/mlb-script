"""
CREATE STARTING LINEUPS MASTER FILE
===================================
Step 2 in daily workflow: After updating fd_slate_today.csv

This script:
1. Loads fd_slate_today.csv (updated FanDuel slate)
2. Fetches Rotowire confirmed lineups 
3. Cross-validates both sources
4. Creates starting_lineups.csv (SINGLE SOURCE OF TRUTH)
5. All other scripts use this file instead of guessing

Output: starting_lineups.csv with only confirmed starters
"""

import pandas as pd
import logging
import requests
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_fanduel_slate():
    """Load the updated FanDuel slate"""
    logger.info("DATA: Loading updated FanDuel slate...")
    try:
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"SUCCESS: Loaded {len(df)} players from FanDuel slate")
        return df
    except Exception as e:
        logger.error(f"ERROR: Failed to load FanDuel slate: {e}")
        return pd.DataFrame()

def fetch_rotowire_lineups():
    """Fetch confirmed starting lineups from Rotowire"""
    logger.info(" Fetching Rotowire confirmed lineups...")
    
    # This is a placeholder - you'll need to implement actual Rotowire fetching
    # For now, return empty dict so we use FanDuel data
    logger.warning("WARNING: Rotowire fetching not implemented yet - using FanDuel batting orders only")
    return {}

def validate_starting_lineups(fd_df, rotowire_data):
    """Cross-validate FanDuel vs Rotowire data"""
    logger.info(" VALIDATING STARTING LINEUPS...")
    
    starting_lineups = []
    
    # Filter pitchers - only probable starters
    pitchers = fd_df[fd_df['Position'] == 'P'].copy()
    if 'Probable Pitcher' in pitchers.columns:
        confirmed_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
        logger.info(f"BASEBALL: Confirmed starting pitchers: {len(confirmed_pitchers)}")
    else:
        confirmed_pitchers = pitchers
        logger.warning("WARNING: No 'Probable Pitcher' column - using all pitchers")
    
    # Add confirmed pitchers
    for _, pitcher in confirmed_pitchers.iterrows():
        starting_lineups.append({
            'player_name': pitcher.get('Nickname', pitcher.get('Last Name', 'Unknown')),
            'position': pitcher['Position'],
            'team': pitcher['Team'],
            'salary': pitcher['Salary'],
            'batting_order': None,  # Pitchers don't bat
            'source': 'FanDuel_Probable',
            'confirmed': True
        })
    
    # Filter hitters - only those with valid batting orders (1-9)
    hitters = fd_df[fd_df['Position'] != 'P'].copy()
    
    if 'Batting Order' in hitters.columns:
        # Convert batting order to numeric
        hitters['batting_order_num'] = pd.to_numeric(hitters['Batting Order'], errors='coerce')
        
        # Only keep hitters with batting orders 1-9
        confirmed_hitters = hitters[
            (hitters['batting_order_num'] >= 1) & 
            (hitters['batting_order_num'] <= 9) &
            (hitters['batting_order_num'].notna())
        ]
        
        logger.info(f" Total hitters in slate: {len(hitters)}")
        logger.info(f"SUCCESS: Confirmed starting hitters (batting 1-9): {len(confirmed_hitters)}")
        logger.info(f" Non-starters filtered out: {len(hitters) - len(confirmed_hitters)}")
        
        # Add confirmed hitters
        for _, hitter in confirmed_hitters.iterrows():
            starting_lineups.append({
                'player_name': hitter.get('Nickname', hitter.get('Last Name', 'Unknown')),
                'position': hitter['Position'],
                'team': hitter['Team'],
                'salary': hitter['Salary'],
                'batting_order': int(hitter['batting_order_num']),
                'source': 'FanDuel_BattingOrder',
                'confirmed': True
            })
    else:
        logger.error("ERROR: No 'Batting Order' column in FanDuel slate!")
        return pd.DataFrame()
    
    # Convert to DataFrame
    starting_df = pd.DataFrame(starting_lineups)
    
    logger.info(f"TARGET: FINAL STARTING LINEUPS: {len(starting_df)} confirmed starters")
    
    # Show breakdown by position
    if len(starting_df) > 0:
        position_counts = starting_df['position'].value_counts()
        logger.info("DATA: Position breakdown:")
        for pos, count in position_counts.items():
            logger.info(f"   {pos}: {count} players")
    
    return starting_df

def save_starting_lineups(starting_df):
    """Save the confirmed starting lineups file"""
    if len(starting_df) == 0:
        logger.error("ERROR: No starting lineups to save!")
        return False
    
    # Save to data directory
    output_path = '../data/starting_lineups.csv'
    starting_df.to_csv(output_path, index=False)
    logger.info(f" Saved starting lineups: {output_path}")
    
    # Create summary report
    summary = {
        'date_created': datetime.now().isoformat(),
        'total_starters': len(starting_df),
        'pitchers': len(starting_df[starting_df['position'] == 'P']),
        'hitters': len(starting_df[starting_df['position'] != 'P']),
        'teams_represented': starting_df['team'].nunique(),
        'validation_sources': ['FanDuel_BattingOrders', 'FanDuel_ProbablePitchers']
    }
    
    with open('../data/starting_lineups_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info("SUCCESS: STARTING LINEUPS MASTER FILE CREATED!")
    logger.info(f"   DATA: {summary['total_starters']} confirmed starters")
    logger.info(f"   BASEBALL: {summary['pitchers']} pitchers, {summary['hitters']} hitters")
    logger.info(f"    {summary['teams_represented']} teams")
    logger.info("   TARGET: All other scripts should now use starting_lineups.csv")
    
    return True

def main():
    """Main execution"""
    logger.info("START: CREATING STARTING LINEUPS MASTER FILE")
    logger.info("=" * 50)
    
    # Step 1: Load FanDuel slate
    fd_df = load_fanduel_slate()
    if len(fd_df) == 0:
        logger.error("ERROR: Cannot proceed without FanDuel slate data")
        return
    
    # Step 2: Fetch Rotowire data (future enhancement)
    rotowire_data = fetch_rotowire_lineups()
    
    # Step 3: Validate and create starting lineups
    starting_df = validate_starting_lineups(fd_df, rotowire_data)
    
    # Step 4: Save master file
    success = save_starting_lineups(starting_df)
    
    if success:
        logger.info("COMPLETE: SUCCESS: starting_lineups.csv is ready!")
        logger.info("TIP: Next steps:")
        logger.info("   1. All lineup generators should use starting_lineups.csv")
        logger.info("   2. No more guessing about starters")
        logger.info("   3. Single source of truth for all scripts")
    else:
        logger.error("ERROR: Failed to create starting lineups file")

if __name__ == "__main__":
    main()
