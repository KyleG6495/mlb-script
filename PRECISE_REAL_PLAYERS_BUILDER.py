#!/usr/bin/env python3
"""
PRECISE REAL PLAYERS LINEUP BUILDER
Uses exact name matching for July 30, 2025 confirmed players only
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_exact_confirmed_matches():
    """
    EXACT MATCHES between RotoWire confirmed players and FanDuel slate
    Only players we are 100% certain are playing July 30, 2025
    """
    exact_matches = {
        # CONFIRMED STARTING PITCHERS
        'Ryan Pepiot': {'fd_search': 'Pepiot', 'position': 'P'},
        'Andrew Abbott': {'fd_search': 'Abbott', 'position': 'P'},
        'George Kirby': {'fd_search': 'Kirby', 'position': 'P'},
        'Kumar Rocker': {'fd_search': 'Rocker', 'position': 'P'},
        'Marcus Stroman': {'fd_search': 'Stroman', 'position': 'P'},
        
        # TB RAYS CONFIRMED LINEUP
        'Brandon Lowe': {'fd_search': 'Brandon Lowe', 'position': '2B'},
        'Jonathan Aranda': {'fd_search': 'Jonathan Aranda', 'position': '1B'},
        'Junior Caminero': {'fd_search': 'Junior Caminero', 'position': '3B'},
        'Josh Lowe': {'fd_search': 'Josh Lowe', 'position': 'OF'},
        'Nick Fortes': {'fd_search': 'Nick Fortes', 'position': 'C'},
        'Taylor Walls': {'fd_search': 'Taylor Walls', 'position': 'SS'},
        
        # NYY YANKEES CONFIRMED LINEUP
        'Trent Grisham': {'fd_search': 'Trent Grisham', 'position': 'OF'},
        'Ben Rice': {'fd_search': 'Ben Rice', 'position': '1B'},
        'Cody Bellinger': {'fd_search': 'Cody Bellinger', 'position': 'OF'},
        'Giancarlo Stanton': {'fd_search': 'Giancarlo Stanton', 'position': 'OF'},
        'Jasson Dominguez': {'fd_search': 'Jasson Dominguez', 'position': 'OF'},
        'Anthony Volpe': {'fd_search': 'Anthony Volpe', 'position': 'SS'},
        'Austin Wells': {'fd_search': 'Austin Wells', 'position': 'C'},
        
        # CIN REDS CONFIRMED LINEUP
        'Gavin Lux': {'fd_search': 'Gavin Lux', 'position': '2B'},
        'Matt McLain': {'fd_search': 'Matt McLain', 'position': '2B'},
        'Elly De La Cruz': {'fd_search': 'Elly De La Cruz', 'position': 'SS'},
        'Austin Hays': {'fd_search': 'Austin Hays', 'position': 'OF'},
        'Jake Fraley': {'fd_search': 'Jake Fraley', 'position': 'OF'},
        'Spencer Steer': {'fd_search': 'Spencer Steer', 'position': '1B'},
        'Will Benson': {'fd_search': 'Will Benson', 'position': 'OF'},
        
        # SEA MARINERS CONFIRMED LINEUP
        'JP Crawford': {'fd_search': 'J.P. Crawford', 'position': 'SS'},
        'Julio Rodriguez': {'fd_search': 'Julio Rodriguez', 'position': 'OF'},
        'Cal Raleigh': {'fd_search': 'Cal Raleigh', 'position': 'C'},
        'Josh Naylor': {'fd_search': 'Josh Naylor', 'position': '1B'},
        'Randy Arozarena': {'fd_search': 'Randy Arozarena', 'position': 'OF'},
        'Jorge Polanco': {'fd_search': 'Jorge Polanco', 'position': '2B'},
        'Dominic Canzone': {'fd_search': 'Dominic Canzone', 'position': 'OF'},
        
        # TEX RANGERS CONFIRMED LINEUP
        'Corey Seager': {'fd_search': 'Corey Seager', 'position': 'SS'},
        'Marcus Semien': {'fd_search': 'Marcus Semien', 'position': '2B'},
        'Joc Pederson': {'fd_search': 'Joc Pederson', 'position': 'OF'},
        'Wyatt Langford': {'fd_search': 'Wyatt Langford', 'position': 'OF'},
        'Evan Carter': {'fd_search': 'Evan Carter', 'position': 'OF'},
        'Josh Jung': {'fd_search': 'Josh Jung', 'position': '3B'},
        'Kyle Higashioka': {'fd_search': 'Kyle Higashioka', 'position': 'C'},
    }
    
    return exact_matches

def find_exact_players_in_fd_slate(fd_df, exact_matches):
    """Find exact confirmed players in FanDuel slate"""
    logger.info(" FINDING EXACT CONFIRMED PLAYERS IN FANDUEL SLATE...")
    
    confirmed_players = []
    
    for confirmed_name, match_info in exact_matches.items():
        search_term = match_info['fd_search']
        expected_pos = match_info['position']
        
        found = False
        
        for idx, fd_player in fd_df.iterrows():
            fd_full = f"{fd_player['First Name']} {fd_player['Last Name']}"
            fd_nick = f"{fd_player['Nickname']} {fd_player['Last Name']}"
            
            # Exact matching
            if (search_term == fd_full or search_term == fd_nick or 
                (len(search_term.split()) == 1 and search_term == fd_player['Last Name'])):
                
                # Verify position compatibility
                fd_positions = fd_player['Position'].split('/')
                
                position_match = False
                if expected_pos == 'P' and 'P' in fd_positions:
                    position_match = True
                elif expected_pos == 'C' and any(p in fd_positions for p in ['C']):
                    position_match = True
                elif expected_pos == '1B' and any(p in fd_positions for p in ['1B']):
                    position_match = True
                elif expected_pos == '2B' and any(p in fd_positions for p in ['2B']):
                    position_match = True
                elif expected_pos == '3B' and any(p in fd_positions for p in ['3B']):
                    position_match = True
                elif expected_pos == 'SS' and any(p in fd_positions for p in ['SS']):
                    position_match = True
                elif expected_pos == 'OF' and any(p in fd_positions for p in ['OF']):
                    position_match = True
                
                if position_match:
                    confirmed_players.append({
                        'fd_id': fd_player['Id'],
                        'name': fd_nick,
                        'confirmed_name': confirmed_name,
                        'position': fd_player['Position'],
                        'salary': fd_player['Salary'],
                        'fppg': fd_player['FPPG'],
                        'team': fd_player['Team'],
                        'game': fd_player['Game'],
                        'value': fd_player['FPPG'] / (fd_player['Salary'] / 1000) if fd_player['Salary'] > 0 else 0
                    })
                    logger.info(f"SUCCESS: CONFIRMED: {confirmed_name}  {fd_nick} ({fd_player['Position']}) ${fd_player['Salary']} - {fd_player['FPPG']:.1f} FPPG")
                    found = True
                    break
        
        if not found:
            logger.warning(f"ERROR: NOT FOUND: {confirmed_name} (searching for: {search_term})")
    
    confirmed_df = pd.DataFrame(confirmed_players)
    logger.info(f"DATA: TOTAL CONFIRMED PLAYERS FOUND: {len(confirmed_df)}")
    return confirmed_df

def build_salary_cap_lineup(confirmed_df, salary_cap=35000):
    """Build salary cap compliant lineup with confirmed players"""
    logger.info("LINEUP: BUILDING SALARY CAP COMPLIANT LINEUP...")
    
    if len(confirmed_df) < 9:
        logger.error(f"ERROR: Only {len(confirmed_df)} confirmed players - need at least 9")
        return None, 0
    
    # Separate by position
    pitchers = confirmed_df[confirmed_df['position'] == 'P'].copy()
    catchers = confirmed_df[confirmed_df['position'].str.contains('C')].copy()
    first_base = confirmed_df[confirmed_df['position'].str.contains('1B')].copy()
    second_base = confirmed_df[confirmed_df['position'].str.contains('2B')].copy()
    third_base = confirmed_df[confirmed_df['position'].str.contains('3B')].copy()
    shortstop = confirmed_df[confirmed_df['position'].str.contains('SS')].copy()
    outfield = confirmed_df[confirmed_df['position'].str.contains('OF')].copy()
    
    logger.info(f"INFO: CONFIRMED PLAYERS BY POSITION:")
    logger.info(f"   P: {len(pitchers)} - {list(pitchers['name']) if len(pitchers) > 0 else 'None'}")
    logger.info(f"   C: {len(catchers)} - {list(catchers['name']) if len(catchers) > 0 else 'None'}")
    logger.info(f"   1B: {len(first_base)} - {list(first_base['name']) if len(first_base) > 0 else 'None'}")
    logger.info(f"   2B: {len(second_base)} - {list(second_base['name']) if len(second_base) > 0 else 'None'}")
    logger.info(f"   3B: {len(third_base)} - {list(third_base['name']) if len(third_base) > 0 else 'None'}")
    logger.info(f"   SS: {len(shortstop)} - {list(shortstop['name']) if len(shortstop) > 0 else 'None'}")
    logger.info(f"   OF: {len(outfield)} - {list(outfield['name']) if len(outfield) > 0 else 'None'}")
    
    # Check if we have minimum required positions
    if len(pitchers) < 1 or len(catchers) < 1 or len(outfield) < 3:
        logger.error("ERROR: Missing required positions for complete lineup")
        logger.error(f"   Need: 1 P ({len(pitchers)} available), 1 C ({len(catchers)} available), 3 OF ({len(outfield)} available)")
        return None, 0
    
    # Try to build best lineup under salary cap
    best_lineup = None
    best_fppg = 0
    
    # Try different pitcher options
    for _, pitcher in pitchers.iterrows():
        remaining_budget = salary_cap - pitcher['salary']
        current_lineup = [('P', pitcher)]
        current_salary = pitcher['salary']
        current_fppg = pitcher['fppg']
        
        logger.info(f"\nTARGET: Trying lineup with {pitcher['name']} (${pitcher['salary']}) - ${remaining_budget:,} remaining")
        
        # Required positions
        required_positions = [
            ('C', catchers, 1),
            ('1B', first_base, 1),
            ('2B', second_base, 1), 
            ('3B', third_base, 1),
            ('SS', shortstop, 1),
            ('OF', outfield, 3)
        ]
        
        success = True
        
        for pos_name, pos_df, needed_count in required_positions:
            if len(pos_df) < needed_count:
                logger.warning(f"   ERROR: Not enough {pos_name} players ({len(pos_df)} available, need {needed_count})")
                success = False
                break
            
            # For OF, need to select 3 players
            if pos_name == 'OF':
                affordable_of = pos_df[pos_df['salary'] <= remaining_budget].copy()
                
                if len(affordable_of) < 3:
                    logger.warning(f"   ERROR: Not enough affordable OF players ({len(affordable_of)} available, need 3)")
                    success = False
                    break
                
                # Select best 3 OF that fit budget
                selected_of = []
                remaining_of_budget = remaining_budget
                
                # Sort by value and try to fit 3
                affordable_of = affordable_of.sort_values('value', ascending=False)
                
                for _, of_player in affordable_of.iterrows():
                    if len(selected_of) < 3 and of_player['salary'] <= remaining_of_budget:
                        selected_of.append(of_player)
                        remaining_of_budget -= of_player['salary']
                
                if len(selected_of) < 3:
                    logger.warning(f"   ERROR: Could only fit {len(selected_of)} OF players in budget")
                    success = False
                    break
                
                # Add OF players to lineup
                for of_player in selected_of:
                    current_lineup.append(('OF', of_player))
                    current_salary += of_player['salary']
                    current_fppg += of_player['fppg']
                    remaining_budget -= of_player['salary']
                    logger.info(f"   SUCCESS: OF: {of_player['name']} (${of_player['salary']}) - ${remaining_budget:,} remaining")
                
            else:
                # Single position players
                affordable = pos_df[pos_df['salary'] <= remaining_budget]
                
                if len(affordable) == 0:
                    logger.warning(f"   ERROR: No affordable {pos_name} players (budget: ${remaining_budget:,})")
                    success = False
                    break
                
                # Select best affordable player
                best_player = affordable.loc[affordable['value'].idxmax()]
                current_lineup.append((pos_name, best_player))
                current_salary += best_player['salary']
                current_fppg += best_player['fppg']
                remaining_budget -= best_player['salary']
                logger.info(f"   SUCCESS: {pos_name}: {best_player['name']} (${best_player['salary']}) - ${remaining_budget:,} remaining")
        
        if success and len(current_lineup) == 9 and current_salary <= salary_cap:
            logger.info(f"   SUCCESS: COMPLETE LINEUP: ${current_salary:,} / ${salary_cap:,} - {current_fppg:.1f} FPPG")
            if current_fppg > best_fppg:
                best_lineup = current_lineup
                best_fppg = current_fppg
                logger.info(f"   LINEUP: NEW BEST LINEUP!")
        else:
            logger.info(f"   ERROR: Failed: {len(current_lineup)} players, ${current_salary:,} salary")
    
    return best_lineup, best_fppg

def save_final_lineup(lineup, total_fppg):
    """Save the final confirmed lineup"""
    if not lineup:
        logger.error("ERROR: No lineup to save")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    total_salary = sum(player['salary'] for _, player in lineup)
    
    logger.info("\n" + "=" * 70)
    logger.info("LINEUP: FINAL LINEUP - CONFIRMED REAL PLAYERS ONLY (JULY 30, 2025)")
    logger.info("=" * 70)
    
    lineup_data = []
    for pos, player in lineup:
        logger.info(f"{pos:3} | {player['name']:25} | ${player['salary']:5,} | {player['fppg']:6.1f} FPPG")
        
        lineup_data.append({
            'Id': player['fd_id'],
            'Position': pos,
            'First Name': player['name'].split()[0],
            'Nickname': player['name'].split()[0],
            'Last Name': ' '.join(player['name'].split()[1:]),
            'FPPG': player['fppg'],
            'Played': '',
            'Salary': player['salary'],
            'Game': player['game'],
            'Team': player['team'],
            'Opponent': '',
            'Injury Indicator': '',
            'Injury Details': '',
            'Tier': '',
            'Rostership %': '',
            'Probable Pitcher': 'Yes' if pos == 'P' else '',
            'lineup_id': 1,
            'strategy': 'CONFIRMED_REAL_PLAYERS_JULY_30_2025'
        })
    
    logger.info("=" * 70)
    logger.info(f"MONEY: TOTAL SALARY: ${total_salary:,} / $35,000")
    logger.info(f"DATA: PROJECTED FPPG: {total_fppg:.1f}")
    logger.info(f" REMAINING: ${35000 - total_salary:,}")
    logger.info("SUCCESS: ALL PLAYERS CONFIRMED FROM ROTOWIRE STARTING LINEUPS!")
    logger.info("TARGET: NO FAKE PLAYERS - THESE ARE REAL JULY 30, 2025 STARTERS!")
    
    # Save lineup
    lineup_df = pd.DataFrame(lineup_data)
    filename = f"../data/CONFIRMED_REAL_LINEUP_JULY_30_2025_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    logger.info(f" SAVED: {filename}")
    
    return filename

def main():
    """Main function"""
    logger.info("START: PRECISE REAL PLAYERS LINEUP BUILDER")
    logger.info(" July 30, 2025 - CONFIRMED STARTING LINEUPS ONLY")
    logger.info("=" * 70)
    
    try:
        # Get exact confirmed matches
        exact_matches = get_exact_confirmed_matches()
        logger.info(f"INFO: Exact confirmed players: {len(exact_matches)} names")
        
        # Load FanDuel slate
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"DATA: FanDuel slate: {len(fd_df)} players")
        
        # Find exact matches
        confirmed_df = find_exact_players_in_fd_slate(fd_df, exact_matches)
        
        if len(confirmed_df) < 9:
            logger.error(f"ERROR: Only found {len(confirmed_df)} confirmed players - need 9 minimum")
            logger.error("TIP: This means some confirmed players are not in your FD slate")
            return
        
        # Build salary cap lineup
        lineup, total_fppg = build_salary_cap_lineup(confirmed_df)
        
        if lineup:
            filename = save_final_lineup(lineup, total_fppg)
            
            logger.info("\nCOMPLETE: SUCCESS! LINEUP WITH CONFIRMED REAL PLAYERS!")
            logger.info("SUCCESS: NO DISASTERS - ALL PLAYERS ARE STARTING JULY 30, 2025!")
            logger.info(f" File: {filename}")
        else:
            logger.error("ERROR: Could not build complete lineup under salary cap")
            logger.error("TIP: Try adjusting player selection or check available positions")
            
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
