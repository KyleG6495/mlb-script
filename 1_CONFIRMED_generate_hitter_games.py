#!/usr/bin/env python3
"""
CONFIRMED STARTERS HITTER GAMES GENERATOR
Only processes confirmed starting hitters from today's slate
Much faster than processing entire league!
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_confirmed_starters():
    """Load confirmed starters from the filtered slate"""
    try:
        confirmed_df = pd.read_csv('../fd_current_slate/fd_slate_confirmed_starters_only.csv')
        logger.info(f"SUCCESS: Loaded {len(confirmed_df)} confirmed starters")
        
        # Filter to hitters only
        hitters = confirmed_df[confirmed_df['Position'] != 'P'].copy()
        logger.info(f" Confirmed hitters: {len(hitters)}")
        
        return hitters
    except FileNotFoundError:
        logger.error("ERROR: Confirmed starters slate not found!")
        logger.error("TIP: Run DAILY_CONFIRMED_WORKFLOW.bat first")
        return None

def extract_hitter_names_from_confirmed(hitters_df):
    """Extract hitter names for processing"""
    
    hitter_names = []
    
    for _, hitter in hitters_df.iterrows():
        # Use the Nickname from FD slate as primary name
        name = hitter['Nickname']
        
        # Clean up name for processing
        clean_name = name.strip()
        
        hitter_info = {
            'fd_name': clean_name,
            'first_name': hitter['First Name'],
            'last_name': hitter['Last Name'],
            'team': hitter['Team'],
            'position': hitter['Position'],
            'salary': hitter['Salary'],
            'game': hitter['Game'],
            'fd_id': hitter['Id']
        }
        
        hitter_names.append(hitter_info)
        logger.info(f"INFO: Added: {clean_name} ({hitter['Team']}) - ${hitter['Salary']:,}")
    
    logger.info(f"SUCCESS: Extracted {len(hitter_names)} confirmed hitter names")
    return hitter_names

def generate_confirmed_hitter_games(hitter_names):
    """Generate games data for confirmed hitters only"""
    
    games_data = []
    
    for hitter in hitter_names:
        # Parse game information
        game = hitter['game']
        team = hitter['team']
        
        if '@' in game:
            away_team, home_team = game.split('@')
            is_home = (team == home_team)
            opponent = home_team if team == away_team else away_team
        else:
            # Fallback if game format is different
            is_home = True
            opponent = 'TBD'
        
        # Create game entry
        game_entry = {
            'player_name': hitter['fd_name'],
            'team': team,
            'opponent': opponent,
            'home_away': 'Home' if is_home else 'Away',
            'game_date': datetime.now().strftime('%Y-%m-%d'),
            'position': hitter['position'],
            'salary': hitter['salary'],
            'fd_id': hitter['fd_id'],
            'confirmed_starter': True,
            'game_string': game
        }
        
        games_data.append(game_entry)
    
    games_df = pd.DataFrame(games_data)
    
    logger.info(f"SUCCESS: Generated {len(games_df)} confirmed hitter games")
    logger.info(f"DATA: Breakdown:")
    logger.info(f"   Home games: {len(games_df[games_df['home_away'] == 'Home'])}")
    logger.info(f"   Away games: {len(games_df[games_df['home_away'] == 'Away'])}")
    
    return games_df

def save_confirmed_hitter_games(games_df):
    """Save confirmed hitter games data"""
    
    # Save main file for pipeline
    main_file = '../data/confirmed_hitter_games.csv'
    games_df.to_csv(main_file, index=False)
    
    # Also save timestamped version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = f'../data/confirmed_hitter_games_{timestamp}.csv'
    games_df.to_csv(timestamped_file, index=False)
    
    logger.info(f" Saved confirmed hitter games:")
    logger.info(f"    Main: {main_file}")
    logger.info(f"    Timestamped: {timestamped_file}")
    
    return main_file

def main():
    """Main function for confirmed hitter games generation"""
    logger.info("TARGET: CONFIRMED STARTERS HITTER GAMES GENERATOR")
    logger.info(" Processing only confirmed starting hitters")
    logger.info("=" * 60)
    
    # Load confirmed starters
    hitters_df = load_confirmed_starters()
    if hitters_df is None:
        return
    
    # Extract hitter names
    hitter_names = extract_hitter_names_from_confirmed(hitters_df)
    
    if not hitter_names:
        logger.error("ERROR: No confirmed hitters found")
        return
    
    # Generate games data
    games_df = generate_confirmed_hitter_games(hitter_names)
    
    # Save results
    main_file = save_confirmed_hitter_games(games_df)
    
    # Summary
    logger.info("=" * 60)
    logger.info("COMPLETE: CONFIRMED HITTER GAMES GENERATION COMPLETE!")
    logger.info(f"SUCCESS: Processed {len(games_df)} confirmed starting hitters")
    logger.info(f" Much faster than processing entire league!")
    logger.info(f" Ready for next pipeline step")
    logger.info("TARGET: 100% focused on players that will actually play")

if __name__ == "__main__":
    main()
