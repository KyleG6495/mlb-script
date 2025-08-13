#!/usr/bin/env python3
"""
CREATE PIPELINE-READY STARTERS FILE
===================================
Creates fd_slate_starters_only.csv that maintains the exact FanDuel format
but contains only confirmed starters. This ensures compatibility with ALL
existing data pipeline scripts.
"""

import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_pipeline_ready_starters():
    """Create starters file with full FanDuel column structure"""
    
    try:
        # Load the starting lineups master file
        starters_df = pd.read_csv('../data/starting_lineups.csv')
        logger.info(f"📊 Loaded {len(starters_df)} confirmed starters")
        
        # Load the original FanDuel slate to get full column structure
        original_slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📥 Loaded original slate with {len(original_slate)} players")
        
        # Match starters with original slate data using player names
        # Extract first and last names from player_name in starters
        starters_df['First Name'] = starters_df['player_name'].str.split().str[0]
        starters_df['Last Name'] = starters_df['player_name'].str.split().str[-1]
        
        # Create lookup keys for matching
        starters_df['lookup_key'] = (starters_df['First Name'] + " " + starters_df['Last Name']).str.lower()
        original_slate['lookup_key'] = (original_slate['First Name'] + " " + original_slate['Last Name']).str.lower()
        
        # Match starters with original slate data
        matched_starters = []
        unmatched_starters = []
        
        for _, starter in starters_df.iterrows():
            # Try exact name match first
            matches = original_slate[original_slate['lookup_key'] == starter['lookup_key']]
            
            if len(matches) > 0:
                # Use the first match (in case of duplicates)
                matched_starters.append(matches.iloc[0])
            else:
                # Try nickname match
                nickname_matches = original_slate[original_slate['Nickname'].str.lower() == starter['player_name'].lower()]
                if len(nickname_matches) > 0:
                    matched_starters.append(nickname_matches.iloc[0])
                else:
                    unmatched_starters.append(starter['player_name'])
        
        if unmatched_starters:
            logger.warning(f"⚠️ Could not match {len(unmatched_starters)} starters:")
            for name in unmatched_starters[:5]:  # Show first 5
                logger.warning(f"   - {name}")
        
        if not matched_starters:
            logger.error("❌ No starters could be matched with original slate!")
            return False
        
        # Convert to DataFrame with original FanDuel structure
        pipeline_ready_df = pd.DataFrame(matched_starters)
        
        # Ensure we have all required columns
        required_columns = [
            'Id', 'Position', 'First Name', 'Nickname', 'Last Name', 'FPPG', 'Played',
            'Salary', 'Game', 'Team', 'Opponent', 'Injury Indicator', 'Injury Details',
            'Tier', 'Probable Pitcher', 'Batting Order', 'Roster Position'
        ]
        
        for col in required_columns:
            if col not in pipeline_ready_df.columns:
                pipeline_ready_df[col] = ''
        
        # Reorder columns to match original
        pipeline_ready_df = pipeline_ready_df[required_columns]
        
        # Save the pipeline-ready file
        output_file = '../data/fd_slate_starters_only.csv'
        pipeline_ready_df.to_csv(output_file, index=False)
        
        logger.info(f"✅ Created pipeline-ready starters file: {output_file}")
        logger.info(f"📊 Contains {len(pipeline_ready_df)} confirmed starters with full FanDuel structure")
        
        # Show position breakdown
        position_counts = pipeline_ready_df['Position'].value_counts()
        logger.info("🎯 Pipeline-ready starters by position:")
        for pos, count in position_counts.items():
            logger.info(f"   {pos}: {count} players")
        
        return True
        
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        logger.error("   Make sure starting_lineups.csv and fd_slate_today.csv exist")
        return False
    except Exception as e:
        logger.error(f"❌ Error creating pipeline-ready file: {e}")
        return False

def main():
    logger.info("🔄 CREATING PIPELINE-READY STARTERS FILE")
    logger.info("=" * 50)
    
    if create_pipeline_ready_starters():
        logger.info("")
        logger.info("🎉 SUCCESS!")
        logger.info("✅ Data pipeline scripts can now use fd_slate_starters_only.csv")
        logger.info("✅ File maintains full FanDuel column structure")
        logger.info("✅ Only contains confirmed starters (no bench players)")
        logger.info("")
        logger.info("Benefits:")
        logger.info("• Historical data pulled only for confirmed starters")
        logger.info("• Weather/park factors only for starters")
        logger.info("• Faster pipeline execution")
        logger.info("• No more Drake Baldwin-type issues")
    else:
        logger.error("❌ Failed to create pipeline-ready file")

if __name__ == "__main__":
    main()
