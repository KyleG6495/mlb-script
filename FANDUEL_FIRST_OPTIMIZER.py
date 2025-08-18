#!/usr/bin/env python3
"""
FANDUEL-FIRST OPTIMIZER
=======================
Optimizes lineups starting with FanDuel's available players only
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def optimize_from_fanduel_slate():
    """Start with FanDuel slate and build optimized lineups from there"""
    
    logger.info("TARGET: FANDUEL-FIRST OPTIMIZATION")
    logger.info("=" * 50)
    
    # START with FanDuel slate as master list
    fd_slate_file = "../fd_current_slate/fd_slate_today.csv"
    df_slate = pd.read_csv(fd_slate_file)
    
    logger.info(f"SUCCESS: FanDuel Slate Master List: {len(df_slate)} players")
    logger.info(f"DATA: Games: {len(df_slate['Game'].unique())} games")
    logger.info(f"DATA: Positions: {df_slate['Position'].value_counts().to_dict()}")
    
    # Load our enhanced ML data to match with FanDuel players
    try:
        enhanced_hitters = pd.read_csv("../data/aggregated_hitter_features_2025.csv")
        logger.info(f"SUCCESS: Loaded enhanced hitter data: {len(enhanced_hitters)} rows")
    except:
        logger.warning("WARNING: No enhanced hitter data found")
        enhanced_hitters = pd.DataFrame()
    
    try:
        enhanced_pitchers = pd.read_csv("../data/aggregated_pitcher_features_2025.csv")
        logger.info(f"SUCCESS: Loaded enhanced pitcher data: {len(enhanced_pitchers)} rows")
    except:
        logger.warning("WARNING: No enhanced pitcher data found")
        enhanced_pitchers = pd.DataFrame()
    
    try:
        ml_projections = pd.read_csv("../data/ml_enhanced_projections_20250812.csv")
        logger.info(f"SUCCESS: Loaded ML projections: {len(ml_projections)} rows")
    except:
        logger.warning("WARNING: No ML projections found")
        ml_projections = pd.DataFrame()
    
    try:
        weather_data = pd.read_csv("../data/weather_park_enhanced_players_20250812.csv")
        logger.info(f"SUCCESS: Loaded weather/park data: {len(weather_data)} rows")
    except:
        logger.warning("WARNING: No weather data found")
        weather_data = pd.DataFrame()
    
    # Create FanDuel-constrained dataset
    fanduel_players = []
    
    for _, player in df_slate.iterrows():
        # Try to match with our enhanced ML data
        ml_projection = 0
        weather_boost = 1.0
        
        # Match with ML projections
        if not ml_projections.empty:
            ml_match = ml_projections[ml_projections['name'].str.contains(player['Nickname'], na=False, case=False)]
            if len(ml_match) > 0:
                ml_projection = ml_match.iloc[0].get('ml_projected_fppg', 0)
        
        # Match with weather/park data
        if not weather_data.empty:
            weather_match = weather_data[weather_data['name'].str.contains(player['Nickname'], na=False, case=False)]
            if len(weather_match) > 0:
                weather_boost = weather_match.iloc[0].get('park_boost', 1.0)
        
        # Match with historical data for baseline
        baseline_fppg = player.get('FPPG', 0)
        if player['Position'] == 'P' and not enhanced_pitchers.empty:
            pitcher_match = enhanced_pitchers[enhanced_pitchers['name'].str.contains(player['Nickname'], na=False, case=False)]
            if len(pitcher_match) > 0:
                baseline_fppg = pitcher_match.iloc[0].get('avg_fppg_l15', baseline_fppg)
        elif player['Position'] != 'P' and not enhanced_hitters.empty:
            hitter_match = enhanced_hitters[enhanced_hitters['name'].str.contains(player['Nickname'], na=False, case=False)]
            if len(hitter_match) > 0:
                baseline_fppg = hitter_match.iloc[0].get('avg_fppg_l15', baseline_fppg)
        
        # Final projection: Use ML if available, otherwise enhanced baseline with weather
        final_projection = ml_projection if ml_projection > 0 else (baseline_fppg * weather_boost)
        
        player_data = {
            'fanduel_id': player['Id'],
            'name': player['Nickname'],
            'position': player['Position'],
            'salary': player['Salary'],
            'team': player['Team'],
            'opponent': player['Opponent'],
            'game': player['Game'],
            'fppg_baseline': baseline_fppg,
            'ml_projected_fppg': ml_projection,
            'weather_boost': weather_boost,
            'projected_fppg': final_projection,
            'value_score': (final_projection * 1000) / player['Salary'] if player['Salary'] > 0 else 0
        }
        
        fanduel_players.append(player_data)
    
    df_fanduel = pd.DataFrame(fanduel_players)
    
    logger.info(f"SUCCESS: FanDuel-Enhanced Dataset: {len(df_fanduel)} players")
    
    # Show top value plays by position
    logger.info("\n TOP VALUE PLAYS BY POSITION:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        pos_players = df_fanduel[df_fanduel['position'] == pos].nlargest(3, 'value_score')
        if len(pos_players) > 0:
            logger.info(f"  {pos}: {pos_players.iloc[0]['name']} (${pos_players.iloc[0]['salary']}, {pos_players.iloc[0]['projected_fppg']:.1f} FPPG)")
    
    # Generate multiple optimized lineups
    lineups = []
    for i in range(5):  # Generate 5 lineups
        lineup = optimize_single_lineup(df_fanduel, used_in_previous=lineups)
        if lineup:
            lineups.append(lineup)
            logger.info(f"\nLINEUP: LINEUP {i+1}:")
            display_lineup(lineup, i+1)
    
    # Save all lineups
    if lineups:
        save_multiple_lineups(lineups)
        return lineups
    
    return None

def display_lineup(lineup, lineup_num):
    """Display a lineup in a nice format"""
    total_salary = 0
    total_projection = 0
    
    for pos, player in lineup.items():
        logger.info(f"  {pos:>4}: {player['name']:<20} | ${player['salary']:<5} | {player['projected_fppg']:.1f} FPPG")
        total_salary += player['salary']
        total_projection += player['projected_fppg']
    
    logger.info(f"  MONEY: Total: ${total_salary:,} | DATA: Projection: {total_projection:.1f} FPPG")

def optimize_single_lineup(df_players, used_in_previous=[]):
    """Optimize a single lineup using advanced value-based selection"""
    
    # Get players already used in previous lineups
    used_players = set()
    for lineup in used_in_previous:
        for _, player in lineup.items():
            used_players.add(player['name'])
    
    lineup = {}
    remaining_salary = 35000
    
    # Enhanced position requirements with flexibility
    positions_needed = {
        'P': 1,
        'C': 1, 
        '1B': 1,
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3
    }
    
    # Sort by value score but add some randomization for lineup diversity
    df_available = df_players[~df_players['name'].isin(used_players)].copy()
    
    # Add slight randomization to avoid identical lineups
    np.random.seed(len(used_in_previous))
    df_available['randomized_value'] = df_available['value_score'] * np.random.uniform(0.9, 1.1, len(df_available))
    df_sorted = df_available.sort_values('randomized_value', ascending=False)
    
    used_in_lineup = set()  # Track players used in this specific lineup
    
    for position, count in positions_needed.items():
        position_players = df_sorted[
            (df_sorted['position'] == position) & 
            (~df_sorted['name'].isin(used_in_lineup)) &
            (df_sorted['salary'] <= remaining_salary)
        ].head(count * 5)  # Get more options for diversity
        
        for i in range(count):
            if len(position_players) > i:
                best_player = position_players.iloc[i]
                lineup[f"{position}_{i+1}" if count > 1 else position] = {
                    'name': best_player['name'],
                    'fanduel_id': best_player['fanduel_id'],
                    'position': best_player['position'],
                    'salary': best_player['salary'],
                    'projected_fppg': best_player['projected_fppg'],
                    'team': best_player['team'],
                    'weather_boost': best_player['weather_boost']
                }
                used_in_lineup.add(best_player['name'])
                remaining_salary -= best_player['salary']
    
    # Add UTIL (best remaining player that fits)
    remaining_players = df_sorted[
        (~df_sorted['name'].isin(used_in_lineup)) &
        (df_sorted['salary'] <= remaining_salary)
    ]
    
    if len(remaining_players) > 0:
        util_player = remaining_players.iloc[0]
        lineup['UTIL'] = {
            'name': util_player['name'],
            'fanduel_id': util_player['fanduel_id'],
            'position': util_player['position'],
            'salary': util_player['salary'],
            'projected_fppg': util_player['projected_fppg'],
            'team': util_player['team'],
            'weather_boost': util_player['weather_boost']
        }
    
    return lineup

def save_multiple_lineups(lineups):
    """Save multiple optimized lineups in FanDuel format"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    all_submission_rows = []
    
    for lineup in lineups:
        # Create submission row for this lineup
        submission_row = ['', '', '', '', '', '', '', '', '']  # 9 positions
        
        # Fill positions
        for key, player in lineup.items():
            if key == 'P':
                submission_row[0] = player['fanduel_id']
            elif key == 'C':
                submission_row[1] = player['fanduel_id']  # C/1B
            elif key == '1B':
                if not submission_row[1]:  # If C/1B empty
                    submission_row[1] = player['fanduel_id']  # Use C/1B
                else:
                    submission_row[8] = player['fanduel_id']  # Use UTIL
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
                if not submission_row[8]:  # If UTIL not filled
                    submission_row[8] = player['fanduel_id']
        
        all_submission_rows.append(submission_row)
    
    # Save to CSV
    df_submission = pd.DataFrame(all_submission_rows, 
                               columns=['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL'])
    
    output_file = f"../data/FANDUEL_ML_ENHANCED_LINEUPS_{timestamp}.csv"
    df_submission.to_csv(output_file, index=False)
    
    logger.info(f"\n Saved {len(lineups)} lineups: {output_file}")
    return output_file

def save_fanduel_lineup(lineup):
    """Save optimized lineup in FanDuel format"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create submission row
    submission_row = ['', '', '', '', '', '', '', '', '']  # 9 positions
    
    position_map = {
        'P': 0,
        'C': 1,  # Will go to C/1B
        '1B': 8,  # Will go to UTIL if C exists
        '2B': 2,
        '3B': 3,
        'SS': 4,
        'OF_1': 5,
        'OF_2': 6,
        'OF_3': 7
    }
    
    # Fill positions
    for key, player in lineup.items():
        if key == 'P':
            submission_row[0] = player['fanduel_id']
        elif key == 'C':
            submission_row[1] = player['fanduel_id']  # C/1B
        elif key == '1B':
            submission_row[8] = player['fanduel_id']  # UTIL
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
            if not submission_row[8]:  # If UTIL not filled by 1B
                submission_row[8] = player['fanduel_id']
    
    # Save to CSV
    df_submission = pd.DataFrame([submission_row], 
                               columns=['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL'])
    
    output_file = f"../data/FANDUEL_FIRST_OPTIMIZED_{timestamp}.csv"
    df_submission.to_csv(output_file, index=False)
    
    logger.info(f" Saved: {output_file}")
    return output_file

if __name__ == "__main__":
    optimize_from_fanduel_slate()
