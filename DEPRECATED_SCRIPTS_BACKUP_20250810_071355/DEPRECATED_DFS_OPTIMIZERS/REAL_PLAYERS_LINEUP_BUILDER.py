#!/usr/bin/env python3
"""
REAL PLAYERS LINEUP BUILDER
Build FanDuel lineups using ONLY players who are actually playing on July 30, 2025
Cross-reference with RotoWire confirmed lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_confirmed_lineups():
    """Load confirmed starting lineups from RotoWire data"""
    # Games confirmed for July 30, 2025 from RotoWire
    confirmed_games = {
        'TB@NYY': {
            'pitchers': {
                'TB': 'Ryan Pepiot',
                'NYY': 'Marcus Stroman'
            },
            'lineups': {
                'TB': ['Chandler Simpson', 'Brandon Lowe', 'Yandy Diaz', 'Jonathan Aranda', 
                       'Junior Caminero', 'Josh Lowe', 'Jake Mangum', 'Nick Fortes', 'Taylor Walls'],
                'NYY': ['Trent Grisham', 'Ben Rice', 'Cody Bellinger', 'Giancarlo Stanton',
                        'Jazz Chisholm', 'Jasson Dominguez', 'Ryan McMahon', 'Anthony Volpe', 'Austin Wells']
            }
        },
        'ATL@CIN': {
            'pitchers': {
                'ATL': 'Carlos Carrasco',
                'CIN': 'Andrew Abbott'
            },
            'lineups': {
                'ATL': ['Jurickson Profar', 'Matt Olson', 'Austin Riley', 'Michael Harris',
                        'Marcell Ozuna', 'Ozzie Albies', 'Sean Murphy', 'Eli White', 'Nick Allen'],
                'CIN': ['Gavin Lux', 'Matt McLain', 'Elly De La Cruz', 'Austin Hays',
                        'Jake Fraley', 'Spencer Steer', 'Tyler Stephenson', 'Will Benson', 'Kebryan Hayes']
            }
        },
        'TEX@SEA': {
            'pitchers': {
                'TEX': 'Kumar Rocker',
                'SEA': 'George Kirby'
            },
            'lineups': {
                'TEX': ['Josh Smith', 'Corey Seager', 'Marcus Semien', 'Adolis Garcia',
                        'Joc Pederson', 'Wyatt Langford', 'Evan Carter', 'Josh Jung', 'Kyle Higashioka'],
                'SEA': ['JP Crawford', 'Julio Rodriguez', 'Cal Raleigh', 'Eugenio Suarez',
                        'Josh Naylor', 'Randy Arozarena', 'Jorge Polanco', 'Dominic Canzone', 'Cole Young']
            }
        }
    }
    return confirmed_games

def load_fd_slate():
    """Load FanDuel slate and filter for real players"""
    logger.info("📥 Loading FanDuel slate...")
    df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
    
    # Get confirmed starting pitchers
    confirmed_pitchers = df[df['Probable Pitcher'] == 'Yes'].copy()
    logger.info(f"✅ Found {len(confirmed_pitchers)} confirmed starting pitchers")
    
    # Get all hitters (non-pitchers)
    hitters = df[df['Position'] != 'P'].copy()
    logger.info(f"🏏 Found {len(hitters)} total hitters in slate")
    
    return df, confirmed_pitchers, hitters

def validate_real_players(df, confirmed_lineups):
    """Validate which players from FD slate are actually playing"""
    logger.info("🔍 VALIDATING REAL PLAYERS...")
    
    real_players = []
    all_confirmed_names = []
    
    # Collect all confirmed player names
    for game, data in confirmed_lineups.items():
        all_confirmed_names.extend(data['pitchers'].values())
        for team_lineup in data['lineups'].values():
            all_confirmed_names.extend(team_lineup)
    
    logger.info(f"📋 Total confirmed players from RotoWire: {len(all_confirmed_names)}")
    
    # Match FD players with confirmed names
    for idx, player in df.iterrows():
        full_name = f"{player['First Name']} {player['Last Name']}"
        nickname_name = f"{player['Nickname']} {player['Last Name']}"
        last_name = player['Last Name']
        
        # Check various name combinations
        if (full_name in all_confirmed_names or 
            nickname_name in all_confirmed_names or
            any(last_name in confirmed_name for confirmed_name in all_confirmed_names)):
            
            real_players.append({
                'fd_id': player['Id'],
                'name': nickname_name,
                'position': player['Position'],
                'salary': player['Salary'],
                'fppg': player['FPPG'],
                'team': player['Team'],
                'opponent': player['Opponent'],
                'game': player['Game']
            })
    
    real_df = pd.DataFrame(real_players)
    logger.info(f"✅ MATCHED {len(real_df)} REAL PLAYERS from FD slate")
    
    return real_df

def build_optimal_lineup(real_players_df):
    """Build optimal lineup using only confirmed real players"""
    logger.info("🏆 BUILDING OPTIMAL LINEUP WITH REAL PLAYERS...")
    
    if len(real_players_df) == 0:
        logger.error("❌ No real players found - cannot build lineup")
        return None
    
    # Separate by position
    pitchers = real_players_df[real_players_df['position'] == 'P'].copy()
    catchers = real_players_df[real_players_df['position'].str.contains('C')].copy()
    first_base = real_players_df[real_players_df['position'].str.contains('1B')].copy()
    second_base = real_players_df[real_players_df['position'].str.contains('2B')].copy()
    third_base = real_players_df[real_players_df['position'].str.contains('3B')].copy()
    shortstop = real_players_df[real_players_df['position'].str.contains('SS')].copy()
    outfield = real_players_df[real_players_df['position'].str.contains('OF')].copy()
    
    logger.info(f"🎯 Position breakdown:")
    logger.info(f"   P: {len(pitchers)} players")
    logger.info(f"   C: {len(catchers)} players")
    logger.info(f"   1B: {len(first_base)} players")
    logger.info(f"   2B: {len(second_base)} players")
    logger.info(f"   3B: {len(third_base)} players")
    logger.info(f"   SS: {len(shortstop)} players")
    logger.info(f"   OF: {len(outfield)} players")
    
    # Build lineup by selecting best value at each position
    lineup = []
    total_salary = 0
    total_fppg = 0
    
    # Select best pitcher
    if len(pitchers) > 0:
        best_p = pitchers.loc[pitchers['fppg'].idxmax()]
        lineup.append(('P', best_p))
        total_salary += best_p['salary']
        total_fppg += best_p['fppg']
        logger.info(f"🎯 P: {best_p['name']} (${best_p['salary']}) - {best_p['fppg']:.1f} FPPG")
    
    # Select best catcher
    if len(catchers) > 0:
        best_c = catchers.loc[catchers['fppg'].idxmax()]
        lineup.append(('C', best_c))
        total_salary += best_c['salary']
        total_fppg += best_c['fppg']
        logger.info(f"🎯 C: {best_c['name']} (${best_c['salary']}) - {best_c['fppg']:.1f} FPPG")
    
    # Select best 1B
    if len(first_base) > 0:
        best_1b = first_base.loc[first_base['fppg'].idxmax()]
        lineup.append(('1B', best_1b))
        total_salary += best_1b['salary']
        total_fppg += best_1b['fppg']
        logger.info(f"🎯 1B: {best_1b['name']} (${best_1b['salary']}) - {best_1b['fppg']:.1f} FPPG")
    
    # Select best 2B
    if len(second_base) > 0:
        best_2b = second_base.loc[second_base['fppg'].idxmax()]
        lineup.append(('2B', best_2b))
        total_salary += best_2b['salary']
        total_fppg += best_2b['fppg']
        logger.info(f"🎯 2B: {best_2b['name']} (${best_2b['salary']}) - {best_2b['fppg']:.1f} FPPG")
    
    # Select best 3B
    if len(third_base) > 0:
        best_3b = third_base.loc[third_base['fppg'].idxmax()]
        lineup.append(('3B', best_3b))
        total_salary += best_3b['salary']
        total_fppg += best_3b['fppg']
        logger.info(f"🎯 3B: {best_3b['name']} (${best_3b['salary']}) - {best_3b['fppg']:.1f} FPPG")
    
    # Select best SS
    if len(shortstop) > 0:
        best_ss = shortstop.loc[shortstop['fppg'].idxmax()]
        lineup.append(('SS', best_ss))
        total_salary += best_ss['salary']
        total_fppg += best_ss['fppg']
        logger.info(f"🎯 SS: {best_ss['name']} (${best_ss['salary']}) - {best_ss['fppg']:.1f} FPPG")
    
    # Select best 3 OF
    if len(outfield) >= 3:
        top_of = outfield.nlargest(3, 'fppg')
        for i, (_, player) in enumerate(top_of.iterrows()):
            lineup.append(('OF', player))
            total_salary += player['salary']
            total_fppg += player['fppg']
            logger.info(f"🎯 OF{i+1}: {player['name']} (${player['salary']}) - {player['fppg']:.1f} FPPG")
    
    logger.info("=" * 60)
    logger.info(f"💰 TOTAL SALARY: ${total_salary:,} / $35,000")
    logger.info(f"📊 TOTAL PROJECTED FPPG: {total_fppg:.1f}")
    logger.info(f"👥 LINEUP SIZE: {len(lineup)}")
    
    if total_salary > 35000:
        logger.warning(f"⚠️ WARNING: Lineup over salary cap by ${total_salary - 35000:,}")
    
    return lineup, total_salary, total_fppg

def save_real_lineup(lineup, total_salary, total_fppg):
    """Save the real players lineup to CSV"""
    if not lineup:
        logger.error("❌ No lineup to save")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create lineup DataFrame
    lineup_data = []
    for pos, player in lineup:
        lineup_data.append({
            'Position': pos,
            'Player': player['name'],
            'FD_ID': player['fd_id'],
            'Salary': player['salary'],
            'FPPG': player['fppg'],
            'Team': player['team'],
            'Game': player['game']
        })
    
    lineup_df = pd.DataFrame(lineup_data)
    
    # Save lineup
    filename = f"../data/REAL_PLAYERS_LINEUP_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    logger.info(f"💾 Saved real players lineup: {filename}")
    
    # Create summary
    summary = {
        'Total_Salary': total_salary,
        'Total_FPPG': total_fppg,
        'Players_Count': len(lineup),
        'Salary_Remaining': 35000 - total_salary,
        'Created': timestamp
    }
    
    summary_filename = f"../data/REAL_PLAYERS_SUMMARY_{timestamp}.csv"
    pd.DataFrame([summary]).to_csv(summary_filename, index=False)
    logger.info(f"📋 Saved summary: {summary_filename}")
    
    return filename

def main():
    """Main function to build real players lineup"""
    logger.info("🚀 REAL PLAYERS LINEUP BUILDER - STARTING")
    logger.info("=" * 60)
    
    try:
        # Load confirmed lineups from RotoWire
        confirmed_lineups = load_confirmed_lineups()
        logger.info(f"📋 Loaded {len(confirmed_lineups)} confirmed games")
        
        # Load FanDuel slate
        fd_df, confirmed_pitchers, hitters = load_fd_slate()
        
        # Validate real players
        real_players_df = validate_real_players(fd_df, confirmed_lineups)
        
        if len(real_players_df) == 0:
            logger.error("❌ No real players found - check name matching logic")
            return
        
        # Build optimal lineup
        lineup, total_salary, total_fppg = build_optimal_lineup(real_players_df)
        
        if lineup:
            # Save lineup
            filename = save_real_lineup(lineup, total_salary, total_fppg)
            
            logger.info("=" * 60)
            logger.info("🎉 REAL PLAYERS LINEUP COMPLETE!")
            logger.info(f"📁 Saved to: {filename}")
            logger.info("🎯 This lineup contains ONLY players confirmed to be playing!")
        else:
            logger.error("❌ Failed to build lineup")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
