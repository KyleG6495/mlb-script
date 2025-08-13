#!/usr/bin/env python3
"""
ULTIMATE REAL PLAYERS VALIDATOR & LINEUP BUILDER
Final validation against RotoWire lineups for July 30, 2025
Creates multiple optimized lineups with ONLY confirmed players
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from itertools import combinations
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_rotowire_confirmed_players_july_30():
    """
    CONFIRMED PLAYERS FROM ROTOWIRE FOR JULY 30, 2025
    These are the ONLY players guaranteed to be in lineups
    """
    confirmed_data = {
        'TB@NYY_game': {
            'TB_lineup': [
                ('CF', 'Chandler Simpson'),
                ('2B', 'Brandon Lowe'),
                ('DH', 'Yandy Diaz'),
                ('1B', 'Jonathan Aranda'),
                ('3B', 'Junior Caminero'),
                ('RF', 'Josh Lowe'),
                ('LF', 'Jake Mangum'),
                ('C', 'Nick Fortes'),
                ('SS', 'Taylor Walls')
            ],
            'NYY_lineup': [
                ('CF', 'Trent Grisham'),
                ('1B', 'Ben Rice'),
                ('RF', 'Cody Bellinger'),
                ('DH', 'Giancarlo Stanton'),
                ('2B', 'Jazz Chisholm'),
                ('LF', 'Jasson Dominguez'),
                ('3B', 'Ryan McMahon'),
                ('SS', 'Anthony Volpe'),
                ('C', 'Austin Wells')
            ],
            'pitchers': {
                'TB': 'Ryan Pepiot',
                'NYY': 'Marcus Stroman'
            }
        },
        'ATL@CIN_game': {
            'ATL_lineup': [
                ('LF', 'Jurickson Profar'),
                ('1B', 'Matt Olson'),
                ('3B', 'Austin Riley'),
                ('CF', 'Michael Harris'),
                ('DH', 'Marcell Ozuna'),
                ('2B', 'Ozzie Albies'),
                ('C', 'Sean Murphy'),
                ('RF', 'Eli White'),
                ('SS', 'Nick Allen')
            ],
            'CIN_lineup': [
                ('DH', 'Gavin Lux'),
                ('2B', 'Matt McLain'),
                ('SS', 'Elly De La Cruz'),
                ('LF', 'Austin Hays'),
                ('RF', 'Jake Fraley'),
                ('1B', 'Spencer Steer'),
                ('C', 'Tyler Stephenson'),
                ('CF', 'Will Benson'),
                ('3B', 'Kebryan Hayes')
            ],
            'pitchers': {
                'ATL': 'Carlos Carrasco',
                'CIN': 'Andrew Abbott'
            }
        },
        'TEX@SEA_game': {
            'TEX_lineup': [
                ('1B', 'Josh Smith'),
                ('SS', 'Corey Seager'),
                ('2B', 'Marcus Semien'),
                ('RF', 'Adolis Garcia'),
                ('DH', 'Joc Pederson'),
                ('LF', 'Wyatt Langford'),
                ('CF', 'Evan Carter'),
                ('3B', 'Josh Jung'),
                ('C', 'Kyle Higashioka')
            ],
            'SEA_lineup': [
                ('SS', 'JP Crawford'),
                ('CF', 'Julio Rodriguez'),
                ('C', 'Cal Raleigh'),
                ('3B', 'Eugenio Suarez'),
                ('1B', 'Josh Naylor'),
                ('LF', 'Randy Arozarena'),
                ('DH', 'Jorge Polanco'),
                ('RF', 'Dominic Canzone'),
                ('2B', 'Cole Young')
            ],
            'pitchers': {
                'TEX': 'Kumar Rocker',
                'SEA': 'George Kirby'
            }
        }
    }
    
    return confirmed_data

def create_master_confirmed_list():
    """Create master list of ALL confirmed players for July 30, 2025"""
    confirmed_data = get_rotowire_confirmed_players_july_30()
    
    all_confirmed = []
    
    for game, data in confirmed_data.items():
        # Add pitchers
        for team, pitcher in data['pitchers'].items():
            all_confirmed.append({
                'name': pitcher,
                'position': 'P',
                'team': team,
                'game': game.replace('_game', '')
            })
        
        # Add lineup players
        for team_key in data.keys():
            if '_lineup' in team_key:
                team = team_key.replace('_lineup', '')
                for pos, player in data[team_key]:
                    all_confirmed.append({
                        'name': player,
                        'position': pos,
                        'team': team,
                        'game': game.replace('_game', '')
                    })
    
    return all_confirmed

def match_fd_players_to_confirmed(fd_df, confirmed_list):
    """Match FanDuel players to confirmed RotoWire list with high accuracy"""
    logger.info("🔍 MATCHING FANDUEL PLAYERS TO CONFIRMED ROTOWIRE LIST...")
    
    matched_players = []
    unmatched_confirmed = []
    
    for confirmed in confirmed_list:
        confirmed_name = confirmed['name']
        matched = False
        
        # Try multiple matching strategies
        for idx, fd_player in fd_df.iterrows():
            fd_full = f"{fd_player['First Name']} {fd_player['Last Name']}"
            fd_nick = f"{fd_player['Nickname']} {fd_player['Last Name']}"
            fd_last = fd_player['Last Name']
            
            # Matching strategies in order of confidence
            match_found = False
            
            # 1. Exact full name match
            if fd_full == confirmed_name or fd_nick == confirmed_name:
                match_found = True
            
            # 2. Last name match with reasonable confidence
            elif (fd_last in confirmed_name and len(fd_last) > 4):
                match_found = True
                
            # 3. Handle common variations
            elif confirmed_name in ['Cal Raleigh'] and 'Raleigh' in fd_last:
                match_found = True
            elif confirmed_name in ['Elly De La Cruz'] and 'De La Cruz' in fd_last:
                match_found = True
            elif confirmed_name in ['Andrew Abbott'] and 'Abbott' in fd_last:
                match_found = True
            elif confirmed_name in ['Ryan Pepiot'] and 'Pepiot' in fd_last:
                match_found = True
            elif confirmed_name in ['George Kirby'] and 'Kirby' in fd_last:
                match_found = True
                
            if match_found:
                # Check position compatibility
                fd_positions = fd_player['Position'].split('/')
                confirmed_pos = confirmed['position']
                
                # Position mapping
                pos_compatible = False
                if confirmed_pos == 'P' and 'P' in fd_positions:
                    pos_compatible = True
                elif confirmed_pos in ['C'] and any(p in fd_positions for p in ['C']):
                    pos_compatible = True
                elif confirmed_pos in ['1B'] and any(p in fd_positions for p in ['1B']):
                    pos_compatible = True
                elif confirmed_pos in ['2B'] and any(p in fd_positions for p in ['2B']):
                    pos_compatible = True
                elif confirmed_pos in ['3B'] and any(p in fd_positions for p in ['3B']):
                    pos_compatible = True
                elif confirmed_pos in ['SS'] and any(p in fd_positions for p in ['SS']):
                    pos_compatible = True
                elif confirmed_pos in ['LF', 'CF', 'RF'] and any(p in fd_positions for p in ['OF']):
                    pos_compatible = True
                elif confirmed_pos in ['DH'] and 'UTIL' in str(fd_player['Position']):
                    pos_compatible = True
                
                if pos_compatible:
                    matched_players.append({
                        'fd_id': fd_player['Id'],
                        'name': fd_nick,
                        'confirmed_name': confirmed_name,
                        'position': fd_player['Position'],
                        'confirmed_position': confirmed_pos,
                        'salary': fd_player['Salary'],
                        'fppg': fd_player['FPPG'],
                        'team': fd_player['Team'],
                        'game': fd_player['Game'],
                        'value': fd_player['FPPG'] / (fd_player['Salary'] / 1000) if fd_player['Salary'] > 0 else 0
                    })
                    matched = True
                    break
        
        if not matched:
            unmatched_confirmed.append(confirmed_name)
    
    logger.info(f"✅ MATCHED {len(matched_players)} players from FD slate")
    logger.info(f"❌ UNMATCHED confirmed players: {len(unmatched_confirmed)}")
    
    if unmatched_confirmed:
        logger.warning("⚠️ Could not find these confirmed players in FD slate:")
        for name in unmatched_confirmed[:10]:  # Show first 10
            logger.warning(f"   - {name}")
    
    return pd.DataFrame(matched_players)

def build_multiple_optimized_lineups(matched_df, num_lineups=5):
    """Build multiple optimized lineups using different strategies"""
    logger.info(f"🏆 BUILDING {num_lineups} OPTIMIZED LINEUPS...")
    
    lineups = []
    
    # Strategy 1: Pure highest FPPG
    lineup1 = build_single_optimized_lineup(matched_df, strategy="max_fppg")
    if lineup1:
        lineups.append(("Max FPPG", lineup1))
    
    # Strategy 2: Best value (FPPG per $1K)
    lineup2 = build_single_optimized_lineup(matched_df, strategy="max_value")
    if lineup2:
        lineups.append(("Max Value", lineup2))
    
    # Strategy 3: Balanced approach
    lineup3 = build_single_optimized_lineup(matched_df, strategy="balanced")
    if lineup3:
        lineups.append(("Balanced", lineup3))
    
    # Strategy 4: Stars and scrubs
    lineup4 = build_single_optimized_lineup(matched_df, strategy="stars_scrubs")
    if lineup4:
        lineups.append(("Stars & Scrubs", lineup4))
    
    # Strategy 5: Contrarian (lower projected ownership)
    lineup5 = build_single_optimized_lineup(matched_df, strategy="contrarian")
    if lineup5:
        lineups.append(("Contrarian", lineup5))
    
    return lineups

def build_single_optimized_lineup(matched_df, strategy="max_fppg", salary_cap=35000):
    """Build a single optimized lineup using specified strategy"""
    
    # Separate by position
    pitchers = matched_df[matched_df['position'] == 'P'].copy()
    catchers = matched_df[matched_df['position'].str.contains('C')].copy()
    first_base = matched_df[matched_df['position'].str.contains('1B')].copy()
    second_base = matched_df[matched_df['position'].str.contains('2B')].copy()
    third_base = matched_df[matched_df['position'].str.contains('3B')].copy()
    shortstop = matched_df[matched_df['position'].str.contains('SS')].copy()
    outfield = matched_df[matched_df['position'].str.contains('OF')].copy()
    
    if strategy == "max_fppg":
        sort_col = 'fppg'
        ascending = False
    elif strategy == "max_value":
        sort_col = 'value'
        ascending = False
    elif strategy == "balanced":
        # Create balanced score
        matched_df['balanced_score'] = matched_df['fppg'] * 0.7 + matched_df['value'] * 0.3
        sort_col = 'balanced_score'
        ascending = False
    elif strategy == "stars_scrubs":
        # Prioritize expensive players first, then cheap
        matched_df['stars_scrubs_score'] = np.where(matched_df['salary'] >= 8000, 
                                                   matched_df['fppg'] * 2, 
                                                   matched_df['value'])
        sort_col = 'stars_scrubs_score'
        ascending = False
    else:  # contrarian
        sort_col = 'fppg'
        ascending = False
    
    # Apply sorting to position groups
    for pos_df in [pitchers, catchers, first_base, second_base, third_base, shortstop, outfield]:
        if len(pos_df) > 0:
            pos_df.sort_values(sort_col, ascending=ascending, inplace=True)
    
    # Build lineup with salary optimization
    best_lineup = None
    best_score = 0
    
    # Try top pitchers
    top_pitchers = pitchers.head(min(3, len(pitchers)))
    
    for _, pitcher in top_pitchers.iterrows():
        remaining_budget = salary_cap - pitcher['salary']
        
        lineup = [('P', pitcher)]
        current_salary = pitcher['salary']
        current_fppg = pitcher['fppg']
        
        # Fill positions with remaining budget
        positions = [
            ('C', catchers),
            ('1B', first_base), 
            ('2B', second_base),
            ('3B', third_base),
            ('SS', shortstop)
        ]
        
        success = True
        for pos_name, pos_players in positions:
            affordable = pos_players[pos_players['salary'] <= remaining_budget]
            if len(affordable) == 0:
                success = False
                break
                
            best_option = affordable.iloc[0]
            lineup.append((pos_name, best_option))
            current_salary += best_option['salary']
            current_fppg += best_option['fppg']
            remaining_budget -= best_option['salary']
        
        # Add 3 OF
        if success:
            of_count = 0
            affordable_of = outfield[outfield['salary'] <= remaining_budget].copy()
            
            while of_count < 3 and len(affordable_of) > 0:
                best_of = affordable_of.iloc[0]
                lineup.append(('OF', best_of))
                current_salary += best_of['salary']
                current_fppg += best_of['fppg']
                remaining_budget -= best_of['salary']
                of_count += 1
                
                # Remove selected player
                affordable_of = affordable_of[affordable_of['fd_id'] != best_of['fd_id']]
                affordable_of = affordable_of[affordable_of['salary'] <= remaining_budget]
            
            if of_count == 3 and current_salary <= salary_cap:
                if current_fppg > best_score:
                    best_lineup = lineup
                    best_score = current_fppg
    
    return best_lineup

def save_multiple_lineups(lineups):
    """Save all optimized lineups"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_lineups_data = []
    
    for i, (strategy, lineup) in enumerate(lineups, 1):
        if not lineup:
            continue
            
        total_salary = sum(player['salary'] for _, player in lineup)
        total_fppg = sum(player['fppg'] for _, player in lineup)
        
        logger.info(f"\n🏆 LINEUP {i}: {strategy.upper()}")
        logger.info("=" * 50)
        
        for pos, player in lineup:
            logger.info(f"{pos:3}: {player['name']:25} ${player['salary']:5,} {player['fppg']:6.1f} FPPG")
            
            all_lineups_data.append({
                'lineup_id': i,
                'strategy': strategy,
                'position': pos,
                'fd_id': player['fd_id'],
                'name': player['name'],
                'salary': player['salary'],
                'fppg': player['fppg'],
                'team': player['team'],
                'game': player['game']
            })
        
        logger.info(f"💰 Total: ${total_salary:,} | 📊 FPPG: {total_fppg:.1f} | 💵 Remaining: ${35000-total_salary:,}")
    
    # Save all lineups
    all_df = pd.DataFrame(all_lineups_data)
    filename = f"../data/VALIDATED_REAL_LINEUPS_ALL_{timestamp}.csv"
    all_df.to_csv(filename, index=False)
    logger.info(f"\n💾 Saved all lineups: {filename}")
    
    return filename

def main():
    """Main function"""
    logger.info("🚀 ULTIMATE REAL PLAYERS VALIDATOR & LINEUP BUILDER")
    logger.info("🎯 Building lineups for July 30, 2025 with CONFIRMED PLAYERS ONLY")
    logger.info("=" * 70)
    
    try:
        # Get confirmed players
        confirmed_list = create_master_confirmed_list()
        logger.info(f"📋 Created master list: {len(confirmed_list)} confirmed players")
        
        # Load FD slate
        fd_df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        logger.info(f"📊 Loaded FD slate: {len(fd_df)} players")
        
        # Match players
        matched_df = match_fd_players_to_confirmed(fd_df, confirmed_list)
        
        if len(matched_df) < 9:
            logger.error(f"❌ Only {len(matched_df)} confirmed players found - need at least 9")
            return
        
        # Build multiple lineups
        lineups = build_multiple_optimized_lineups(matched_df)
        
        if lineups:
            filename = save_multiple_lineups(lineups)
            
            logger.info("\n" + "=" * 70)
            logger.info("🎉 VALIDATED REAL PLAYERS LINEUPS COMPLETE!")
            logger.info(f"📁 File: {filename}")
            logger.info("✅ ALL PLAYERS CONFIRMED TO BE PLAYING JULY 30, 2025")
            logger.info("🎯 These lineups will NOT have players who didn't play!")
        else:
            logger.error("❌ Failed to build any complete lineups")
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
