#!/usr/bin/env python3
"""
 LINEUP VERIFICATION SYSTEM
Double-check that all players in smart lineups are confirmed starters
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_smart_lineups():
    """Verify all players in smart lineups are confirmed starters"""
    
    logger.info(" LINEUP VERIFICATION SYSTEM")
    logger.info("="*50)
    
    try:
        # Load smart lineups
        lineups = pd.read_csv('../fd_current_slate/SMART_CHAMPIONSHIP_LINEUPS.csv')
        logger.info(f" Loaded {len(lineups)} smart lineups")
        
        # Load original slate for comparison
        original_slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f" Loaded original slate: {len(original_slate)} players")
        
        # Load smart starter slate
        smart_starters = pd.read_csv('../data/fd_slate_SMART_STARTERS.csv')
        logger.info(f" Loaded smart starters: {len(smart_starters)} confirmed starters")
        
        # Extract all player names from lineups
        all_lineup_players = []
        positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF_2', 'OF_3', 'UTIL']
        
        for _, lineup in lineups.iterrows():
            lineup_players = []
            for pos in positions:
                player_str = lineup[pos]
                if pd.notna(player_str) and player_str.strip():
                    # Extract player name (before the parentheses)
                    player_name = player_str.split(' (')[0].strip()
                    team = player_str.split('(')[1].split(')')[0] if '(' in player_str else "Unknown"
                    lineup_players.append({
                        'name': player_name,
                        'team': team,
                        'position': pos,
                        'lineup': lineup['Lineup']
                    })
            all_lineup_players.extend(lineup_players)
        
        logger.info(f"DATA: Total player selections: {len(all_lineup_players)}")
        logger.info(f"DATA: Unique players used: {len(set(p['name'] for p in all_lineup_players))}")
        
        # Check each player against smart starters
        logger.info("")
        logger.info(" PLAYER VERIFICATION:")
        
        problematic_players = []
        verified_players = []
        
        for player in all_lineup_players:
            player_name = player['name']
            player_team = player['team']
            
            # Find in smart starters
            matches = smart_starters[
                (smart_starters['Nickname'].str.contains(player_name.split()[-1], na=False, case=False)) &
                (smart_starters['Team'] == player_team)
            ]
            
            if len(matches) > 0:
                match = matches.iloc[0]
                batting_order = match['Batting Order'] if pd.notna(match['Batting Order']) else 0
                probable_pitcher = match['Probable Pitcher'] if pd.notna(match['Probable Pitcher']) else ""
                
                verified_players.append({
                    'player': player,
                    'batting_order': batting_order,
                    'probable_pitcher': probable_pitcher,
                    'salary': match['Salary'],
                    'fppg': match['FPPG']
                })
                
                if match['Position'] == 'P':
                    status = f"Probable Pitcher: {probable_pitcher}"
                else:
                    status = f"Batting Order: {batting_order}"
                    
                logger.info(f"   SUCCESS: {player_name} ({player_team}) - {status}")
            else:
                problematic_players.append(player)
                logger.warning(f"   ERROR: {player_name} ({player_team}) - NOT FOUND in smart starters!")
        
        logger.info("")
        logger.info("DATA: VERIFICATION SUMMARY:")
        logger.info(f"   SUCCESS: Verified players: {len(verified_players)}")
        logger.info(f"   ERROR: Problematic players: {len(problematic_players)}")
        
        if len(problematic_players) == 0:
            logger.info("")
            logger.info("COMPLETE: VERIFICATION PASSED!")  
            logger.info("SUCCESS: ALL players in smart lineups are confirmed starters")
            logger.info(" NO NS/PO players found in lineups")
            logger.info(" SMART_CHAMPIONSHIP_LINEUPS.csv is SAFE to upload!")
        else:
            logger.error("")
            logger.error("ERROR: VERIFICATION FAILED!")
            for player in problematic_players:
                logger.error(f"   Problem: {player['name']} ({player['team']}) in {player['lineup']}")
        
        # Show batting order breakdown
        logger.info("")
        logger.info("DATA: BATTING ORDER BREAKDOWN:")
        hitters = [p for p in verified_players if p['player']['position'] != 'P']
        pitchers = [p for p in verified_players if p['player']['position'] == 'P']
        
        logger.info(f"   Pitchers (Probable=Yes): {len(pitchers)}")
        for order in range(1, 10):
            count = len([p for p in hitters if p['batting_order'] == order])
            if count > 0:
                logger.info(f"   Batting Order {order}: {count} players")
        
    except Exception as e:
        logger.error(f"ERROR: Verification error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_smart_lineups()
