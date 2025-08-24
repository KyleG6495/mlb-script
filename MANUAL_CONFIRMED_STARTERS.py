#!/usr/bin/env python3
"""
MANUAL CONFIRMED STARTERS UPDATER
Use this to manually input confirmed starters from RotoWire or other sources
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def manually_input_confirmed_starters():
    """Manual input of confirmed starters for today"""
    
    print("TARGET: MANUAL CONFIRMED STARTERS INPUT")
    print("=" * 50)
    print("Enter confirmed starting lineups from RotoWire or other sources")
    print("Enter 'done' when finished")
    print("")
    
    confirmed_starters = []
    
    while True:
        name = input("Player name (or 'done'): ").strip()
        if name.lower() == 'done':
            break
            
        team = input("Team: ").strip().upper()
        position = input("Position: ").strip().upper()
        game = input("Game (e.g., NYY@BOS): ").strip()
        
        confirmed_starters.append({
            'name': name,
            'team': team,
            'position': position,
            'game': game,
            'confirmed': True,
            'source': 'manual_input',
            'timestamp': datetime.now().isoformat()
        })
        
        print(f"SUCCESS: Added: {name} ({position}) - {team}")
        print("")
    
    return confirmed_starters

def save_manual_confirmed_starters(confirmed_starters):
    """Save manually entered confirmed starters"""
    
    if not confirmed_starters:
        logger.error("No confirmed starters entered")
        return None
    
    # Create DataFrame
    df = pd.DataFrame(confirmed_starters)
    
    # Save with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/manual_confirmed_starters_{timestamp}.csv"
    df.to_csv(filename, index=False)
    
    logger.info(f" Saved {len(confirmed_starters)} confirmed starters to {filename}")
    
    # Show summary
    pitchers = df[df['position'] == 'P']
    hitters = df[df['position'] != 'P']
    
    logger.info(f"DATA: SUMMARY:")
    logger.info(f"   Pitchers: {len(pitchers)}")
    logger.info(f"   Hitters: {len(hitters)}")
    logger.info(f"   Total: {len(df)}")
    
    return filename

def quick_add_todays_confirmed():
    """Quick add for today's confirmed starters"""
    
    # You can manually update this list each day
    todays_confirmed = [
        # Update this section daily with confirmed starters
        
        # Example format:
        # {'name': 'Aaron Judge', 'team': 'NYY', 'position': 'CF', 'game': 'NYY@BOS'},
        # {'name': 'Shohei Ohtani', 'team': 'LAD', 'position': 'DH', 'game': 'LAD@SD'},
        
        # TODO: Add today's confirmed starters here
        
    ]
    
    if not todays_confirmed:
        print("WARNING: No confirmed starters in quick list - use manual input instead")
        return manually_input_confirmed_starters()
    
    # Add metadata
    for player in todays_confirmed:
        player['confirmed'] = True
        player['source'] = 'quick_add'
        player['timestamp'] = datetime.now().isoformat()
    
    return todays_confirmed

def main():
    """Main function"""
    print("TARGET: CONFIRMED STARTERS UPDATER")
    print("=" * 40)
    print("1. Manual input")
    print("2. Quick add (pre-filled)")
    print("")
    
    choice = input("Choose option (1 or 2): ").strip()
    
    if choice == "1":
        confirmed_starters = manually_input_confirmed_starters()
    elif choice == "2":
        confirmed_starters = quick_add_todays_confirmed()
    else:
        print("Invalid choice")
        return
    
    if confirmed_starters:
        filename = save_manual_confirmed_starters(confirmed_starters)
        if filename:
            print(f"SUCCESS: Confirmed starters saved to {filename}")
            print("TARGET: Now run GET_CONFIRMED_STARTERS.py to filter your FD slate!")

if __name__ == "__main__":
    main()
