#!/usr/bin/env python3
"""
🔄 LINEUP REFRESH SYSTEM
Quick update for new fd_slate_today.csv with batting orders/lineups
No historical data pull needed - just weather and projections refresh
"""

import pandas as pd
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_slate_updates():
    """Check what's new in the slate file"""
    logger.info("🔍 CHECKING SLATE UPDATES...")
    
    try:
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        
        # Check for batting order info
        has_batting_order = 'Batting Order' in df.columns and df['Batting Order'].notna().sum() > 0
        
        # Check for confirmed lineups
        confirmed_count = len(df[df.get('Probable Pitcher', '') == 'Yes']) if 'Probable Pitcher' in df.columns else 0
        
        # Check IL players
        il_count = len(df[df['Injury Indicator'] == 'IL']) if 'Injury Indicator' in df.columns else 0
        
        logger.info(f"📊 SLATE ANALYSIS:")
        logger.info(f"   Total players: {len(df)}")
        logger.info(f"   Batting orders available: {has_batting_order}")
        logger.info(f"   Confirmed starters: {confirmed_count}")
        logger.info(f"   IL players to remove: {il_count}")
        
        return {
            'total_players': len(df),
            'has_batting_order': has_batting_order,
            'confirmed_count': confirmed_count,
            'il_count': il_count,
            'slate_df': df
        }
        
    except Exception as e:
        logger.error(f"❌ Error reading slate: {e}")
        return None

def update_weather_data():
    """Update weather data for today's games"""
    logger.info("🌤️  UPDATING WEATHER DATA...")
    
    try:
        # Try different weather update methods
        weather_scripts = [
            'get_weather_today.py',
            'weather_enhanced_system.py',
            '6. get_weather_data.py'
        ]
        
        weather_updated = False
        for script in weather_scripts:
            if os.path.exists(script):
                logger.info(f"   Running {script}...")
                os.system(f'python "{script}"')
                weather_updated = True
                break
        
        if not weather_updated:
            logger.warning("⚠️  No weather update script found")
            
        # Check if weather data exists
        weather_files = ['../data/weather_today.csv', 'weather_today.csv']
        weather_available = any(os.path.exists(f) for f in weather_files)
        
        if weather_available:
            logger.info("✅ Weather data available")
        else:
            logger.warning("⚠️  No weather data found")
            
        return weather_available
        
    except Exception as e:
        logger.error(f"❌ Weather update error: {e}")
        return False

def rebuild_today_features():
    """Rebuild today's features with new lineup data"""
    logger.info("🏗️  REBUILDING TODAY'S FEATURES...")
    
    feature_scripts = [
        ('11. build_today_pitcher_features.py', 'Pitcher features'),
        ('build_today_hitter_features.py', 'Hitter features'),
        ('12. build_rolling_hitter_features.py', 'Rolling hitter features')
    ]
    
    updated_features = []
    
    for script, description in feature_scripts:
        if os.path.exists(script):
            logger.info(f"   Updating {description}...")
            try:
                os.system(f'python "{script}"')
                updated_features.append(description)
                logger.info(f"   ✅ {description} updated")
            except Exception as e:
                logger.error(f"   ❌ Error updating {description}: {e}")
        else:
            logger.warning(f"   ⚠️  {script} not found")
    
    return updated_features

def update_projections():
    """Update player projections with new data"""
    logger.info("🎯 UPDATING PROJECTIONS...")
    
    projection_scripts = [
        ('(23)project_base_hitter_scores.py', 'Base hitter scores'),
        ('(24)project_base_pitcher_scores.py', 'Base pitcher scores'),
        ('(26)project_hitter_scores.py', 'Final hitter scores'),
        ('(27)project_pitcher_scores.py', 'Final pitcher scores')
    ]
    
    updated_projections = []
    
    for script, description in projection_scripts:
        if os.path.exists(script):
            logger.info(f"   Updating {description}...")
            try:
                os.system(f'python "{script}"')
                updated_projections.append(description)
                logger.info(f"   ✅ {description} updated")
            except Exception as e:
                logger.error(f"   ❌ Error updating {description}: {e}")
        else:
            logger.warning(f"   ⚠️  {script} not found")
    
    return updated_projections

def update_confirmed_starters():
    """Update confirmed starters from Rotowire"""
    logger.info("🎯 UPDATING CONFIRMED STARTERS FROM ROTOWIRE...")
    
    try:
        if os.path.exists('DYNAMIC_CONFIRMED_STARTERS.py'):
            logger.info("   📡 Fetching latest lineup information from Rotowire...")
            os.system('python DYNAMIC_CONFIRMED_STARTERS.py')
            
            # Check if confirmed starters file was created
            confirmed_files = [
                '../data/fd_slate_confirmed_starters_only.csv',
                '../fd_current_slate/fd_slate_confirmed_starters_only.csv'
            ]
            
            for file_path in confirmed_files:
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    logger.info(f"✅ Confirmed starters updated: {len(df)} players confirmed")
                    return True
            
            logger.warning("⚠️  Confirmed starters file not found after update")
            return False
            
        else:
            logger.warning("⚠️  DYNAMIC_CONFIRMED_STARTERS.py not found")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error updating confirmed starters: {e}")
        return False

def create_healthy_slate(slate_df):
    """Create IL-free slate"""
    logger.info("🏥 CREATING HEALTHY-ONLY SLATE...")
    
    # Remove IL players
    healthy_df = slate_df[slate_df['Injury Indicator'] != 'IL'].copy()
    
    # Save healthy slate
    healthy_df.to_csv('../data/fd_slave_NO_IL_PLAYERS.csv', index=False)
    
    logger.info(f"✅ Healthy slate created:")
    logger.info(f"   Original: {len(slate_df)} players")
    logger.info(f"   Healthy: {len(healthy_df)} players")
    logger.info(f"   Removed: {len(slate_df) - len(healthy_df)} IL players")
    
    return healthy_df

def filter_only_confirmed_starters():
    """Filter to only confirmed starting players"""
    logger.info("🔒 FILTERING TO CONFIRMED STARTERS ONLY...")
    
    try:
        # Look for confirmed starters file
        confirmed_files = [
            '../data/fd_slate_confirmed_starters_only.csv',
            '../fd_current_slate/fd_slate_confirmed_starters_only.csv'
        ]
        
        confirmed_df = None
        for file_path in confirmed_files:
            if os.path.exists(file_path):
                confirmed_df = pd.read_csv(file_path)
                logger.info(f"📊 Loaded confirmed starters: {len(confirmed_df)} players")
                break
        
        if confirmed_df is None:
            logger.warning("⚠️  No confirmed starters file found - using healthy slate")
            return False
        
        # Also check batting order information
        batting_order_count = confirmed_df['Batting Order'].notna().sum() if 'Batting Order' in confirmed_df.columns else 0
        
        logger.info(f"✅ Confirmed starters analysis:")
        logger.info(f"   Total confirmed: {len(confirmed_df)} players")
        logger.info(f"   With batting order: {batting_order_count} players")
        logger.info(f"   Pitchers: {len(confirmed_df[confirmed_df['Position'] == 'P'])} starters")
        
        # Save as the primary slate for lineup generation
        confirmed_df.to_csv('../data/fd_slate_CONFIRMED_ONLY.csv', index=False)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error filtering confirmed starters: {e}")
        return False

def regenerate_lineups():
    """Regenerate championship lineups and combine into single sheet"""
    logger.info("🏆 REGENERATING CHAMPIONSHIP LINEUPS...")
    
    try:
        if os.path.exists('MULTIPLE_CHAMPIONSHIP_BUILDER.py'):
            os.system('python MULTIPLE_CHAMPIONSHIP_BUILDER.py')
            logger.info("✅ Championship lineups regenerated")
            
            # Combine all individual lineup files into one sheet
            combine_lineups_to_single_sheet()
            
            return True
        else:
            logger.error("❌ MULTIPLE_CHAMPIONSHIP_BUILDER.py not found")
            return False
    except Exception as e:
        logger.error(f"❌ Error regenerating lineups: {e}")
        return False

def combine_lineups_to_single_sheet():
    """Combine all individual lineup files into a single FanDuel-ready sheet"""
    logger.info("📋 COMBINING LINEUPS INTO SINGLE SHEET...")
    
    try:
        import glob
        from datetime import datetime
        
        # Find the most recent lineup files
        lineup_pattern = '../data/CHAMPIONSHIP_LINEUP_*_*.csv'
        lineup_files = glob.glob(lineup_pattern)
        
        if not lineup_files:
            logger.warning("⚠️  No championship lineup files found")
            return False
        
        # Sort by modification time to get the newest batch
        lineup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Group files by timestamp (assuming they all have same timestamp for one batch)
        latest_timestamp = None
        latest_files = []
        
        for file in lineup_files:
            # Extract timestamp from filename (e.g., 20250804_171433)
            try:
                parts = file.split('_')
                timestamp = f"{parts[-2]}_{parts[-1].replace('.csv', '')}"
                if latest_timestamp is None:
                    latest_timestamp = timestamp
                    latest_files.append(file)
                elif timestamp == latest_timestamp:
                    latest_files.append(file)
                else:
                    break  # Different timestamp, stop here
            except:
                continue
        
        if not latest_files:
            logger.warning("⚠️  Could not identify latest lineup batch")
            return False
        
        logger.info(f"   📁 Found {len(latest_files)} lineup files from latest batch")
        
        # Read and combine all lineups
        combined_lineups = []
        
        for i, file_path in enumerate(latest_files, 1):
            try:
                df = pd.read_csv(file_path)
                if not df.empty:
                    # Update lineup ID to be sequential
                    df['Lineup_ID'] = f'LINEUP_{i}'
                    combined_lineups.append(df)
                    
                    # Extract lineup info for logging
                    filename = os.path.basename(file_path)
                    logger.info(f"   ✅ Added {filename}")
                    
            except Exception as e:
                logger.warning(f"   ⚠️  Could not read {file_path}: {e}")
                continue
        
        if not combined_lineups:
            logger.error("❌ No valid lineup data found")
            return False
        
        # Combine all lineups into single DataFrame
        final_df = pd.concat(combined_lineups, ignore_index=True)
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'../data/ALL_CHAMPIONSHIP_LINEUPS_{timestamp}.csv'
        
        # Save combined lineups
        final_df.to_csv(output_file, index=False)
        
        logger.info(f"")
        logger.info(f"✅ COMBINED LINEUP SHEET CREATED:")
        logger.info(f"   📊 Total lineups: {len(final_df)}")
        logger.info(f"   💾 File: {output_file}")
        logger.info(f"   🎯 Format: Ready for FanDuel multi-entry upload")
        logger.info(f"   📋 Lineup IDs: LINEUP_1 through LINEUP_{len(final_df)}")
        
        # Also create a copy in fd_current_slate for easy access
        easy_access_file = '../fd_current_slate/ALL_CHAMPIONSHIP_LINEUPS_READY.csv'
        final_df.to_csv(easy_access_file, index=False)
        logger.info(f"   📁 Quick access copy: {easy_access_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error combining lineups: {e}")
        import traceback
        traceback.print_exc()
        return False

def validate_lineups():
    """Validate the regenerated lineups"""
    logger.info("🔍 VALIDATING LINEUPS...")
    
    try:
        if os.path.exists('QUICK_LINEUP_CHECK.py'):
            os.system('python QUICK_LINEUP_CHECK.py')
            logger.info("✅ Lineup validation complete")
            return True
        else:
            logger.warning("⚠️  QUICK_LINEUP_CHECK.py not found")
            return False
    except Exception as e:
        logger.error(f"❌ Error validating lineups: {e}")
        return False

def main():
    """Main lineup refresh process"""
    
    logger.info("🔄 LINEUP REFRESH SYSTEM")
    logger.info("=" * 60)
    logger.info("Quick update for new slate with batting orders/lineups")
    logger.info("No historical data pull - just weather and projections")
    logger.info("")
    
    try:
        # Step 1: Check slate updates
        slate_info = check_slate_updates()
        if not slate_info:
            logger.error("❌ Could not read slate file")
            return
        
        # Step 2: Update weather
        weather_updated = update_weather_data()
        
        # Step 3: Rebuild features
        updated_features = rebuild_today_features()
        
        # Step 4: Update projections
        updated_projections = update_projections()
        
        # Step 5: Update confirmed starters from Rotowire
        confirmed_updated = update_confirmed_starters()
        
        # Step 6: Create healthy slate
        healthy_df = create_healthy_slate(slate_info['slate_df'])
        
        # Step 7: Filter to confirmed starters only
        confirmed_filtered = filter_only_confirmed_starters()
        
        # Step 8: Regenerate lineups
        lineups_updated = regenerate_lineups()
        
        # Step 9: Validate
        validation_complete = validate_lineups()
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎉 LINEUP REFRESH COMPLETE!")
        logger.info("=" * 60)
        
        logger.info("📊 SUMMARY:")
        logger.info(f"   🌤️  Weather updated: {'✅' if weather_updated else '⚠️'}")
        logger.info(f"   🏗️  Features updated: {len(updated_features)} scripts")
        logger.info(f"   🎯 Projections updated: {len(updated_projections)} scripts")
        logger.info(f"   📡 Confirmed starters: {'✅' if confirmed_updated else '⚠️'}")
        logger.info(f"   🏥 Healthy players: {len(healthy_df)}")
        logger.info(f"   🔒 Confirmed filtering: {'✅' if confirmed_filtered else '⚠️'}")
        logger.info(f"   🏆 Lineups regenerated: {'✅' if lineups_updated else '❌'}")
        logger.info(f"   🔍 Validation complete: {'✅' if validation_complete else '⚠️'}")
        
        if lineups_updated:
            logger.info("")
            logger.info("🚀 NEXT STEPS:")
            logger.info("1. Review the combined championship lineups file")
            logger.info("2. Check for any last-minute injury news")
            logger.info("3. Upload the single file to FanDuel (supports multi-entry)")
            logger.info("4. Monitor weather/lineup changes until lock")
            logger.info("")
            logger.info("📁 FILES READY:")
            logger.info("   • ALL_CHAMPIONSHIP_LINEUPS_READY.csv (in fd_current_slate)")
            logger.info("   • Individual files still available in data folder")
        else:
            logger.error("❌ Lineup generation failed - check logs above")
            
    except Exception as e:
        logger.error(f"❌ Lineup refresh error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
