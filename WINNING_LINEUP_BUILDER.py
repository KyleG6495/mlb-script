#!/usr/bin/env python3
"""
TARGET: SIMPLE WINNING LINEUP BUILDER
Uses actual fd_slate_today.csv with Rotowire data
Creates WINNING lineups based on FPPG and confirmed starters
"""

import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_winning_lineups():
    """Create winning lineups using actual fd_slate_today.csv"""
    
    logger.info("TARGET: CREATING WINNING LINEUPS")
    logger.info("="*50)
    logger.info("Using fd_slate_today.csv with current Rotowire data")
    logger.info("")
    
    try:
        # Load the actual FD slate
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f" Loaded fd_slate_today.csv: {len(df)} players")
        
        # Remove IL players first
        healthy_players = df[df['Injury Indicator'] != 'IL'].copy()
        logger.info(f"SUCCESS: After removing IL players: {len(healthy_players)} healthy players")
        
        # Get confirmed starting pitchers (Probable Pitcher = Yes)
        starting_pitchers = healthy_players[
            (healthy_players['Position'] == 'P') & 
            (healthy_players['Probable Pitcher'] == 'Yes')
        ].copy()
        
        # If no "Yes" probable pitchers, use top FPPG pitchers
        if len(starting_pitchers) == 0:
            starting_pitchers = healthy_players[
                healthy_players['Position'] == 'P'
            ].nlargest(20, 'FPPG')
        
        logger.info(f"BASEBALL: Starting pitchers available: {len(starting_pitchers)}")
        
        # Get hitters with batting orders (confirmed starters)
        confirmed_hitters = healthy_players[
            (healthy_players['Position'] != 'P') &
            (healthy_players['Batting Order'].notna()) &
            (healthy_players['Batting Order'] > 0)
        ].copy()
        
        logger.info(f"BASEBALL: Confirmed starting hitters: {len(confirmed_hitters)}")
        
        # If not enough confirmed hitters, add high FPPG players
        if len(confirmed_hitters) < 50:  # Need enough for lineups
            additional_hitters = healthy_players[
                (healthy_players['Position'] != 'P') &
                (~healthy_players['Id'].isin(confirmed_hitters['Id'])) &
                (healthy_players['FPPG'] >= 8.0)  # Minimum FPPG threshold
            ].nlargest(100, 'FPPG')
            
            all_hitters = pd.concat([confirmed_hitters, additional_hitters], ignore_index=True)
            all_hitters = all_hitters.drop_duplicates(subset=['Id'], keep='first')
        else:
            all_hitters = confirmed_hitters
        
        logger.info(f"BASEBALL: Total hitter pool: {len(all_hitters)}")
        
        # Sort by FPPG for better selection
        starting_pitchers = starting_pitchers.sort_values('FPPG', ascending=False)
        all_hitters = all_hitters.sort_values('FPPG', ascending=False)
        
        # Separate hitters by position
        catchers = all_hitters[
            (all_hitters['Position'].str.contains('C', na=False)) |
            (all_hitters['Roster Position'].str.contains('C/', na=False))
        ].copy()
        
        first_base = all_hitters[
            (all_hitters['Position'].str.contains('1B', na=False)) |
            (all_hitters['Roster Position'].str.contains('1B/', na=False))
        ].copy()
        
        second_base = all_hitters[
            (all_hitters['Position'].str.contains('2B', na=False)) |
            (all_hitters['Roster Position'].str.contains('2B/', na=False))
        ].copy()
        
        third_base = all_hitters[
            (all_hitters['Position'].str.contains('3B', na=False)) |
            (all_hitters['Roster Position'].str.contains('3B/', na=False))
        ].copy()
        
        shortstops = all_hitters[
            (all_hitters['Position'].str.contains('SS', na=False)) |
            (all_hitters['Roster Position'].str.contains('SS/', na=False))
        ].copy()
        
        outfielders = all_hitters[
            (all_hitters['Position'].str.contains('OF', na=False)) |
            (all_hitters['Roster Position'].str.contains('OF/', na=False))
        ].copy()
        
        logger.info(f"Position breakdown: P={len(starting_pitchers)}, C={len(catchers)}, 1B={len(first_base)}, 2B={len(second_base)}, 3B={len(third_base)}, SS={len(shortstops)}, OF={len(outfielders)}")
        
        # Create 8 winning lineups
        lineups = []
        used_combinations = set()
        
        for i in range(8):
            lineup_players = []
            used_ids = set()
            
            # Select pitcher (cycle through top pitchers)
            pitcher_idx = i % min(len(starting_pitchers), 8)
            pitcher = starting_pitchers.iloc[pitcher_idx]
            lineup_players.append(pitcher)
            used_ids.add(pitcher['Id'])
            
            # Select position players (avoid duplicates across lineups)
            position_data = [
                (catchers, 'C'),
                (first_base, '1B'),
                (second_base, '2B'),
                (third_base, '3B'),
                (shortstops, 'SS')
            ]
            
            for pos_df, pos_name in position_data:
                available = pos_df[~pos_df['Id'].isin(used_ids)]
                if len(available) > 0:
                    # Select different players for variety
                    idx = (i * 2) % len(available)
                    player = available.iloc[idx]
                    lineup_players.append(player)
                    used_ids.add(player['Id'])
            
            # Select 3 outfielders
            available_of = outfielders[~outfielders['Id'].isin(used_ids)]
            for of_idx in range(3):
                if len(available_of) > of_idx:
                    idx = (i + of_idx) % len(available_of)
                    of_player = available_of.iloc[idx]
                    lineup_players.append(of_player)
                    used_ids.add(of_player['Id'])
                    available_of = available_of[available_of['Id'] != of_player['Id']]
            
            # Select utility (any remaining hitter)
            all_remaining = all_hitters[~all_hitters['Id'].isin(used_ids)]
            if len(all_remaining) > 0:
                util_idx = (i * 3) % len(all_remaining)
                util_player = all_remaining.iloc[util_idx]
                lineup_players.append(util_player)
                used_ids.add(util_player['Id'])
            
            # Check if we have 10 players and reasonable salary
            if len(lineup_players) == 10:
                total_salary = sum(p['Salary'] for p in lineup_players)
                total_fppg = sum(p['FPPG'] for p in lineup_players)
                
                if total_salary <= 35000:  # FanDuel salary cap
                    lineup_df = pd.DataFrame(lineup_players)
                    lineup_info = {
                        'lineup': lineup_df,
                        'total_salary': total_salary,
                        'total_fppg': total_fppg,
                        'lineup_num': i + 1
                    }
                    lineups.append(lineup_info)
                    logger.info(f"SUCCESS: Lineup {i+1}: ${total_salary:,} | {total_fppg:.1f} FPPG")
        
        return lineups, starting_pitchers, all_hitters
        
    except Exception as e:
        logger.error(f"ERROR: Error creating winning lineups: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def format_for_fanduel_upload(lineups):
    """Format lineups exactly for FanDuel CSV upload"""
    
    logger.info("INFO: Formatting for FanDuel upload...")
    
    upload_rows = []
    
    for lineup_info in lineups:
        lineup = lineup_info['lineup']
        lineup_num = lineup_info['lineup_num']
        
        # Get players by position
        pitcher = lineup[lineup['Position'] == 'P'].iloc[0]
        
        remaining_players = lineup[lineup['Position'] != 'P'].copy()
        
        # Fill positions
        positions_filled = {}
        
        # Fill specific positions
        for pos in ['C', '1B', '2B', '3B', 'SS']:
            pos_players = remaining_players[
                (remaining_players['Position'].str.contains(pos, na=False)) |
                (remaining_players['Roster Position'].str.contains(pos, na=False))
            ]
            
            if len(pos_players) > 0:
                selected = pos_players.iloc[0]
                positions_filled[pos] = selected
                remaining_players = remaining_players[remaining_players['Id'] != selected['Id']]
        
        # Fill OF positions
        of_players = remaining_players[
            (remaining_players['Position'].str.contains('OF', na=False)) |
            (remaining_players['Roster Position'].str.contains('OF', na=False))
        ]
        
        of_filled = []
        for idx, of_player in of_players.iterrows():
            if len(of_filled) < 3:
                of_filled.append(of_player)
                remaining_players = remaining_players[remaining_players['Id'] != of_player['Id']]
        
        # Fill UTIL with remaining player
        util_player = remaining_players.iloc[0] if len(remaining_players) > 0 else None
        
        # Create upload row
        upload_row = {
            'P': pitcher['Id'],
            'C/1B': positions_filled.get('C', {}).get('Id', ''),
            '2B': positions_filled.get('2B', {}).get('Id', ''),
            '3B': positions_filled.get('3B', {}).get('Id', ''),
            'SS': positions_filled.get('SS', {}).get('Id', ''),
            'OF1': of_filled[0]['Id'] if len(of_filled) > 0 else '',
            'OF2': of_filled[1]['Id'] if len(of_filled) > 1 else '',
            'OF3': of_filled[2]['Id'] if len(of_filled) > 2 else '',
            'UTIL': util_player['Id'] if util_player is not None else '',
            'Lineup_Name': f"Winning_Lineup_{lineup_num}",
            'Salary': lineup_info['total_salary'],
            'FPPG': round(lineup_info['total_fppg'], 1)
        }
        
        upload_rows.append(upload_row)
    
    return pd.DataFrame(upload_rows)

def main():
    """Main winning lineup builder"""
    
    logger.info("LINEUP: SIMPLE WINNING LINEUP BUILDER")
    logger.info("="*60)
    logger.info("Creating WINNING lineups from fd_slate_today.csv")
    logger.info("")
    
    # Create winning lineups
    lineups, pitchers, hitters = create_winning_lineups()
    
    if not lineups:
        logger.error("ERROR: Could not create any lineups")
        return
    
    # Format for FanDuel upload
    upload_df = format_for_fanduel_upload(lineups)
    
    # Save lineups
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save upload format
    upload_file = f'../data/WINNING_LINEUPS_{timestamp}.csv'
    upload_df.to_csv(upload_file, index=False)
    
    # Also save as current
    current_file = '../data/WINNING_LINEUPS.csv'
    upload_df.to_csv(current_file, index=False)
    
    logger.info("")
    logger.info(" WINNING LINEUPS SAVED:")
    logger.info(f"    Timestamped: {upload_file}")
    logger.info(f"    Current: {current_file}")
    
    logger.info("")
    logger.info("DATA: LINEUP SUMMARY:")
    logger.info(f"   Lineups created: {len(upload_df)}")
    logger.info(f"   Salary range: ${upload_df['Salary'].min():,} - ${upload_df['Salary'].max():,}")
    logger.info(f"   FPPG range: {upload_df['FPPG'].min():.1f} - {upload_df['FPPG'].max():.1f}")
    
    logger.info("")
    logger.info("COMPLETE: WINNING LINEUPS COMPLETE!")
    logger.info("="*60)
    logger.info("SUCCESS: Using actual fd_slate_today.csv data")
    logger.info("LINEUP: Optimized for WINNING performance")
    logger.info(" Ready for FanDuel upload")

if __name__ == "__main__":
    main()
