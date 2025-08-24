#!/usr/bin/env python3
"""
CONFIRMED STARTERS HITTER ID ASSIGNMENT
Maps confirmed starting hitters to MLB API player IDs
Only processes confirmed starters for maximum efficiency!
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_confirmed_hitter_games():
    """Load confirmed hitter games data"""
    try:
        games_df = pd.read_csv('../data/confirmed_hitter_games.csv')
        logger.info(f"SUCCESS: Loaded {len(games_df)} confirmed hitter games")
        return games_df
    except FileNotFoundError:
        logger.error("ERROR: confirmed_hitter_games.csv not found!")
        logger.error("TIP: Run step 1 first: 1_CONFIRMED_generate_hitter_games.py")
        return None

def load_player_id_mapping():
    """Load existing player ID mapping if available"""
    try:
        # Try to load from main player database
        mapping_files = [
            '../data/player_ids.csv',
            '../data/hitter_ids.csv',
            '../data/players_with_ids.csv'
        ]
        
        mapping_df = None
        for file_path in mapping_files:
            try:
                mapping_df = pd.read_csv(file_path)
                logger.info(f"SUCCESS: Loaded player ID mapping from {file_path}")
                break
            except FileNotFoundError:
                continue
        
        if mapping_df is None:
            logger.warning("WARNING: No existing player ID mapping found")
            logger.info("TIP: Will create basic mapping from confirmed players")
            return None
        
        return mapping_df
    except Exception as e:
        logger.warning(f"WARNING: Error loading player mapping: {e}")
        return None

def create_confirmed_player_ids(games_df):
    """Create player IDs for confirmed starters"""
    
    confirmed_players = []
    
    for _, game in games_df.iterrows():
        player_name = game['player_name']
        team = game['team']
        fd_id = game['fd_id']
        
        # Create a simple player ID based on FD ID
        player_id = f"MLB_{fd_id}_{team}"
        
        player_entry = {
            'player_name': player_name,
            'player_id': player_id,
            'team': team,
            'fd_id': fd_id,
            'confirmed_starter': True,
            'mapping_source': 'confirmed_slate'
        }
        
        confirmed_players.append(player_entry)
        logger.info(f"INFO: Mapped: {player_name} ({team})  {player_id}")
    
    return pd.DataFrame(confirmed_players)

def assign_confirmed_hitter_ids(games_df, player_mapping):
    """Assign player IDs to confirmed hitters"""
    
    # If we have existing mapping, try to use it
    if player_mapping is not None:
        # Try to match by name and team
        games_with_ids = games_df.copy()
        games_with_ids['player_id'] = None
        
        for idx, game in games_df.iterrows():
            player_name = game['player_name']
            team = game['team']
            
            # Try exact name match first
            matches = player_mapping[
                (player_mapping['player_name'].str.lower() == player_name.lower()) &
                (player_mapping['team'] == team)
            ]
            
            if len(matches) > 0:
                games_with_ids.at[idx, 'player_id'] = matches.iloc[0]['player_id']
                logger.info(f"SUCCESS: Matched: {player_name} ({team})")
            else:
                # Create new ID for unmatched players
                new_id = f"MLB_{game['fd_id']}_{team}"
                games_with_ids.at[idx, 'player_id'] = new_id
                logger.info(f" New ID: {player_name} ({team})  {new_id}")
    else:
        # Create all new IDs
        logger.info(" Creating new player IDs for all confirmed starters")
        games_with_ids = games_df.copy()
        games_with_ids['player_id'] = games_with_ids.apply(
            lambda row: f"MLB_{row['fd_id']}_{row['team']}", axis=1
        )
    
    return games_with_ids

def save_confirmed_hitter_ids(games_with_ids_df):
    """Save confirmed hitter games with IDs"""
    
    # Save main file for pipeline
    main_file = '../data/confirmed_hitter_games_with_ids.csv'
    games_with_ids_df.to_csv(main_file, index=False)
    
    # Also save timestamped version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = f'../data/confirmed_hitter_games_with_ids_{timestamp}.csv'
    games_with_ids_df.to_csv(timestamped_file, index=False)
    
    logger.info(f" Saved confirmed hitter games with IDs:")
    logger.info(f"    Main: {main_file}")
    logger.info(f"    Timestamped: {timestamped_file}")
    
    return main_file

def main():
    """Main function for confirmed hitter ID assignment"""
    logger.info(" CONFIRMED STARTERS HITTER ID ASSIGNMENT")
    logger.info(" Processing only confirmed starting hitters")
    logger.info("=" * 60)
    
    # Load confirmed hitter games
    games_df = load_confirmed_hitter_games()
    if games_df is None:
        return
    
    # Load existing player ID mapping
    player_mapping = load_player_id_mapping()
    
    # Assign player IDs to confirmed hitters
    games_with_ids_df = assign_confirmed_hitter_ids(games_df, player_mapping)
    
    # Save results
    main_file = save_confirmed_hitter_ids(games_with_ids_df)
    
    # Summary
    logger.info("=" * 60)
    logger.info("COMPLETE: CONFIRMED HITTER ID ASSIGNMENT COMPLETE!")
    logger.info(f"SUCCESS: Processed {len(games_with_ids_df)} confirmed starting hitters")
    logger.info(f" All players now have unique IDs")
    logger.info(f" Much faster than processing entire league!")
    logger.info(f" Ready for next pipeline step")
    logger.info("TARGET: 100% focused on players that will actually play")

if __name__ == "__main__":
    main()
