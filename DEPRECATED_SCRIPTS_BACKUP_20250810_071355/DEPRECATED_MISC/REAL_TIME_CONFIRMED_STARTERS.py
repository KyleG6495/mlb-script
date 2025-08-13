#!/usr/bin/env python3
"""
🎯 REAL-TIME CONFIRMED STARTERS CHECKER
Updates confirmed starters list and generates safe lineups
Run this 30 minutes before first pitch for maximum safety
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import logging
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_todays_confirmed_starters():
    """Get today's confirmed starters - update this manually before running"""
    
    # 🚨 UPDATE THIS LIST DAILY based on RotoWire/Twitter/Beat reporters
    # Check around 3-4 PM ET when lineups are typically posted
    
    today = datetime.now().strftime("%Y-%m-%d")
    logger.info(f"📅 Getting confirmed starters for {today}")
    
    confirmed_starters = {
        "last_updated": datetime.now().isoformat(),
        "date": today,
        "confirmed_players": [
            
            # 🔥 EXAMPLE - UPDATE THESE WITH TODAY'S ACTUAL CONFIRMED STARTERS
            # Check RotoWire, Twitter @MLBLineups, team beat reporters
            
            # Game 1: Yankees @ Red Sox (example)
            {"name": "Aaron Judge", "team": "NYY", "position": "OF", "status": "CONFIRMED"},
            {"name": "Juan Soto", "team": "NYY", "position": "OF", "status": "CONFIRMED"}, 
            {"name": "Gleyber Torres", "team": "NYY", "position": "2B", "status": "CONFIRMED"},
            {"name": "Rafael Devers", "team": "BOS", "position": "3B", "status": "CONFIRMED"},
            {"name": "Trevor Story", "team": "BOS", "position": "SS", "status": "CONFIRMED"},
            {"name": "Jarren Duran", "team": "BOS", "position": "OF", "status": "CONFIRMED"},
            
            # Game 2: Dodgers @ Padres (example)
            {"name": "Shohei Ohtani", "team": "LAD", "position": "OF", "status": "CONFIRMED"},
            {"name": "Mookie Betts", "team": "LAD", "position": "2B", "status": "CONFIRMED"},
            {"name": "Freddie Freeman", "team": "LAD", "position": "1B", "status": "CONFIRMED"},
            {"name": "Fernando Tatis Jr.", "team": "SD", "position": "OF", "status": "CONFIRMED"},
            {"name": "Manny Machado", "team": "SD", "position": "3B", "status": "CONFIRMED"},
            {"name": "Luis Arraez", "team": "SD", "position": "1B", "status": "CONFIRMED"},
            
            # Game 3: Braves @ Cubs (example) 
            {"name": "Ronald Acuna Jr.", "team": "ATL", "position": "OF", "status": "CONFIRMED"},
            {"name": "Austin Riley", "team": "ATL", "position": "3B", "status": "CONFIRMED"},
            {"name": "Cody Bellinger", "team": "CHC", "position": "OF", "status": "CONFIRMED"},
            {"name": "Ian Happ", "team": "CHC", "position": "OF", "status": "CONFIRMED"},
            
            # PITCHERS - Usually confirmed 1-2 hours before first pitch
            {"name": "Gerrit Cole", "team": "NYY", "position": "P", "status": "PROBABLE"},  # Change to CONFIRMED when announced
            {"name": "Brayan Bello", "team": "BOS", "position": "P", "status": "PROBABLE"},
            {"name": "Tyler Glasnow", "team": "LAD", "position": "P", "status": "PROBABLE"},
            {"name": "Dylan Cease", "team": "SD", "position": "P", "status": "PROBABLE"},
            
            # 🚨 ADD MORE BASED ON TODAY'S ACTUAL LINEUPS
            # Check these sources:
            # - RotoWire.com/baseball/daily-lineups
            # - Twitter @MLBLineups  
            # - ESPN Starting Lineups
            # - Team beat reporters on Twitter
        ],
        
        # Players to AVOID (injured, not starting, etc.)
        "avoid_players": [
            {"name": "Shane Bieber", "reason": "IL - Elbow", "team": "CLE"},
            {"name": "Ronald Acuna Jr.", "reason": "IL - Calf", "team": "ATL"},
            {"name": "Chris Sale", "reason": "IL - Ribs", "team": "ATL"},
            {"name": "Shane McClanahan", "reason": "IL - Triceps", "team": "TB"},
            # Add more players to avoid based on injury reports
        ]
    }
    
    return confirmed_starters

def match_confirmed_with_fd_slate(confirmed_data, fd_df):
    """Match confirmed starters with FanDuel slate"""
    
    logger.info("🔍 MATCHING CONFIRMED STARTERS WITH FANDUEL SLATE...")
    
    confirmed_players = confirmed_data["confirmed_players"]
    avoid_players = {p["name"].lower() for p in confirmed_data["avoid_players"]}
    
    matched_players = []
    unmatched_confirmed = []
    
    for confirmed in confirmed_players:
        if confirmed["status"] != "CONFIRMED":
            continue  # Skip probable/questionable players
            
        confirmed_name = confirmed["name"].lower()
        
        # Skip players on avoid list
        if confirmed_name in avoid_players:
            logger.warning(f"⚠️  SKIPPING {confirmed['name']} - {confirmed.get('reason', 'On avoid list')}")
            continue
        
        # Find matching FD player
        matched = False
        for _, fd_player in fd_df.iterrows():
            fd_full = f"{fd_player['First Name']} {fd_player['Last Name']}".lower()
            fd_nickname = f"{fd_player['Nickname']}".lower()
            
            if (confirmed_name == fd_full or 
                confirmed_name == fd_nickname or
                confirmed["name"].split()[-1].lower() == fd_player['Last Name'].lower()):
                
                # Additional safety - check team if available
                if 'Team' in fd_player and confirmed.get('team'):
                    if fd_player['Team'] != confirmed['team']:
                        continue
                
                matched_players.append(fd_player)
                matched = True
                logger.info(f"✅ MATCHED: {confirmed['name']} -> {fd_player['Nickname']}")
                break
        
        if not matched:
            unmatched_confirmed.append(confirmed['name'])
    
    if unmatched_confirmed:
        logger.warning(f"⚠️  Could not match {len(unmatched_confirmed)} confirmed players:")
        for name in unmatched_confirmed:
            logger.warning(f"   - {name}")
    
    confirmed_df = pd.DataFrame(matched_players)
    
    logger.info(f"📊 MATCHING RESULTS:")
    logger.info(f"   ✅ Confirmed players found: {len(confirmed_df)}")
    logger.info(f"   📋 Pitchers: {len(confirmed_df[confirmed_df['Position'] == 'P'])}")
    logger.info(f"   🏏 Hitters: {len(confirmed_df[confirmed_df['Position'] != 'P'])}")
    
    return confirmed_df

def save_confirmed_slate(confirmed_df):
    """Save confirmed starters slate"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save for MULTIPLE_CHAMPIONSHIP_BUILDER
    main_file = "../data/fd_slate_confirmed_starters_only.csv"
    confirmed_df.to_csv(main_file, index=False)
    
    # Save timestamped backup
    backup_file = f"../data/fd_slate_confirmed_starters_{timestamp}.csv"
    confirmed_df.to_csv(backup_file, index=False)
    
    logger.info(f"💾 SAVED CONFIRMED STARTERS SLATE:")
    logger.info(f"   🎯 Main file: {main_file}")
    logger.info(f"   📁 Backup: {backup_file}")
    
    return main_file

def validate_confirmed_slate(confirmed_df):
    """Validate the confirmed starters slate"""
    
    logger.info("🔍 VALIDATING CONFIRMED STARTERS SLATE...")
    
    issues = []
    
    # Check positions
    pitchers = len(confirmed_df[confirmed_df['Position'] == 'P'])
    catchers = len(confirmed_df[confirmed_df['Position'] == 'C'])
    first_base = len(confirmed_df[confirmed_df['Position'] == '1B'])
    second_base = len(confirmed_df[confirmed_df['Position'] == '2B'])
    third_base = len(confirmed_df[confirmed_df['Position'] == '3B'])
    shortstop = len(confirmed_df[confirmed_df['Position'] == 'SS'])
    outfield = len(confirmed_df[confirmed_df['Position'] == 'OF'])
    
    logger.info(f"📊 POSITION BREAKDOWN:")
    logger.info(f"   P: {pitchers}, C: {catchers}, 1B: {first_base}, 2B: {second_base}")
    logger.info(f"   3B: {third_base}, SS: {shortstop}, OF: {outfield}")
    
    # Warnings for low counts
    if pitchers < 4:
        issues.append(f"⚠️  Only {pitchers} confirmed pitchers")
    if catchers < 2:
        issues.append(f"⚠️  Only {catchers} confirmed catchers")
    if outfield < 6:
        issues.append(f"⚠️  Only {outfield} confirmed outfielders")
    
    # Check for IL players
    il_players = confirmed_df[confirmed_df['Injury Indicator'] == 'IL']
    if len(il_players) > 0:
        issues.append(f"🚨 {len(il_players)} IL players still in slate!")
    
    if issues:
        logger.warning("🚨 VALIDATION ISSUES:")
        for issue in issues:
            logger.warning(f"   {issue}")
        return False
    else:
        logger.info("✅ VALIDATION PASSED - Slate looks good!")
        return True

def main():
    """Main function"""
    
    logger.info("🎯 REAL-TIME CONFIRMED STARTERS CHECKER")
    logger.info("=" * 60)
    
    try:
        # Step 1: Get confirmed starters list
        confirmed_data = get_todays_confirmed_starters()
        logger.info(f"📋 Loaded {len(confirmed_data['confirmed_players'])} confirmed players")
        
        # Step 2: Load FD slate
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📊 FanDuel slate: {len(fd_df)} players")
        
        # Step 3: Match confirmed with FD slate
        confirmed_df = match_confirmed_with_fd_slate(confirmed_data, fd_df)
        
        if len(confirmed_df) < 15:
            logger.error(f"❌ Only {len(confirmed_df)} confirmed players found - need more!")
            logger.error("🚨 Update the confirmed_starters list in this script!")
            return
        
        # Step 4: Remove IL players from confirmed list
        confirmed_healthy = confirmed_df[confirmed_df['Injury Indicator'] != 'IL'].copy()
        removed_il = len(confirmed_df) - len(confirmed_healthy)
        if removed_il > 0:
            logger.info(f"🏥 Removed {removed_il} IL players from confirmed list")
        
        # Step 5: Validate
        is_valid = validate_confirmed_slate(confirmed_healthy)
        
        # Step 6: Save
        slate_file = save_confirmed_slate(confirmed_healthy)
        
        # Summary
        logger.info("=" * 60)
        logger.info("🎉 CONFIRMED STARTERS PROCESSING COMPLETE!")
        logger.info(f"✅ Final confirmed + healthy players: {len(confirmed_healthy)}")
        logger.info(f"📁 Saved to: {slate_file}")
        
        if is_valid:
            logger.info("🚀 READY FOR LINEUP GENERATION!")
            logger.info("   Run: python MULTIPLE_CHAMPIONSHIP_BUILDER.py")
        else:
            logger.warning("⚠️  Validation issues found - review before using")
            
        # Show next steps
        logger.info("")
        logger.info("📋 NEXT STEPS:")
        logger.info("1. Review the confirmed players list above")
        logger.info("2. Run PRE_GAME_LINEUP_OPTIMIZER.bat")
        logger.info("3. Upload generated lineups to FanDuel")
        logger.info("4. Monitor for any last-minute lineup changes")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
