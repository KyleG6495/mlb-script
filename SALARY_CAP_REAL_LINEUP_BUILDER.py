#!/usr/bin/env python3
"""
SALARY CAP COMPLIANT REAL PLAYERS LINEUP BUILDER
Build FanDuel lineups using ONLY players who are actually playing AND stay under $35K
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from itertools import combinations

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_confirmed_lineups():
    """Load confirmed starting lineups from RotoWire data for July 30, 2025"""
    # These are the ACTUAL confirmed lineups from RotoWire for July 30, 2025
    confirmed_games = {
        'TB@NYY': {
            'pitchers': {
                'TB': ['Ryan Pepiot', 'Pepiot'],
                'NYY': ['Marcus Stroman', 'Stroman']
            },
            'lineup_players': [
                # TB Rays lineup
                'Chandler Simpson', 'Simpson', 'Brandon Lowe', 'Lowe', 'Yandy Diaz', 'Diaz',
                'Jonathan Aranda', 'Aranda', 'Junior Caminero', 'Caminero', 'Josh Lowe',
                'Jake Mangum', 'Mangum', 'Nick Fortes', 'Fortes', 'Taylor Walls', 'Walls',
                # NYY Yankees lineup  
                'Trent Grisham', 'Grisham', 'Ben Rice', 'Rice', 'Cody Bellinger', 'Bellinger',
                'Giancarlo Stanton', 'Stanton', 'Jazz Chisholm', 'Chisholm', 'Jasson Dominguez', 'Dominguez',
                'Ryan McMahon', 'McMahon', 'Anthony Volpe', 'Volpe', 'Austin Wells', 'Wells'
            ]
        },
        'ATL@CIN': {
            'pitchers': {
                'ATL': ['Carlos Carrasco', 'Carrasco'],
                'CIN': ['Andrew Abbott', 'Abbott']
            },
            'lineup_players': [
                # ATL Braves lineup
                'Jurickson Profar', 'Profar', 'Matt Olson', 'Olson', 'Austin Riley', 'Riley',
                'Michael Harris', 'Harris', 'Marcell Ozuna', 'Ozuna', 'Ozzie Albies', 'Albies',
                'Sean Murphy', 'Murphy', 'Eli White', 'White', 'Nick Allen', 'Allen',
                # CIN Reds lineup
                'Gavin Lux', 'Lux', 'Matt McLain', 'McLain', 'Elly De La Cruz', 'De La Cruz',
                'Austin Hays', 'Hays', 'Jake Fraley', 'Fraley', 'Spencer Steer', 'Steer',
                'Tyler Stephenson', 'Stephenson', 'Will Benson', 'Benson', 'Kebryan Hayes', 'Hayes'
            ]
        },
        'TEX@SEA': {
            'pitchers': {
                'TEX': ['Kumar Rocker', 'Rocker'],
                'SEA': ['George Kirby', 'Kirby']
            },
            'lineup_players': [
                # TEX Rangers lineup
                'Josh Smith', 'Smith', 'Corey Seager', 'Seager', 'Marcus Semien', 'Semien',
                'Adolis Garcia', 'Garcia', 'Joc Pederson', 'Pederson', 'Wyatt Langford', 'Langford',
                'Evan Carter', 'Carter', 'Josh Jung', 'Jung', 'Kyle Higashioka', 'Higashioka',
                # SEA Mariners lineup
                'JP Crawford', 'Crawford', 'Julio Rodriguez', 'Rodriguez', 'Cal Raleigh', 'Raleigh',
                'Eugenio Suarez', 'Suarez', 'Josh Naylor', 'Naylor', 'Randy Arozarena', 'Arozarena',
                'Jorge Polanco', 'Polanco', 'Dominic Canzone', 'Canzone', 'Cole Young', 'Young'
            ]
        }
    }
    return confirmed_games

def validate_real_players(df, confirmed_lineups):
    """Validate which players from FD slate are actually playing TODAY"""
    logger.info(" VALIDATING REAL PLAYERS FOR JULY 30, 2025...")
    
    real_players = []
    all_confirmed_names = []
    
    # Collect all confirmed player names and variants
    for game, data in confirmed_lineups.items():
        # Add pitchers
        for team_pitchers in data['pitchers'].values():
            all_confirmed_names.extend(team_pitchers)
        # Add lineup players
        all_confirmed_names.extend(data['lineup_players'])
    
    logger.info(f"INFO: Total confirmed names/variants: {len(all_confirmed_names)}")
    
    # Match FD players with confirmed names using multiple matching strategies
    for idx, player in df.iterrows():
        full_name = f"{player['First Name']} {player['Last Name']}"
        nickname_name = f"{player['Nickname']} {player['Last Name']}"
        last_name = player['Last Name']
        first_name = player['First Name']
        nickname = player['Nickname']
        
        # Multiple matching strategies
        is_confirmed = False
        
        # Strategy 1: Exact full name match
        if full_name in all_confirmed_names or nickname_name in all_confirmed_names:
            is_confirmed = True
            
        # Strategy 2: Last name match with first name or nickname
        elif any(last_name in confirmed_name and (first_name in confirmed_name or nickname in confirmed_name) 
                for confirmed_name in all_confirmed_names):
            is_confirmed = True
            
        # Strategy 3: Unique last name match (for distinctive names)
        elif len([name for name in all_confirmed_names if last_name in name]) == 1:
            is_confirmed = True
            
        # Strategy 4: Special cases for common names
        elif last_name in ['Abbott', 'Raleigh', 'Bellinger', 'Rodriguez', 'Garcia', 'Smith']:
            # Be more specific for common names
            if any(f"{first_name} {last_name}" == confirmed_name or f"{nickname} {last_name}" == confirmed_name 
                   for confirmed_name in all_confirmed_names):
                is_confirmed = True
        
        if is_confirmed:
            real_players.append({
                'fd_id': player['Id'],
                'name': nickname_name,
                'position': player['Position'],
                'salary': player['Salary'],
                'fppg': player['FPPG'],
                'team': player['Team'],
                'opponent': player['Opponent'],
                'game': player['Game'],
                'value': player['FPPG'] / (player['Salary'] / 1000) if player['Salary'] > 0 else 0
            })
    
    real_df = pd.DataFrame(real_players)
    logger.info(f"SUCCESS: MATCHED {len(real_df)} CONFIRMED REAL PLAYERS from FD slate")
    
    # Show some matches for verification
    if len(real_df) > 0:
        logger.info("TARGET: Sample confirmed players:")
        for _, player in real_df.head(10).iterrows():
            logger.info(f"   {player['name']} ({player['position']}) - ${player['salary']} - {player['fppg']:.1f} FPPG")
    
    return real_df

def optimize_lineup_with_salary_cap(real_players_df, salary_cap=35000):
    """Build salary-cap compliant lineup using optimization"""
    logger.info(f"LINEUP: OPTIMIZING LINEUP WITH ${salary_cap:,} SALARY CAP...")
    
    if len(real_players_df) == 0:
        logger.error("ERROR: No real players found - cannot build lineup")
        return None, 0, 0
    
    # Separate by position
    pitchers = real_players_df[real_players_df['position'] == 'P'].copy()
    catchers = real_players_df[real_players_df['position'].str.contains('C')].copy()
    first_base = real_players_df[real_players_df['position'].str.contains('1B')].copy()
    second_base = real_players_df[real_players_df['position'].str.contains('2B')].copy()
    third_base = real_players_df[real_players_df['position'].str.contains('3B')].copy()
    shortstop = real_players_df[real_players_df['position'].str.contains('SS')].copy()
    outfield = real_players_df[real_players_df['position'].str.contains('OF')].copy()
    
    logger.info(f"TARGET: Position breakdown:")
    logger.info(f"   P: {len(pitchers)} players")
    logger.info(f"   C: {len(catchers)} players")
    logger.info(f"   1B: {len(first_base)} players")
    logger.info(f"   2B: {len(second_base)} players")
    logger.info(f"   3B: {len(third_base)} players")
    logger.info(f"   SS: {len(shortstop)} players")
    logger.info(f"   OF: {len(outfield)} players")
    
    best_lineup = None
    best_fppg = 0
    best_salary = 0
    
    # Try different pitcher options to optimize
    pitcher_options = pitchers.nlargest(5, 'fppg') if len(pitchers) >= 5 else pitchers
    
    for _, pitcher in pitcher_options.iterrows():
        remaining_budget = salary_cap - pitcher['salary']
        
        # Greedy optimization for remaining positions
        current_lineup = [('P', pitcher)]
        current_salary = pitcher['salary']
        current_fppg = pitcher['fppg']
        
        # Get best value players for each position within budget
        positions_needed = [
            ('C', catchers),
            ('1B', first_base),
            ('2B', second_base),
            ('3B', third_base),
            ('SS', shortstop)
        ]
        
        # Fill required positions
        for pos_name, pos_players in positions_needed:
            if len(pos_players) == 0:
                continue
                
            # Find best value player that fits budget
            affordable = pos_players[pos_players['salary'] <= remaining_budget]
            if len(affordable) > 0:
                best_player = affordable.loc[affordable['value'].idxmax()]
                current_lineup.append((pos_name, best_player))
                current_salary += best_player['salary']
                current_fppg += best_player['fppg']
                remaining_budget -= best_player['salary']
        
        # Fill 3 OF positions
        of_count = 0
        affordable_of = outfield[outfield['salary'] <= remaining_budget].copy()
        
        while of_count < 3 and len(affordable_of) > 0:
            best_of = affordable_of.loc[affordable_of['value'].idxmax()]
            current_lineup.append((f'OF', best_of))
            current_salary += best_of['salary']
            current_fppg += best_of['fppg']
            remaining_budget -= best_of['salary']
            of_count += 1
            
            # Remove this player from consideration and update affordable list
            affordable_of = affordable_of[affordable_of['fd_id'] != best_of['fd_id']]
            affordable_of = affordable_of[affordable_of['salary'] <= remaining_budget]
        
        # Check if this is our best lineup so far
        if len(current_lineup) == 9 and current_salary <= salary_cap and current_fppg > best_fppg:
            best_lineup = current_lineup
            best_fppg = current_fppg
            best_salary = current_salary
    
    if best_lineup:
        logger.info("=" * 60)
        logger.info("LINEUP: OPTIMIZED LINEUP:")
        for pos, player in best_lineup:
            logger.info(f"TARGET: {pos}: {player['name']} (${player['salary']}) - {player['fppg']:.1f} FPPG")
        
        logger.info("=" * 60)
        logger.info(f"MONEY: TOTAL SALARY: ${best_salary:,} / ${salary_cap:,}")
        logger.info(f"DATA: TOTAL PROJECTED FPPG: {best_fppg:.1f}")
        logger.info(f"OWNERSHIP: LINEUP SIZE: {len(best_lineup)}")
        logger.info(f" SALARY REMAINING: ${salary_cap - best_salary:,}")
    else:
        logger.error("ERROR: Could not build salary-cap compliant lineup")
    
    return best_lineup, best_salary, best_fppg

def save_real_lineup(lineup, total_salary, total_fppg):
    """Save the real players lineup to CSV in FanDuel format"""
    if not lineup:
        logger.error("ERROR: No lineup to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create FanDuel submission format
    fanduel_lineup = []
    for pos, player in lineup:
        fanduel_lineup.append({
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
            'Opponent': player['opponent'],
            'Injury Indicator': '',
            'Injury Details': '',
            'Tier': '',
            'Rostership %': '',
            'Probable Pitcher': '',
            'lineup_id': 1,
            'strategy': 'real_players_only'
        })
    
    lineup_df = pd.DataFrame(fanduel_lineup)
    
    # Save in FanDuel format
    filename = f"../data/FANDUEL_REAL_PLAYERS_LINEUP_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    logger.info(f" Saved FanDuel format lineup: {filename}")
    
    # Create summary
    summary = {
        'Total_Salary': total_salary,
        'Total_FPPG': total_fppg,
        'Players_Count': len(lineup),
        'Salary_Remaining': 35000 - total_salary,
        'Created': timestamp,
        'Strategy': 'Real Players Only - July 30, 2025'
    }
    
    summary_filename = f"../data/REAL_PLAYERS_SUMMARY_{timestamp}.csv"
    pd.DataFrame([summary]).to_csv(summary_filename, index=False)
    logger.info(f"INFO: Saved summary: {summary_filename}")
    
    return filename

def main():
    """Main function to build salary-cap compliant real players lineup"""
    logger.info("START: SALARY CAP COMPLIANT REAL PLAYERS LINEUP BUILDER")
    logger.info(" Building lineup for July 30, 2025 ONLY")
    logger.info("=" * 60)
    
    try:
        # Load confirmed lineups from RotoWire for July 30, 2025
        confirmed_lineups = load_confirmed_lineups()
        logger.info(f"INFO: Loaded {len(confirmed_lineups)} confirmed games for July 30, 2025")
        
        # Load FanDuel slate
        logger.info(" Loading FanDuel slate...")
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"DATA: Loaded {len(fd_df)} total players from FD slate")
        
        # Validate real players
        real_players_df = validate_real_players(fd_df, confirmed_lineups)
        
        if len(real_players_df) == 0:
            logger.error("ERROR: No real players found - check RotoWire lineup data")
            return
        
        # Build salary-cap compliant lineup
        lineup, total_salary, total_fppg = optimize_lineup_with_salary_cap(real_players_df)
        
        if lineup and len(lineup) == 9:
            # Save lineup
            filename = save_real_lineup(lineup, total_salary, total_fppg)
            
            logger.info("=" * 60)
            logger.info("COMPLETE: REAL PLAYERS LINEUP COMPLETE!")
            logger.info(f" Saved to: {filename}")
            logger.info("TARGET: This lineup contains ONLY players confirmed to be playing July 30, 2025!")
            logger.info(f"MONEY: Under salary cap: ${35000 - total_salary:,} remaining")
            logger.info(f"DATA: Projected FPPG: {total_fppg:.1f}")
        else:
            logger.error("ERROR: Failed to build complete 9-player lineup under salary cap")
            logger.error("TIP: Possible issues:")
            logger.error("   - Not enough confirmed players in each position")
            logger.error("   - Salary constraints too tight with available players")
            
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
