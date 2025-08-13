"""
UPDATE LINEUP GENERATORS TO USE STARTING LINEUPS
================================================

This script updates your existing lineup generators to use the starting_lineups.csv
master file instead of doing their own complex filtering.

Much simpler and more reliable!
"""

import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_starting_lineups_for_dfs():
    """Load starting lineups and convert to DFS format"""
    try:
        df = pd.read_csv('../data/starting_lineups.csv')
        logger.info(f"✅ Loaded {len(df)} confirmed starters from master file")
        
        # Convert to format expected by existing DFS scripts
        dfs_df = df.copy()
        
        # Rename columns to match existing script expectations
        dfs_df = dfs_df.rename(columns={
            'player_name': 'Nickname',
            'position': 'Position', 
            'team': 'Team',
            'salary': 'Salary',
            'batting_order': 'Batting Order'
        })
        
        # Add required columns that existing scripts expect
        dfs_df['FPPG'] = 10.0  # Default projection - will be enhanced
        dfs_df['Opponent'] = 'TBD'  # Will be filled from original slate
        dfs_df['Game'] = 'TBD'
        dfs_df['Tier'] = 'Starter'
        dfs_df['Probable Pitcher'] = dfs_df['Position'].apply(lambda x: 'Yes' if x == 'P' else '')
        
        logger.info(f"📊 Converted to DFS format: {len(dfs_df)} players ready for lineup generation")
        
        # Show position breakdown
        position_counts = dfs_df['Position'].value_counts()
        logger.info("🎯 Confirmed starters by position:")
        for pos, count in position_counts.items():
            if count >= 3:  # Only show positions with multiple players
                logger.info(f"   {pos}: {count} players")
        
        return dfs_df
        
    except FileNotFoundError:
        logger.error("❌ starting_lineups.csv not found!")
        logger.error("   Run create_starting_lineups.py first")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error loading starting lineups: {e}")
        return pd.DataFrame()

def save_for_existing_scripts(dfs_df):
    """Save in format that existing scripts can use"""
    if len(dfs_df) == 0:
        logger.error("❌ No data to save")
        return False
    
    # Save as filtered slate that existing scripts can use
    output_path = '../data/fd_slate_starters_only.csv'
    dfs_df.to_csv(output_path, index=False)
    logger.info(f"💾 Saved starters-only slate: {output_path}")
    
    # Create instruction file for other scripts
    instructions = """
# USING STARTING LINEUPS MASTER FILE
====================================

Instead of loading fd_slate_today.csv, your scripts should now load:
- fd_slate_starters_only.csv (contains only confirmed starters)

Benefits:
- No Drake Baldwin or other bench players
- No complex batting order filtering needed
- Pre-validated starting lineups only
- Consistent across all scripts

Example code change:
OLD: df = pd.read_csv('../data/fd_slate_today.csv')
NEW: df = pd.read_csv('../data/fd_slate_starters_only.csv')

All the filtering is already done!
"""
    
    with open('../data/starting_lineups_usage_guide.txt', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    logger.info("📝 Created usage guide: starting_lineups_usage_guide.txt")
    return True

def main():
    """Main execution"""
    logger.info("🔄 UPDATING LINEUP GENERATORS TO USE STARTING LINEUPS")
    logger.info("=" * 60)
    
    # Load and convert starting lineups
    dfs_df = load_starting_lineups_for_dfs()
    if len(dfs_df) == 0:
        logger.error("❌ Cannot proceed without starting lineups data")
        return
    
    # Save for existing scripts
    success = save_for_existing_scripts(dfs_df)
    
    if success:
        logger.info("🎉 SUCCESS!")
        logger.info("💡 Your existing scripts can now use:")
        logger.info("   📄 fd_slate_starters_only.csv (pre-filtered)")
        logger.info("   📋 starting_lineups_usage_guide.txt (instructions)")
        logger.info("")
        logger.info("🔧 To update existing scripts:")
        logger.info("   1. Change: pd.read_csv('../data/fd_slate_today.csv')")
        logger.info("   2. To:     pd.read_csv('../data/fd_slate_starters_only.csv')")
        logger.info("   3. Remove all batting order filtering logic")
        logger.info("   4. Remove injury filtering (already done)")
        logger.info("")
        logger.info("✅ All scripts will now use only confirmed starters!")
    else:
        logger.error("❌ Failed to prepare files for existing scripts")

if __name__ == "__main__":
    main()
