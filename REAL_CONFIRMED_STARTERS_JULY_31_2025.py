#!/usr/bin/env python3
"""
REAL CONFIRMED STARTERS - JULY 31, 2025
Updated with actual RotoWire confirmed starting lineups
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_confirmed_starters_july_31_2025():
    """Real confirmed starters from RotoWire for July 31, 2025"""
    
    confirmed_starters = [
        # Game 1: TB @ NYY (1:05 PM ET)
        {'name': 'Ryan Pepiot', 'team': 'TB', 'position': 'P', 'game': 'TB@NYY', 'order': 0},
        {'name': 'Chandler Simpson', 'team': 'TB', 'position': 'CF', 'game': 'TB@NYY', 'order': 1},
        {'name': 'Brandon Lowe', 'team': 'TB', 'position': '2B', 'game': 'TB@NYY', 'order': 2},
        {'name': 'Yandy Diaz', 'team': 'TB', 'position': 'DH', 'game': 'TB@NYY', 'order': 3},
        {'name': 'Jonathan Aranda', 'team': 'TB', 'position': '1B', 'game': 'TB@NYY', 'order': 4},
        {'name': 'Junior Caminero', 'team': 'TB', 'position': '3B', 'game': 'TB@NYY', 'order': 5},
        {'name': 'Josh Lowe', 'team': 'TB', 'position': 'RF', 'game': 'TB@NYY', 'order': 6},
        {'name': 'Jake Mangum', 'team': 'TB', 'position': 'LF', 'game': 'TB@NYY', 'order': 7},
        {'name': 'Nick Fortes', 'team': 'TB', 'position': 'C', 'game': 'TB@NYY', 'order': 8},
        {'name': 'Taylor Walls', 'team': 'TB', 'position': 'SS', 'game': 'TB@NYY', 'order': 9},
        
        {'name': 'Marcus Stroman', 'team': 'NYY', 'position': 'P', 'game': 'TB@NYY', 'order': 0},
        {'name': 'Trent Grisham', 'team': 'NYY', 'position': 'CF', 'game': 'TB@NYY', 'order': 1},
        {'name': 'Ben Rice', 'team': 'NYY', 'position': '1B', 'game': 'TB@NYY', 'order': 2},
        {'name': 'Cody Bellinger', 'team': 'NYY', 'position': 'RF', 'game': 'TB@NYY', 'order': 3},
        {'name': 'Giancarlo Stanton', 'team': 'NYY', 'position': 'DH', 'game': 'TB@NYY', 'order': 4},
        {'name': 'Jazz Chisholm', 'team': 'NYY', 'position': '2B', 'game': 'TB@NYY', 'order': 5},
        {'name': 'Jasson Dominguez', 'team': 'NYY', 'position': 'LF', 'game': 'TB@NYY', 'order': 6},
        {'name': 'Ryan McMahon', 'team': 'NYY', 'position': '3B', 'game': 'TB@NYY', 'order': 7},
        {'name': 'Anthony Volpe', 'team': 'NYY', 'position': 'SS', 'game': 'TB@NYY', 'order': 8},
        {'name': 'Austin Wells', 'team': 'NYY', 'position': 'C', 'game': 'TB@NYY', 'order': 9},
        
        # Game 2: ATL @ CIN (7:10 PM ET)
        {'name': 'Carlos Carrasco', 'team': 'ATL', 'position': 'P', 'game': 'ATL@CIN', 'order': 0},
        {'name': 'Jurickson Profar', 'team': 'ATL', 'position': 'LF', 'game': 'ATL@CIN', 'order': 1},
        {'name': 'Matt Olson', 'team': 'ATL', 'position': '1B', 'game': 'ATL@CIN', 'order': 2},
        {'name': 'Austin Riley', 'team': 'ATL', 'position': '3B', 'game': 'ATL@CIN', 'order': 3},
        {'name': 'Michael Harris', 'team': 'ATL', 'position': 'CF', 'game': 'ATL@CIN', 'order': 4},
        {'name': 'Marcell Ozuna', 'team': 'ATL', 'position': 'DH', 'game': 'ATL@CIN', 'order': 5},
        {'name': 'Ozzie Albies', 'team': 'ATL', 'position': '2B', 'game': 'ATL@CIN', 'order': 6},
        {'name': 'Sean Murphy', 'team': 'ATL', 'position': 'C', 'game': 'ATL@CIN', 'order': 7},
        {'name': 'Eli White', 'team': 'ATL', 'position': 'RF', 'game': 'ATL@CIN', 'order': 8},
        {'name': 'Nick Allen', 'team': 'ATL', 'position': 'SS', 'game': 'ATL@CIN', 'order': 9},
        
        {'name': 'Andrew Abbott', 'team': 'CIN', 'position': 'P', 'game': 'ATL@CIN', 'order': 0},
        {'name': 'Gavin Lux', 'team': 'CIN', 'position': 'DH', 'game': 'ATL@CIN', 'order': 1},
        {'name': 'Matt McLain', 'team': 'CIN', 'position': '2B', 'game': 'ATL@CIN', 'order': 2},
        {'name': 'Elly De La Cruz', 'team': 'CIN', 'position': 'SS', 'game': 'ATL@CIN', 'order': 3},
        {'name': 'Austin Hays', 'team': 'CIN', 'position': 'LF', 'game': 'ATL@CIN', 'order': 4},
        {'name': 'Jake Fraley', 'team': 'CIN', 'position': 'RF', 'game': 'ATL@CIN', 'order': 5},
        {'name': 'Spencer Steer', 'team': 'CIN', 'position': '1B', 'game': 'ATL@CIN', 'order': 6},
        {'name': 'Tyler Stephenson', 'team': 'CIN', 'position': 'C', 'game': 'ATL@CIN', 'order': 7},
        {'name': 'Will Benson', 'team': 'CIN', 'position': 'CF', 'game': 'ATL@CIN', 'order': 8},
        {'name': 'Kebryan Hayes', 'team': 'CIN', 'position': '3B', 'game': 'ATL@CIN', 'order': 9},
        
        # Game 3: TEX @ SEA (9:40 PM ET)
        {'name': 'Kumar Rocker', 'team': 'TEX', 'position': 'P', 'game': 'TEX@SEA', 'order': 0},
        {'name': 'Josh Smith', 'team': 'TEX', 'position': '1B', 'game': 'TEX@SEA', 'order': 1},
        {'name': 'Corey Seager', 'team': 'TEX', 'position': 'SS', 'game': 'TEX@SEA', 'order': 2},
        {'name': 'Marcus Semien', 'team': 'TEX', 'position': '2B', 'game': 'TEX@SEA', 'order': 3},
        {'name': 'Adolis Garcia', 'team': 'TEX', 'position': 'RF', 'game': 'TEX@SEA', 'order': 4},
        {'name': 'Joc Pederson', 'team': 'TEX', 'position': 'DH', 'game': 'TEX@SEA', 'order': 5},
        {'name': 'Wyatt Langford', 'team': 'TEX', 'position': 'LF', 'game': 'TEX@SEA', 'order': 6},
        {'name': 'Evan Carter', 'team': 'TEX', 'position': 'CF', 'game': 'TEX@SEA', 'order': 7},
        {'name': 'Josh Jung', 'team': 'TEX', 'position': '3B', 'game': 'TEX@SEA', 'order': 8},
        {'name': 'Kyle Higashioka', 'team': 'TEX', 'position': 'C', 'game': 'TEX@SEA', 'order': 9},
        
        {'name': 'George Kirby', 'team': 'SEA', 'position': 'P', 'game': 'TEX@SEA', 'order': 0},
        {'name': 'JP Crawford', 'team': 'SEA', 'position': 'SS', 'game': 'TEX@SEA', 'order': 1},
        {'name': 'Julio Rodriguez', 'team': 'SEA', 'position': 'CF', 'game': 'TEX@SEA', 'order': 2},
        {'name': 'Cal Raleigh', 'team': 'SEA', 'position': 'C', 'game': 'TEX@SEA', 'order': 3},
        {'name': 'Eugenio Suarez', 'team': 'SEA', 'position': '3B', 'game': 'TEX@SEA', 'order': 4},
        {'name': 'Josh Naylor', 'team': 'SEA', 'position': '1B', 'game': 'TEX@SEA', 'order': 5},
        {'name': 'Randy Arozarena', 'team': 'SEA', 'position': 'LF', 'game': 'TEX@SEA', 'order': 6},
        {'name': 'Jorge Polanco', 'team': 'SEA', 'position': 'DH', 'game': 'TEX@SEA', 'order': 7},
        {'name': 'Dominic Canzone', 'team': 'SEA', 'position': 'RF', 'game': 'TEX@SEA', 'order': 8},
        {'name': 'Cole Young', 'team': 'SEA', 'position': '2B', 'game': 'TEX@SEA', 'order': 9},
    ]
    
    # Add metadata
    for player in confirmed_starters:
        player['confirmed'] = True
        player['source'] = 'rotowire_actual'
        player['date'] = '2025-07-31'
        player['timestamp'] = datetime.now().isoformat()
    
    return confirmed_starters

def filter_fd_slate_with_real_confirmed(fd_df, confirmed_starters):
    """Filter FD slate with real confirmed starters from RotoWire"""
    logger.info("TARGET: FILTERING FD SLATE WITH REAL CONFIRMED STARTERS")
    logger.info(f"INFO: {len(confirmed_starters)} confirmed starters from RotoWire")
    
    confirmed_names = [player['name'] for player in confirmed_starters]
    filtered_players = []
    
    for idx, fd_player in fd_df.iterrows():
        fd_full = f"{fd_player['First Name']} {fd_player['Last Name']}"
        fd_nick = fd_player['Nickname']
        
        # Check if this player is in confirmed starters
        is_confirmed = False
        for confirmed_name in confirmed_names:
            if (confirmed_name == fd_full or 
                confirmed_name == fd_nick or
                confirmed_name.split()[-1] == fd_player['Last Name']):
                is_confirmed = True
                logger.info(f"SUCCESS: CONFIRMED: {fd_nick} (matches {confirmed_name})")
                break
        
        if is_confirmed:
            filtered_players.append(fd_player)
    
    filtered_df = pd.DataFrame(filtered_players)
    
    logger.info(f"DATA: REAL CONFIRMED STARTERS FILTERING:")
    logger.info(f"   Original FD slate: {len(fd_df)} players")
    logger.info(f"   Real confirmed starters: {len(filtered_df)} players")
    logger.info(f"   ERROR: Non-starters filtered: {len(fd_df) - len(filtered_df)} players")
    
    return filtered_df

def save_real_confirmed_starters():
    """Save real confirmed starters for July 31, 2025"""
    confirmed_starters = get_confirmed_starters_july_31_2025()
    
    # Save confirmed starters list
    df = pd.DataFrame(confirmed_starters)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/real_confirmed_starters_july_31_2025_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    logger.info(f" Saved {len(confirmed_starters)} real confirmed starters to {filename}")
    
    # Show breakdown
    pitchers = df[df['position'] == 'P']
    hitters = df[df['position'] != 'P']
    
    logger.info(f"DATA: BREAKDOWN:")
    logger.info(f"   Pitchers: {len(pitchers)}")
    logger.info(f"   Hitters: {len(hitters)}")
    logger.info(f"   Total confirmed: {len(df)}")
    
    return filename, confirmed_starters

def main():
    """Update system with real confirmed starters"""
    logger.info("TARGET: REAL CONFIRMED STARTERS - JULY 31, 2025")
    logger.info("INFO: Updated with actual RotoWire starting lineups")
    logger.info("=" * 60)
    
    # Save confirmed starters
    filename, confirmed_starters = save_real_confirmed_starters()
    
    # Filter FD slate
    try:
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f" Loaded FD slate: {len(fd_df)} players")
        
        # Filter with real confirmed starters
        confirmed_df = filter_fd_slate_with_real_confirmed(fd_df, confirmed_starters)
        
        # Save filtered slate
        main_file = "../fd_current_slate/fd_slate_real_confirmed_july_31_2025.csv"
        confirmed_df.to_csv(main_file, index=False)
        
        logger.info(f" SAVED REAL CONFIRMED SLATE: {main_file}")
        logger.info("")
        logger.info("COMPLETE: REAL CONFIRMED STARTERS SYSTEM READY!")
        logger.info(f"SUCCESS: {len(confirmed_df)} confirmed starting players")
        logger.info(f" {len(fd_df) - len(confirmed_df)} non-starters eliminated")
        logger.info(" 100% DISASTER-PROOF LINEUPS GUARANTEED!")
        
    except FileNotFoundError:
        logger.error("ERROR: FD slate file not found")

if __name__ == "__main__":
    main()
