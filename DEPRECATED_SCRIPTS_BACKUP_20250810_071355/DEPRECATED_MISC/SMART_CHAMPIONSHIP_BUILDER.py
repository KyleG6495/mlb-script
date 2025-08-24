#!/usr/bin/env python3
"""
🏆 SMART CHAMPIONSHIP LINEUP BUILDER
Uses ONLY confirmed starting players (batting order + probable pitchers)
Prevents NS/PO players from appearing in lineups
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import itertools
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_smart_starter_slate():
    """Load the smart starter slate with only confirmed starters"""
    
    logger.info("📥 Loading smart starter slate...")
    
    # FORCE LOAD STRICT STARTERS ONLY - CONFIRMED BATTING ORDERS ONLY
    import os
    
    strict_file = '../data/fd_slate_STRICT_STARTERS.csv'
    if not os.path.exists(strict_file):
        logger.error(f"❌ {strict_file} not found! Run STRICT_STARTER_FILTER.py first")
        return None
    
    try:
        df = pd.read_csv(strict_file)
        logger.info(f"✅ FORCE LOADED strict starter slate: {len(df)} CONFIRMED STARTERS ONLY")
        logger.info(f"📍 File: {strict_file}")
        
        # VERIFY NO NOLAN GORMAN
        gorman_check = df[df['Nickname'].str.contains('Gorman', na=False)]
        if len(gorman_check) > 0:
            logger.error(f"❌ NOLAN GORMAN FOUND IN STRICT SLATE! This should not happen!")
            logger.error(f"Gorman entries: {gorman_check[['Nickname', 'Team', 'Batting Order']].to_dict('records')}")
            return None
        else:
            logger.info("✅ VERIFIED: No Nolan Gorman in strict slate")
        
        # Verify we have enough players for lineups
        positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3, 'Util': 1}
        
        logger.info("🏟️ Position availability check:")
        for pos, needed in positions_needed.items():
            if pos == 'Util':
                continue  # Util can be any hitter
                
            if pos == 'OF':
                available = len(df[
                    (df['Position'] == 'OF') |
                    (df['Position'].str.contains('OF', na=False)) |
                    (df['Roster Position'].str.contains('OF', na=False))
                ])
            else:
                available = len(df[
                    (df['Position'] == pos) |
                    (df['Position'].str.contains(pos, na=False)) |
                    (df['Roster Position'].str.contains(pos, na=False))
                ])
                
            logger.info(f"   {pos}: {available} available (need {needed})")
            
            if available < needed:
                logger.warning(f"⚠️ Limited {pos} options: only {available} available")
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error loading strict starter slate: {e}")
        return None

def create_optimized_lineups(df, num_lineups=8):
    """Create optimized lineups using only confirmed starters"""
    
    logger.info(f"🎯 Creating {num_lineups} optimized lineups from confirmed starters...")
    
    lineups = []
    used_combinations = set()
    
    # Separate by position - handle multi-position players
    pitchers = df[df['Position'] == 'P'].copy()
    
    # For position players, check both Position and Roster Position columns
    catchers = df[
        (df['Position'].str.contains('C', na=False)) |
        (df['Roster Position'].str.contains('C/', na=False))
    ].copy()
    
    first_base = df[
        (df['Position'].str.contains('1B', na=False)) |
        (df['Roster Position'].str.contains('1B/', na=False))
    ].copy()
    
    second_base = df[
        (df['Position'].str.contains('2B', na=False)) |
        (df['Roster Position'].str.contains('2B/', na=False))
    ].copy()
    
    third_base = df[
        (df['Position'].str.contains('3B', na=False)) |
        (df['Roster Position'].str.contains('3B/', na=False))
    ].copy()
    
    shortstops = df[
        (df['Position'].str.contains('SS', na=False)) |
        (df['Roster Position'].str.contains('SS/', na=False))
    ].copy()
    
    outfielders = df[
        (df['Position'].str.contains('OF', na=False)) |
        (df['Roster Position'].str.contains('OF/', na=False))
    ].copy()
    
    # All hitters for utility
    hitters = df[df['Position'] != 'P'].copy()
    
    logger.info(f"Position pools: P={len(pitchers)}, C={len(catchers)}, 1B={len(first_base)}, 2B={len(second_base)}, 3B={len(third_base)}, SS={len(shortstops)}, OF={len(outfielders)}")
    
    # Sort by FPPG for better lineup construction
    for pos_df in [pitchers, catchers, first_base, second_base, third_base, shortstops, outfielders, hitters]:
        pos_df.sort_values('FPPG', ascending=False, inplace=True)
    
    attempts = 0
    max_attempts = 100  # Reduced for faster execution
    
    while len(lineups) < num_lineups and attempts < max_attempts:
        attempts += 1
        
        try:
            # Build lineup 
            lineup_players = []
            used_ids = set()
            
            # Select pitcher
            if len(pitchers) > 0:
                pitcher_idx = attempts % len(pitchers)  # Cycle through pitchers
                pitcher = pitchers.iloc[pitcher_idx]
                lineup_players.append(pitcher)
                used_ids.add(pitcher['Id'])
            else:
                continue
                
            # Select position players - one from each position
            position_data = [
                (catchers, 'C'),
                (first_base, '1B'), 
                (second_base, '2B'),
                (third_base, '3B'),
                (shortstops, 'SS')
            ]
            
            valid_lineup = True
            for pos_df, pos_name in position_data:
                available = pos_df[~pos_df['Id'].isin(used_ids)]
                if len(available) > 0:
                    # Use cycling with some randomness
                    idx = (attempts + len(lineup_players)) % len(available)
                    player = available.iloc[idx]
                    lineup_players.append(player)
                    used_ids.add(player['Id'])
                else:
                    logger.warning(f"⚠️ No available {pos_name} players")
                    valid_lineup = False
                    break
            
            if not valid_lineup:
                continue
                
            # Select 3 outfielders
            available_of = outfielders[~outfielders['Id'].isin(used_ids)]
            if len(available_of) >= 3:
                # Select 3 different outfielders
                for i in range(3):
                    idx = (attempts + i) % len(available_of)
                    of_player = available_of.iloc[idx]
                    if of_player['Id'] not in used_ids:
                        lineup_players.append(of_player)
                        used_ids.add(of_player['Id'])
                        available_of = available_of[available_of['Id'] != of_player['Id']]
            else:
                continue
                
            # Select utility player (any remaining hitter)
            all_hitters = hitters[~hitters['Id'].isin(used_ids)]
            if len(all_hitters) > 0:
                util_idx = attempts % len(all_hitters)
                util_player = all_hitters.iloc[util_idx]
                lineup_players.append(util_player)
                used_ids.add(util_player['Id'])
            else:
                continue
                
            # Check salary constraint
            total_salary = sum(p['Salary'] for p in lineup_players)
            if total_salary > 35000:
                continue
                
            # Check for duplicate lineup
            lineup_key = tuple(sorted(p['Id'] for p in lineup_players))
            if lineup_key in used_combinations:
                continue
                
            used_combinations.add(lineup_key)
            
            # Create lineup dataframe
            lineup_df = pd.DataFrame(lineup_players)
            total_fppg = lineup_df['FPPG'].sum()
            
            lineup_info = {
                'lineup': lineup_df,
                'total_salary': total_salary,
                'total_fppg': total_fppg,
                'players': len(lineup_df)
            }
            
            lineups.append(lineup_info)
            logger.info(f"✅ Lineup {len(lineups)}: ${total_salary:,} | {total_fppg:.1f} FPPG")
            
        except Exception as e:
            logger.warning(f"⚠️ Lineup creation error: {e}")
            continue
    
    logger.info(f"🎯 Created {len(lineups)} lineups from {attempts} attempts")
    return lineups

def format_for_fanduel(lineups):
    """Format lineups for FanDuel submission"""
    
    logger.info("📋 Formatting lineups for FanDuel...")
    
    all_lineups = []
    
    for i, lineup_info in enumerate(lineups, 1):
        lineup = lineup_info['lineup']
        
        # Create FanDuel format
        fd_lineup = {}
        
        # Find players for each position
        pitcher = lineup[lineup['Position'] == 'P'].iloc[0] if len(lineup[lineup['Position'] == 'P']) > 0 else None
        
        # Position players
        remaining_players = lineup[lineup['Position'] != 'P'].copy()
        
        # Fill positions
        positions_filled = {}
        
        # Fill specific positions first
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
            (remaining_players['Position'] == 'OF') |
            (remaining_players['Position'].str.contains('OF', na=False)) |
            (remaining_players['Roster Position'].str.contains('OF', na=False))
        ]
        
        of_filled = 0
        for idx, of_player in of_players.iterrows():
            if of_filled < 3:
                positions_filled[f'OF{of_filled+1}'] = of_player
                remaining_players = remaining_players[remaining_players['Id'] != of_player['Id']]
                of_filled += 1
        
        # Fill UTIL with remaining player
        if len(remaining_players) > 0:
            positions_filled['UTIL'] = remaining_players.iloc[0]
        
        # Create FD row with player IDs
        fd_row = {
            'P': pitcher['Id'] if pitcher is not None else "",
            'C': positions_filled['C']['Id'] if 'C' in positions_filled else "",
            '1B': positions_filled['1B']['Id'] if '1B' in positions_filled else "",
            '2B': positions_filled['2B']['Id'] if '2B' in positions_filled else "",
            '3B': positions_filled['3B']['Id'] if '3B' in positions_filled else "",
            'SS': positions_filled['SS']['Id'] if 'SS' in positions_filled else "",
            'OF': positions_filled['OF1']['Id'] if 'OF1' in positions_filled else "",
            'OF_2': positions_filled['OF2']['Id'] if 'OF2' in positions_filled else "",
            'OF_3': positions_filled['OF3']['Id'] if 'OF3' in positions_filled else "",
            'UTIL': positions_filled['UTIL']['Id'] if 'UTIL' in positions_filled else "",
            'Lineup': f"Smart_Lineup_{i}",
            'Salary': lineup_info['total_salary'],
            'FPPG': round(lineup_info['total_fppg'], 1),
            # Add player names for reference
            'P_Name': f"{pitcher['Nickname']} ({pitcher['Team']})" if pitcher is not None else "",
            'C_Name': f"{positions_filled['C']['Nickname']} ({positions_filled['C']['Team']})" if 'C' in positions_filled else "",
            '1B_Name': f"{positions_filled['1B']['Nickname']} ({positions_filled['1B']['Team']})" if '1B' in positions_filled else "",
            '2B_Name': f"{positions_filled['2B']['Nickname']} ({positions_filled['2B']['Team']})" if '2B' in positions_filled else "",
            '3B_Name': f"{positions_filled['3B']['Nickname']} ({positions_filled['3B']['Team']})" if '3B' in positions_filled else "",
            'SS_Name': f"{positions_filled['SS']['Nickname']} ({positions_filled['SS']['Team']})" if 'SS' in positions_filled else "",
            'OF_Name': f"{positions_filled['OF1']['Nickname']} ({positions_filled['OF1']['Team']})" if 'OF1' in positions_filled else "",
            'OF_2_Name': f"{positions_filled['OF2']['Nickname']} ({positions_filled['OF2']['Team']})" if 'OF2' in positions_filled else "",
            'OF_3_Name': f"{positions_filled['OF3']['Nickname']} ({positions_filled['OF3']['Team']})" if 'OF3' in positions_filled else "",
            'UTIL_Name': f"{positions_filled['UTIL']['Nickname']} ({positions_filled['UTIL']['Team']})" if 'UTIL' in positions_filled else ""
        }
        
        all_lineups.append(fd_row)
    
    return pd.DataFrame(all_lineups)

def main():
    """Main smart championship lineup builder"""
    
    logger.info("🏆 SMART CHAMPIONSHIP LINEUP BUILDER")
    logger.info("="*60)
    logger.info("Building lineups from ONLY confirmed starting players")
    logger.info("This eliminates NS/PO players from your lineups!")
    logger.info("")
    
    try:
        # Load smart starter slate
        df = load_smart_starter_slate()
        if df is None:
            logger.error("❌ Cannot load smart starter slate")
            return
        
        # Create optimized lineups
        lineups = create_optimized_lineups(df, num_lineups=8)
        
        if not lineups:
            logger.error("❌ Could not create any lineups")
            return
        
        # Format for FanDuel
        fd_lineups = format_for_fanduel(lineups)
        
        # Save lineups
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save to multiple locations
        files_to_save = [
            f'../data/SMART_CHAMPIONSHIP_LINEUPS_{timestamp}.csv',
            '../data/SMART_CHAMPIONSHIP_LINEUPS.csv',
            '../fd_current_slate/SMART_CHAMPIONSHIP_LINEUPS.csv'
        ]
        
        for file_path in files_to_save:
            fd_lineups.to_csv(file_path, index=False)
            logger.info(f"💾 Saved: {file_path}")
        
        logger.info("")
        logger.info("📊 LINEUP SUMMARY:")
        logger.info(f"   Lineups created: {len(fd_lineups)}")
        logger.info(f"   Salary range: ${fd_lineups['Salary'].min():,} - ${fd_lineups['Salary'].max():,}")
        logger.info(f"   FPPG range: {fd_lineups['FPPG'].min():.1f} - {fd_lineups['FPPG'].max():.1f}")
        logger.info(f"   Players used: {len(df)} confirmed starters only")
        
        logger.info("")
        logger.info("🎉 SMART CHAMPIONSHIP LINEUPS COMPLETE!")
        logger.info("="*60)
        logger.info("✅ All lineups use ONLY confirmed starting players")
        logger.info("🚫 NO NS/PO players should appear in these lineups")
        logger.info("📁 Upload SMART_CHAMPIONSHIP_LINEUPS.csv to FanDuel")
        
    except Exception as e:
        logger.error(f"❌ Smart championship builder error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
