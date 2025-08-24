#!/usr/bin/env python3
"""
CONFIRMED STARTERS BRIDGE
Creates the files your existing scripts expect, but with confirmed players only
This lets us use ALL your existing proven infrastructure!
"""

import pandas as pd
import shutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def bridge_confirmed_to_existing():
    """Bridge confirmed starters data to existing script expectations"""
    
    logger.info(" BRIDGING CONFIRMED STARTERS TO EXISTING SCRIPTS")
    logger.info("=" * 60)
    
    try:
        # Load confirmed hitter games
        confirmed_hitters = pd.read_csv('../data/confirmed_hitter_games.csv')
        logger.info(f"SUCCESS: Loaded {len(confirmed_hitters)} confirmed hitter games")
        
        # Save as the file your existing scripts expect
        # Add target_name column that existing scripts need
        confirmed_hitters['target_name'] = confirmed_hitters['player_name']
        confirmed_hitters.to_csv('../data/hitter_games.csv', index=False)
        logger.info("SUCCESS: Created hitter_games.csv for existing scripts")
        logger.info("SUCCESS: Added target_name column for compatibility")
        
        # Load confirmed starters slate for pitcher data
        confirmed_slate = pd.read_csv('../fd_current_slate/fd_slate_confirmed_starters_only.csv')
        pitchers = confirmed_slate[confirmed_slate['Position'] == 'P'].copy()
        logger.info(f"SUCCESS: Found {len(pitchers)} confirmed starting pitchers")
        
        # Create pitcher games in expected format
        pitcher_games = []
        for _, pitcher in pitchers.iterrows():
            game = pitcher['Game']
            team = pitcher['Team']
            
            if '@' in game:
                away_team, home_team = game.split('@')
                is_home = (team == home_team)
                opponent = home_team if team == away_team else away_team
            else:
                is_home = True
                opponent = 'TBD'
            
            pitcher_game = {
                'player_name': pitcher['Nickname'],
                'target_name': pitcher['Nickname'],  # Add for compatibility
                'team': team,
                'opponent': opponent,
                'home_away': 'Home' if is_home else 'Away',
                'game_date': datetime.now().strftime('%Y-%m-%d'),
                'position': pitcher['Position'],
                'salary': pitcher['Salary'],
                'fd_id': pitcher['Id'],
                'confirmed_starter': True,
                'game_string': game
            }
            
            pitcher_games.append(pitcher_game)
        
        if pitcher_games:
            pitcher_games_df = pd.DataFrame(pitcher_games)
            pitcher_games_df.to_csv('../data/pitcher_games.csv', index=False)
            logger.info("SUCCESS: Created pitcher_games.csv for existing scripts")
            logger.info(f"DATA: Pitcher games: {len(pitcher_games_df)}")
        
        logger.info("=" * 60)
        logger.info("COMPLETE: BRIDGE COMPLETE!")
        logger.info("TARGET: Your existing scripts can now process confirmed starters only")
        logger.info(" All the speed benefits of focused processing")
        logger.info(" All the reliability of your proven infrastructure")
        
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Bridge failed: {e}")
        return False

if __name__ == "__main__":
    bridge_confirmed_to_existing()
