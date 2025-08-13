"""
UPDATED LINEUP GENERATOR - USES STARTING LINEUPS MASTER FILE
=============================================================

This replaces the complex filtering logic with a simple approach:
1. Load starting_lineups.csv (already validated)
2. Build lineups from confirmed starters only
3. No more guessing or complex validation

Much simpler and more reliable!
"""

import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_starting_lineups():
    """Load the master starting lineups file with FPPG data"""
    try:
        # Load the pipeline-ready file which has FPPG data
        df = pd.read_csv('../data/fd_slate_starters_only.csv')
        logger.info(f"✅ Loaded {len(df)} confirmed starters from pipeline file")
        
        # Convert to master file format for compatibility
        master_df = df.copy()
        master_df['player_name'] = df['First Name'] + ' ' + df['Last Name']
        master_df['position'] = df['Position']
        master_df['team'] = df['Team']
        master_df['salary'] = df['Salary']
        master_df['batting_order'] = df['Batting Order']
        master_df['FPPG'] = df['FPPG']
        
        # Show breakdown
        pitchers = len(master_df[master_df['position'] == 'P'])
        hitters = len(master_df[master_df['position'] != 'P'])
        logger.info(f"   ⚾ {pitchers} starting pitchers")
        logger.info(f"   🏏 {hitters} starting hitters")
        
        return master_df
    except FileNotFoundError:
        logger.error("❌ starting_lineups.csv not found!")
        logger.error("   Run create_starting_lineups.py first")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error loading starting lineups: {e}")
        return pd.DataFrame()

def build_lineup_from_starters(starters_df, strategy="balanced"):
    """Build lineup using only confirmed starters"""
    if len(starters_df) == 0:
        logger.error("❌ No starters available for lineup building")
        return {}
    
    lineup = {}
    remaining_salary = 35000
    
    # Required positions
    positions_needed = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for position in positions_needed:
        if position == 'OF':
            # Handle multiple OF positions - get available OF not already used
            available = starters_df[
                (starters_df['position'].str.contains('OF', na=False)) & 
                (~starters_df['player_name'].isin([p.get('name', '') for p in lineup.values()]))
            ].copy()
        else:
            # For other positions, check if they can play this position
            available = starters_df[
                (starters_df['position'].str.contains(position, na=False)) &
                (~starters_df['player_name'].isin([p.get('name', '') for p in lineup.values()]))
            ].copy()
        
        if len(available) == 0:
            logger.warning(f"⚠️ No {position} available in starting lineups")
            continue
        
        # Simple strategy: best value (FPPG/salary) but ensure reasonable salary
        if 'FPPG' in available.columns and 'salary' in available.columns:
            # Filter out players with salary too high for remaining budget
            affordable = available[available['salary'] <= remaining_salary - 2000]  # Leave buffer
            if len(affordable) == 0:
                affordable = available  # Use all if none affordable
            
            affordable['value'] = affordable['FPPG'] / (affordable['salary'] / 1000)
            selected = affordable.loc[affordable['value'].idxmax()]
        else:
            # Fallback: lowest salary
            selected = available.loc[available['salary'].idxmin()]
        
        lineup[position] = {
            'name': selected['player_name'],
            'position': position,
            'team': selected['team'],
            'salary': selected['salary'],
            'fppg': selected.get('FPPG', 0),
            'batting_order': selected.get('batting_order', None)
        }
        
        remaining_salary -= selected['salary']
    
    total_salary = 35000 - remaining_salary
    total_fppg = sum([p.get('fppg', 0) for p in lineup.values()])
    
    logger.info(f"🏆 Lineup built: ${total_salary:,} salary, {total_fppg:.1f} FPPG")
    
    return lineup

def save_lineup(lineup, filename_prefix="confirmed_starters_lineup"):
    """Save lineup in FanDuel format"""
    if not lineup:
        logger.error("❌ No lineup to save")
        return
    
    # Create FanDuel submission format
    lineup_data = []
    for pos, player in lineup.items():
        lineup_data.append({
            'Position': pos,
            'Player': player['name'],
            'Team': player['team'],
            'Salary': player['salary'],
            'FPPG': player['fppg'],
            'Batting_Order': player.get('batting_order', '')
        })
    
    df = pd.DataFrame(lineup_data)
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/{filename_prefix}_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    logger.info(f"💾 Saved lineup: {filename}")
    
    # Print lineup for review
    logger.info("🎯 CONFIRMED STARTERS LINEUP:")
    logger.info("=" * 50)
    for pos, player in lineup.items():
        batting = f" (bats {player.get('batting_order', 'N/A')})" if player.get('batting_order') else ""
        logger.info(f"{pos:3} | {player['name']:20} | {player['team']} | ${player['salary']:,} | {player['fppg']:.1f} FPPG{batting}")
    
    total_salary = sum([p['salary'] for p in lineup.values()])
    total_fppg = sum([p['fppg'] for p in lineup.values()])
    logger.info("=" * 50)
    logger.info(f"Total: ${total_salary:,} / $35,000 | {total_fppg:.1f} FPPG")

def main():
    """Main execution"""
    logger.info("🚀 BUILDING LINEUP FROM CONFIRMED STARTERS")
    logger.info("=" * 50)
    
    # Load confirmed starters
    starters_df = load_starting_lineups()
    if len(starters_df) == 0:
        logger.error("❌ Cannot build lineup without starting lineups data")
        logger.error("   1. Update fd_slate_today.csv with latest data")
        logger.error("   2. Run create_starting_lineups.py")
        return
    
    # Build lineup
    lineup = build_lineup_from_starters(starters_df)
    
    # Save lineup
    save_lineup(lineup)
    
    logger.info("✅ Lineup built using only confirmed starters!")
    logger.info("💡 No Drake Baldwin or other bench players included")

if __name__ == "__main__":
    main()
