#!/usr/bin/env python3
"""
CREATE PIPELINE-READY STARTERS FILE
===================================
Creates fd_slate_starters_only.csv using Rotowire confirmed lineups
matched against the FanDuel slate. This ensures we get complete 9-man
lineups for all teams, not just partial batting orders.
"""

import pandas as pd
import logging
from datetime import datetime
import subprocess
import json
import re

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_and_parse_rotowire():
    """Fetch fresh Rotowire lineup data"""
    logger.info("🌐 Fetching fresh Rotowire lineup data...")
    
    try:
        # Run the Rotowire fetcher
        result = subprocess.run(['python', 'fetch_rotowire_lineups.py'], 
                              capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            logger.warning("⚠️ Rotowire fetch failed, will use FD salary-based lineups")
            return {}, {}
        
        # Load lineup data if available
        lineup_data = {}
        pitcher_data = {}
        
        try:
            with open('temp_lineup_data.json', 'r') as f:
                lineup_data = json.load(f)
            logger.info(f"📊 Loaded {len(lineup_data)} batting order assignments from Rotowire")
        except:
            logger.info("📊 No batting order data from Rotowire")
        
        try:
            with open('temp_pitcher_data.json', 'r') as f:
                pitcher_data = json.load(f)
            logger.info(f"⚾ Loaded {len(pitcher_data)} starting pitchers from Rotowire")
        except:
            logger.info("⚾ No pitcher data from Rotowire")
        
        return lineup_data, pitcher_data
        
    except Exception as e:
        logger.warning(f"⚠️ Error fetching Rotowire data: {e}")
        return {}, {}

def create_complete_lineups(fd_df, lineup_data, pitcher_data):
    """Create complete starting lineups prioritizing Rotowire confirmed lineups"""
    logger.info("🔧 Creating complete starting lineups...")
    
    slate_teams = sorted(fd_df['Team'].unique())
    all_starters = []
    
    logger.info(f"📋 Processing {len(slate_teams)} teams: {slate_teams}")
    
    # Let's try to get better Rotowire data by using a more comprehensive approach
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        import time
        
        logger.info("🌐 Attempting to fetch complete Rotowire lineups...")
        
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get("https://www.rotowire.com/baseball/daily-lineups.php")
            
            # Wait for content to load
            wait = WebDriverWait(driver, 10)
            
            # Look for confirmed lineups
            lineup_sections = driver.find_elements(By.XPATH, "//div[contains(text(), 'Confirmed Lineup') or contains(text(), 'Probable Lineup')]")
            
            enhanced_lineup_data = {}
            
            for section in lineup_sections:
                # Get the parent container that should have the full lineup
                parent = section.find_element(By.XPATH, "./ancestor::div[contains(@class, 'lineup') or contains(@class, 'game')]")
                lineup_text = parent.text
                
                # Parse team names and players
                lines = lineup_text.split('\n')
                current_team = None
                batting_order = 1
                
                for line in lines:
                    line = line.strip()
                    
                    # Check if this is a team abbreviation
                    if re.match(r'^[A-Z]{3}$', line):
                        current_team = line
                        batting_order = 1
                        continue
                    
                    # Check if this looks like a player entry
                    if current_team and len(line) > 3 and not any(word in line.lower() for word in ['confirmed', 'probable', 'lineup', 'vs', '@']):
                        # Clean player name
                        clean_name = re.sub(r'[^a-zA-Z\s.]', '', line).strip()
                        if clean_name and len(clean_name.split()) >= 2:
                            enhanced_lineup_data[f"{current_team}_{clean_name}"] = batting_order
                            batting_order += 1
                            
                            if batting_order > 9:  # Reset for next team
                                batting_order = 1
            
            driver.quit()
            
            if enhanced_lineup_data:
                logger.info(f"🎯 Enhanced Rotowire data: {len(enhanced_lineup_data)} confirmed starters")
                lineup_data.update(enhanced_lineup_data)
            
        except Exception as e:
            logger.warning(f"⚠️ Selenium approach failed: {e}")
            
    except ImportError:
        logger.info("📊 Selenium not available, using existing Rotowire data")
    
    for team in slate_teams:
        logger.info(f"\n🏟️ Processing {team}...")
        
        # Get all players for this team
        team_players = fd_df[fd_df['Team'] == team].copy()
        pitchers = team_players[team_players['Position'] == 'P']
        hitters = team_players[team_players['Position'] != 'P']
        
        # 1. Add starting pitcher (keep existing logic)
        starting_pitcher = None
        
        # First try: Probable pitcher from FD
        probable_pitchers = pitchers[pitchers.get('Probable Pitcher', '') == 'Yes']
        if len(probable_pitchers) > 0:
            starting_pitcher = probable_pitchers.iloc[0]
            logger.info(f"   ⚾ Starting pitcher: {starting_pitcher['Nickname']} (FD probable)")
        
        # Second try: Match with Rotowire pitcher data
        elif pitcher_data:
            best_match = None
            best_score = 0
            
            for _, pitcher in pitchers.iterrows():
                pitcher_name = pitcher.get('Nickname', pitcher.get('Last Name', ''))
                
                for rotowire_name, rotowire_info in pitcher_data.items():
                    if pitcher_name.lower() in rotowire_name.lower() or rotowire_name.lower() in pitcher_name.lower():
                        score = 10 - float(rotowire_info.get('era', 5.0))
                        if score > best_score:
                            best_score = score
                            best_match = pitcher
            
            if best_match is not None:
                starting_pitcher = best_match
                logger.info(f"   ⚾ Starting pitcher: {starting_pitcher['Nickname']} (Rotowire match)")
        
        # Third try: Highest salary pitcher
        if starting_pitcher is None:
            starting_pitcher = pitchers.loc[pitchers['Salary'].idxmax()]
            logger.info(f"   ⚾ Starting pitcher: {starting_pitcher['Nickname']} (highest salary)")
        
        all_starters.append(starting_pitcher)
        
        # 2. Add starting hitters - PRIORITIZE ROTOWIRE DATA
        confirmed_hitters = []
        
        # First: Get ALL Rotowire confirmed players for this team
        rotowire_hitters = []
        if lineup_data:
            for key, batting_order in lineup_data.items():
                if key.startswith(f"{team}_"):
                    player_name = key.replace(f"{team}_", "")
                    
                    # Try to match with FD hitters using multiple matching strategies
                    best_match = None
                    best_score = 0
                    
                    for _, hitter in hitters.iterrows():
                        hitter_full_name = f"{hitter['First Name']} {hitter['Nickname']}"
                        
                        # Score the match
                        score = 0
                        
                        # Exact name match
                        if player_name.lower() == hitter_full_name.lower():
                            score = 100
                        # Last name match
                        elif player_name.split()[-1].lower() == hitter['Nickname'].lower():
                            score = 80
                        # Partial name match
                        elif any(part.lower() in hitter_full_name.lower() for part in player_name.split()):
                            score = 60
                        # Nickname match
                        elif player_name.lower() in hitter['Nickname'].lower():
                            score = 50
                        
                        if score > best_score:
                            best_score = score
                            best_match = hitter
                    
                    if best_match is not None and best_score >= 50:  # Minimum confidence threshold
                        hitter_copy = best_match.copy()
                        hitter_copy['Batting Order'] = batting_order
                        rotowire_hitters.append((batting_order, hitter_copy))
                        logger.info(f"   ✅ Confirmed: {batting_order}. {hitter_copy['Nickname']} (Rotowire)")
        
        # Sort Rotowire hitters by batting order
        rotowire_hitters.sort(key=lambda x: x[0])
        confirmed_hitters = [hitter for _, hitter in rotowire_hitters]
        
        logger.info(f"   � {len(confirmed_hitters)}/9 hitters confirmed from Rotowire")
        
        # Second: Fill remaining spots with healthy, high-salary players
        used_player_ids = set(h['Id'] for h in confirmed_hitters)
        remaining_hitters = hitters[~hitters['Id'].isin(used_player_ids)].copy()
        
        # Filter out injured players
        healthy_hitters = remaining_hitters[
            (remaining_hitters['Injury Indicator'].isna()) | 
            (remaining_hitters['Injury Indicator'] == '') |
            (remaining_hitters['Injury Indicator'] == 'DTD')
        ].sort_values('Salary', ascending=False)
        
        spots_needed = 9 - len(confirmed_hitters)
        if spots_needed > 0:
            available_healthy = len(healthy_hitters)
            players_to_add = min(spots_needed, available_healthy)
            
            for i, (_, hitter) in enumerate(healthy_hitters.head(players_to_add).iterrows()):
                hitter_copy = hitter.copy()
                hitter_copy['Batting Order'] = len(confirmed_hitters) + i + 1
                confirmed_hitters.append(hitter_copy)
                logger.info(f"   💰 Salary-based: {len(confirmed_hitters)}. {hitter_copy['Nickname']} (${hitter_copy['Salary']})")
            
            # If still need players, warn and use IL players as last resort
            if players_to_add < spots_needed:
                logger.warning(f"   ⚠️ {team}: Only {available_healthy} healthy hitters available, need {spots_needed}")
                il_hitters = remaining_hitters[
                    remaining_hitters['Injury Indicator'] == 'IL'
                ].sort_values('Salary', ascending=False)
                
                remaining_spots = spots_needed - players_to_add
                for i, (_, hitter) in enumerate(il_hitters.head(remaining_spots).iterrows()):
                    hitter_copy = hitter.copy()
                    hitter_copy['Batting Order'] = len(confirmed_hitters) + i + 1
                    confirmed_hitters.append(hitter_copy)
                    logger.warning(f"   🏥 IL fallback: {len(confirmed_hitters)}. {hitter_copy['Nickname']} ({hitter_copy['Injury Details']})")
        
        # Take only top 9 hitters
        confirmed_hitters = confirmed_hitters[:9]
        all_starters.extend(confirmed_hitters)
        
        # Count sources
        rotowire_count = len([h for h in confirmed_hitters if h.get('Batting Order', 0) <= len(rotowire_hitters)])
        salary_count = len(confirmed_hitters) - rotowire_count
        
        logger.info(f"   ✅ {team}: 1P + {len(confirmed_hitters)}H = 10 starters ({rotowire_count} Rotowire + {salary_count} salary-based)")
    
    return pd.DataFrame(all_starters)

def create_pipeline_ready_starters():
    """Create starters file with complete lineups using Rotowire + FanDuel"""
    
    try:
        # Load the original FanDuel slate
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📋 Loaded FanDuel slate with {len(fd_df)} players from {len(fd_df['Team'].unique())} teams")
        
        # Fetch fresh Rotowire data
        lineup_data, pitcher_data = fetch_and_parse_rotowire()
        
        # Create complete starting lineups
        pipeline_ready_df = create_complete_lineups(fd_df, lineup_data, pitcher_data)
        
        logger.info(f"🎯 Created complete lineups: {len(pipeline_ready_df)} total starters")
        
        # Show team distribution
        team_counts = pipeline_ready_df['Team'].value_counts().sort_index()
        logger.info("📊 Starters per team:")
        for team, count in team_counts.items():
            logger.info(f"   {team}: {count} players")
        
        # Save the pipeline-ready file
        output_file = '../data/fd_slate_starters_only.csv'
        pipeline_ready_df.to_csv(output_file, index=False)
        
        logger.info(f"💾 Saved pipeline-ready starters: {output_file}")
        
        # Clean up temp files
        import os
        for temp_file in ['temp_lineup_data.json', 'temp_pitcher_data.json']:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating pipeline-ready file: {e}")
        return False

if __name__ == "__main__":
    print("🚀 CREATING PIPELINE-READY STARTERS FILE")
    print("=" * 50)
    print("Strategy: Rotowire confirmed lineups + FanDuel slate matching")
    print("Goal: Complete 9-man lineups for all teams")
    print()
    
    success = create_pipeline_ready_starters()
    
    if success:
        print()
        print("✅ PIPELINE-READY STARTERS FILE CREATED SUCCESSFULLY!")
        print("📁 File: ../data/fd_slate_starters_only.csv")
        print("🎯 Contains complete lineups for all teams in today's slate")
        print("🔄 Ready for data pipeline processing")
    else:
        print()
        print("❌ FAILED TO CREATE PIPELINE-READY STARTERS FILE")
        print("🔧 Check logs above for error details")
        exit(1)
