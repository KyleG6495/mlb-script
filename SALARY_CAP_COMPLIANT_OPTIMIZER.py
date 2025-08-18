#!/usr/bin/env python3
"""
SALARY CAP COMPLIANT OPTIMIZER
=============================
Creates ULTIMATE lineups that stay under $35,000 salary cap
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_salary_cap_compliant_lineups():
    """Create salary cap compliant versions of our ULTIMATE lineups"""
    
    logger.info("MONEY: CREATING SALARY CAP COMPLIANT LINEUPS")
    logger.info("=" * 60)
    
    # Load FanDuel slate
    df_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # Load our enhanced datasets
    try:
        df_weather = pd.read_csv("../data/real_weather_enhanced_20250812_171640.csv")
        logger.info(f"SUCCESS: Weather data loaded: {len(df_weather)} players")
    except:
        df_weather = pd.DataFrame()
        logger.warning("WARNING: No weather data")
    
    # Create enhanced player dataset
    players = []
    for _, player in df_slate.iterrows():
        player_name = player['Nickname']
        
        # Get weather boost
        weather_boost = 1.0
        if not df_weather.empty:
            match = df_weather[df_weather['name'].str.contains(player_name, na=False, case=False)]
            if len(match) > 0:
                weather_boost = match.iloc[0].get('weather_boost', 1.0)
        
        # Calculate enhanced projection
        base_fppg = player.get('FPPG', 0)
        enhanced_fppg = base_fppg * weather_boost
        value_score = (enhanced_fppg * 1000) / player['Salary'] if player['Salary'] > 0 else 0
        
        players.append({
            'fanduel_id': player['Id'],
            'name': player_name,
            'position': player['Position'],
            'salary': player['Salary'],
            'team': player['Team'],
            'enhanced_fppg': enhanced_fppg,
            'value_score': value_score,
            'weather_boost': weather_boost
        })
    
    df_players = pd.DataFrame(players)
    
    # Create 5 salary cap compliant lineups
    compliant_lineups = []
    strategies = ['BALANCED', 'VALUE', 'CEILING', 'CONTRARIAN', 'WEATHER']
    
    for i, strategy in enumerate(strategies):
        logger.info(f"\nTARGET: Creating {strategy} lineup (under $35,000)")
        
        lineup = create_cap_compliant_lineup(df_players, strategy, compliant_lineups)
        if lineup:
            compliant_lineups.append(lineup)
            display_compliant_lineup(lineup, strategy)
    
    # Save compliant lineups
    if compliant_lineups:
        save_compliant_lineups(compliant_lineups)
    
    return compliant_lineups

def create_cap_compliant_lineup(df_players, strategy, used_lineups):
    """Create a single salary cap compliant lineup"""
    
    # Get used players from previous lineups
    used_players = set()
    for lineup in used_lineups:
        for _, player in lineup.items():
            used_players.add(player['name'])
    
    # Filter available players
    df_available = df_players[~df_players['name'].isin(used_players)].copy()
    
    # Strategy-specific sorting
    if strategy == 'VALUE':
        df_sorted = df_available.sort_values('value_score', ascending=False)
    elif strategy == 'CEILING':
        df_sorted = df_available.sort_values('enhanced_fppg', ascending=False)
    elif strategy == 'CONTRARIAN':
        # Favor mid-tier players
        df_available['contrarian_score'] = df_available['enhanced_fppg'] / (df_available['salary'] / 1000) * np.random.uniform(0.8, 1.2, len(df_available))
        df_sorted = df_available.sort_values('contrarian_score', ascending=False)
    elif strategy == 'WEATHER':
        df_available['weather_score'] = df_available['enhanced_fppg'] * df_available['weather_boost']
        df_sorted = df_available.sort_values('weather_score', ascending=False)
    else:  # BALANCED
        df_available['balanced_score'] = df_available['value_score'] * (df_available['enhanced_fppg'] / 15)
        df_sorted = df_available.sort_values('balanced_score', ascending=False)
    
    # Build lineup with salary constraint
    lineup = {}
    remaining_salary = 35000
    positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    
    used_in_lineup = set()
    
    # Fill positions
    for position, count in positions_needed.items():
        position_players = df_sorted[
            (df_sorted['position'] == position) & 
            (~df_sorted['name'].isin(used_in_lineup)) &
            (df_sorted['salary'] <= remaining_salary - 2000)  # Leave room for other positions
        ]
        
        for i in range(count):
            if len(position_players) > i:
                player = position_players.iloc[i]
                key = f"{position}_{i+1}" if count > 1 else position
                
                lineup[key] = {
                    'name': player['name'],
                    'fanduel_id': player['fanduel_id'],
                    'position': player['position'],
                    'salary': player['salary'],
                    'enhanced_fppg': player['enhanced_fppg'],
                    'value_score': player['value_score'],
                    'team': player['team']
                }
                
                used_in_lineup.add(player['name'])
                remaining_salary -= player['salary']
    
    # Add UTIL with remaining salary
    util_players = df_sorted[
        (~df_sorted['name'].isin(used_in_lineup)) &
        (df_sorted['salary'] <= remaining_salary)
    ]
    
    if len(util_players) > 0:
        util_player = util_players.iloc[0]
        lineup['UTIL'] = {
            'name': util_player['name'],
            'fanduel_id': util_player['fanduel_id'],
            'position': util_player['position'],
            'salary': util_player['salary'],
            'enhanced_fppg': util_player['enhanced_fppg'],
            'value_score': util_player['value_score'],
            'team': util_player['team']
        }
    
    return lineup

def display_compliant_lineup(lineup, strategy):
    """Display a compliant lineup"""
    total_salary = sum(player['salary'] for player in lineup.values())
    total_projection = sum(player['enhanced_fppg'] for player in lineup.values())
    
    logger.info(f"  Strategy: {strategy}")
    for pos, player in lineup.items():
        logger.info(f"  {pos:>4}: {player['name']:<20} | ${player['salary']:<5} | {player['enhanced_fppg']:.1f} FPPG")
    
    logger.info(f"  MONEY: Total: ${total_salary:,} | DATA: Projection: {total_projection:.1f} FPPG")
    
    if total_salary > 35000:
        logger.warning(f"  WARNING: OVER SALARY CAP by ${total_salary - 35000}")
    else:
        logger.info(f"  SUCCESS: UNDER SALARY CAP (${35000 - total_salary} remaining)")

def save_compliant_lineups(lineups):
    """Save compliant lineups in FanDuel format"""
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create submission format
    submission_rows = []
    
    for lineup in lineups:
        submission_row = ['', '', '', '', '', '', '', '', '']
        
        for key, player in lineup.items():
            if key == 'P':
                submission_row[0] = player['fanduel_id']
            elif key == 'C':
                submission_row[1] = player['fanduel_id']
            elif key == '1B':
                if not submission_row[1]:
                    submission_row[1] = player['fanduel_id']
                else:
                    submission_row[8] = player['fanduel_id']
            elif key == '2B':
                submission_row[2] = player['fanduel_id']
            elif key == '3B':
                submission_row[3] = player['fanduel_id']
            elif key == 'SS':
                submission_row[4] = player['fanduel_id']
            elif key == 'OF_1':
                submission_row[5] = player['fanduel_id']
            elif key == 'OF_2':
                submission_row[6] = player['fanduel_id']
            elif key == 'OF_3':
                submission_row[7] = player['fanduel_id']
            elif key == 'UTIL':
                if not submission_row[8]:
                    submission_row[8] = player['fanduel_id']
        
        submission_rows.append(submission_row)
    
    # Save to CSV
    df_submission = pd.DataFrame(submission_rows, 
                               columns=['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL'])
    
    output_file = f"../data/SALARY_CAP_COMPLIANT_LINEUPS_{timestamp}.csv"
    df_submission.to_csv(output_file, index=False)
    
    logger.info(f"\n Salary cap compliant lineups saved: {output_file}")
    return output_file

if __name__ == "__main__":
    create_salary_cap_compliant_lineups()
