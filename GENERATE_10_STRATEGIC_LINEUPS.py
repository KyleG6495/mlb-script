#!/usr/bin/env python3
"""
GENERATE 10 STRATEGIC LINEUPS - Hybrid approach using refined 5-lineup methodology with variations
"""

import pandas as pd
import numpy as np
import random
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_filter_slate():
    """Load August 12th slate and apply proper filtering"""
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    
    try:
        df = pd.read_csv(slate_file)
        logger.info(f"Original slate size: {len(df)} players")
        
        # Step 1: Filter out injured players
        injury_indicators = ['IL', 'DTD', 'O']
        injured_players = df[df['Injury Indicator'].isin(injury_indicators)]
        logger.info(f"Players with injury indicators: {len(injured_players)}")
        
        healthy_df = df[~df['Injury Indicator'].isin(injury_indicators)]
        logger.info(f"Healthy players remaining: {len(healthy_df)}")
        
        # Step 2: Filter pitchers to probable only
        pitchers = healthy_df[healthy_df['Position'] == 'P']
        probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
        logger.info(f"Probable pitchers: {len(probable_pitchers)}")
        
        # Combine non-pitchers + probable pitchers
        non_pitchers = healthy_df[healthy_df['Position'] != 'P']
        filtered_df = pd.concat([non_pitchers, probable_pitchers], ignore_index=True)
        
        logger.info(f"FINAL FILTERED SLATE: {len(filtered_df)} players")
        logger.info(f"REMOVED: {len(df) - len(filtered_df)} unplayable players ({(len(df) - len(filtered_df))/len(df)*100:.1f}%)")
        
        return filtered_df
        
    except Exception as e:
        logger.error(f"Error loading slate: {e}")
        return None

def create_player_pools(df):
    """Create strategic player pools based on salary and position"""
    pools = {}
    
    # Value catchers ($2,200-$3,000)
    pools['value_catchers'] = df[(df['Position'] == 'C') & 
                                (df['Salary'] >= 2200) & (df['Salary'] <= 3000)].copy()
    
    # Power 1B ($3,000+)
    pools['power_1b'] = df[(df['Position'].str.contains('1B')) & 
                          (df['Salary'] >= 3000)].copy()
    
    # Value infielders ($2,200-$3,500)
    pools['value_infield'] = df[(df['Position'].isin(['2B', '3B', 'SS']) | 
                                df['Position'].str.contains('2B|3B|SS')) & 
                               (df['Salary'] >= 2200) & (df['Salary'] <= 3500)].copy()
    
    # Star outfielders ($4,000+)
    pools['star_of'] = df[(df['Position'].str.contains('OF')) & 
                         (df['Salary'] >= 4000)].copy()
    
    # Value outfielders ($2,500-$3,500)
    pools['value_of'] = df[(df['Position'].str.contains('OF')) & 
                          (df['Salary'] >= 2500) & (df['Salary'] <= 3500)].copy()
    
    # Mid-tier pitchers ($6,000-$9,000)
    pools['mid_pitchers'] = df[(df['Position'] == 'P') & 
                              (df['Salary'] >= 6000) & (df['Salary'] <= 9000)].copy()
    
    # Expensive pitchers ($9,000+)
    pools['expensive_pitchers'] = df[(df['Position'] == 'P') & 
                                    (df['Salary'] >= 9000)].copy()
    
    return pools

def optimize_strategic_lineup(df, pools, strategy_config, max_attempts=5000):
    """Generate a strategic lineup using the refined methodology"""
    
    best_lineup = None
    best_score = 0
    
    for attempt in range(max_attempts):
        try:
            lineup = {}
            total_salary = 0
            total_projection = 0
            used_players = []
            
            # Select catcher
            catcher_pool = pools['value_catchers']
            if strategy_config.get('prefer_expensive_c', False):
                catcher_pool = catcher_pool[catcher_pool['Salary'] >= 2600]
            
            if not catcher_pool.empty:
                # Weight by FPPG/salary ratio
                catcher_pool = catcher_pool.copy()
                catcher_pool['value_score'] = catcher_pool['FPPG'] / (catcher_pool['Salary'] / 1000)
                catcher = catcher_pool.loc[catcher_pool['value_score'].idxmax()]
                
                lineup['C'] = {
                    'Name': f"{catcher['First Name']} {catcher['Last Name']}",
                    'Position': 'C',
                    'Salary': catcher['Salary'],
                    'FPPG': catcher['FPPG']
                }
                total_salary += catcher['Salary']
                total_projection += catcher['FPPG']
                used_players.append(catcher.name)
            
            # Select 1B
            first_base_pool = pools['power_1b']
            if strategy_config.get('value_1b', False):
                first_base_pool = df[(df['Position'].str.contains('1B')) & 
                                   (df['Salary'] >= 2500) & (df['Salary'] <= 3500)]
            
            first_base_pool = first_base_pool[~first_base_pool.index.isin(used_players)]
            if not first_base_pool.empty:
                first_base_pool = first_base_pool.copy()
                if strategy_config.get('target_upside', False):
                    # Prefer higher projection players
                    first_base = first_base_pool.loc[first_base_pool['FPPG'].idxmax()]
                else:
                    first_base_pool['value_score'] = first_base_pool['FPPG'] / (first_base_pool['Salary'] / 1000)
                    first_base = first_base_pool.loc[first_base_pool['value_score'].idxmax()]
                
                lineup['1B'] = {
                    'Name': f"{first_base['First Name']} {first_base['Last Name']}",
                    'Position': '1B',
                    'Salary': first_base['Salary'],
                    'FPPG': first_base['FPPG']
                }
                total_salary += first_base['Salary']
                total_projection += first_base['FPPG']
                used_players.append(first_base.name)
            
            # Select 2B, 3B, SS from value pool
            infield_positions = ['2B', '3B', 'SS']
            for pos in infield_positions:
                pos_pool = pools['value_infield']
                pos_pool = pos_pool[pos_pool['Position'].str.contains(pos)]
                pos_pool = pos_pool[~pos_pool.index.isin(used_players)]
                
                if not pos_pool.empty:
                    pos_pool = pos_pool.copy()
                    if strategy_config.get('boost_infield', False):
                        # Boost SS/3B projections by 10%
                        if pos in ['SS', '3B']:
                            pos_pool['FPPG'] = pos_pool['FPPG'] * 1.1
                    
                    pos_pool['value_score'] = pos_pool['FPPG'] / (pos_pool['Salary'] / 1000)
                    player = pos_pool.loc[pos_pool['value_score'].idxmax()]
                    
                    lineup[pos] = {
                        'Name': f"{player['First Name']} {player['Last Name']}",
                        'Position': pos,
                        'Salary': player['Salary'],
                        'FPPG': player['FPPG']
                    }
                    total_salary += player['Salary']
                    total_projection += player['FPPG']
                    used_players.append(player.name)
            
            # Select 3 outfielders
            of_count = 0
            remaining_salary = 35000 - total_salary
            
            # First OF - potential star if budget allows
            if strategy_config.get('star_of', False) and remaining_salary >= 4500:
                star_pool = pools['star_of']
                star_pool = star_pool[~star_pool.index.isin(used_players)]
                star_pool = star_pool[star_pool['Salary'] <= remaining_salary - 6000]  # Leave room for others
                
                if not star_pool.empty:
                    star_pool = star_pool.copy()
                    star_pool['value_score'] = star_pool['FPPG'] / (star_pool['Salary'] / 1000)
                    star_of = star_pool.loc[star_pool['value_score'].idxmax()]
                    
                    lineup['OF1'] = {
                        'Name': f"{star_of['First Name']} {star_of['Last Name']}",
                        'Position': 'OF',
                        'Salary': star_of['Salary'],
                        'FPPG': star_of['FPPG']
                    }
                    total_salary += star_of['Salary']
                    total_projection += star_of['FPPG']
                    used_players.append(star_of.name)
                    of_count += 1
            
            # Fill remaining OF spots with value plays
            for i in range(of_count, 3):
                of_pool = pools['value_of']
                of_pool = of_pool[~of_pool.index.isin(used_players)]
                remaining_salary = 35000 - total_salary
                of_pool = of_pool[of_pool['Salary'] <= remaining_salary - 5000]  # Leave room for pitcher
                
                if not of_pool.empty:
                    of_pool = of_pool.copy()
                    if strategy_config.get('target_upside', False):
                        # Boost projections for $2,800-$3,200 range
                        value_boost = (of_pool['Salary'] >= 2800) & (of_pool['Salary'] <= 3200)
                        of_pool.loc[value_boost, 'FPPG'] = of_pool.loc[value_boost, 'FPPG'] * 1.15
                    
                    of_pool['value_score'] = of_pool['FPPG'] / (of_pool['Salary'] / 1000)
                    of_player = of_pool.loc[of_pool['value_score'].idxmax()]
                    
                    lineup[f'OF{i+1}'] = {
                        'Name': f"{of_player['First Name']} {of_player['Last Name']}",
                        'Position': 'OF',
                        'Salary': of_player['Salary'],
                        'FPPG': of_player['FPPG']
                    }
                    total_salary += of_player['Salary']
                    total_projection += of_player['FPPG']
                    used_players.append(of_player.name)
            
            # Select pitcher
            remaining_salary = 35000 - total_salary
            if strategy_config.get('expensive_pitcher', False) and remaining_salary >= 9000:
                pitcher_pool = pools['expensive_pitchers']
            else:
                pitcher_pool = pools['mid_pitchers']
            
            pitcher_pool = pitcher_pool[~pitcher_pool.index.isin(used_players)]
            pitcher_pool = pitcher_pool[pitcher_pool['Salary'] <= remaining_salary]
            
            if not pitcher_pool.empty:
                pitcher_pool = pitcher_pool.copy()
                if strategy_config.get('penalize_expensive_p', False):
                    # Penalize pitchers over $9,000
                    expensive_penalty = pitcher_pool['Salary'] >= 9000
                    pitcher_pool.loc[expensive_penalty, 'FPPG'] = pitcher_pool.loc[expensive_penalty, 'FPPG'] * 0.85
                
                pitcher_pool['value_score'] = pitcher_pool['FPPG'] / (pitcher_pool['Salary'] / 1000)
                pitcher = pitcher_pool.loc[pitcher_pool['value_score'].idxmax()]
                
                lineup['P'] = {
                    'Name': f"{pitcher['First Name']} {pitcher['Last Name']}",
                    'Position': 'P',
                    'Salary': pitcher['Salary'],
                    'FPPG': pitcher['FPPG']
                }
                total_salary += pitcher['Salary']
                total_projection += pitcher['FPPG']
            
            # Check if lineup is complete and valid
            if len(lineup) == 9 and total_salary <= 35000:
                if total_projection > best_score:
                    best_score = total_projection
                    best_lineup = lineup.copy()
                    best_lineup['total_salary'] = total_salary
                    best_lineup['projected_score'] = total_projection
        
        except Exception as e:
            continue
    
    return best_lineup, best_score

def main():
    logger.info("TARGET: GENERATING 10 STRATEGIC LINEUPS - HYBRID APPROACH")
    logger.info("=" * 60)
    
    # Load and filter slate
    filtered_df = load_and_filter_slate()
    if filtered_df is None:
        return
    
    # Create strategic player pools
    pools = create_player_pools(filtered_df)
    
    # Define 10 strategic configurations
    strategies = [
        {'name': 'Strategic_Upside_A', 'prefer_expensive_c': True, 'target_upside': True, 'boost_infield': True, 'star_of': True, 'penalize_expensive_p': True},
        {'name': 'Strategic_Upside_B', 'prefer_expensive_c': True, 'target_upside': True, 'boost_infield': True, 'star_of': False, 'penalize_expensive_p': True},
        {'name': 'Strategic_Value_A', 'prefer_expensive_c': False, 'value_1b': True, 'boost_infield': True, 'star_of': False, 'penalize_expensive_p': True},
        {'name': 'Strategic_Value_B', 'prefer_expensive_c': False, 'value_1b': True, 'boost_infield': False, 'star_of': False, 'penalize_expensive_p': True},
        {'name': 'Strategic_Balanced_A', 'prefer_expensive_c': True, 'target_upside': False, 'boost_infield': True, 'star_of': True, 'expensive_pitcher': False},
        {'name': 'Strategic_Balanced_B', 'prefer_expensive_c': False, 'target_upside': True, 'boost_infield': True, 'star_of': True, 'expensive_pitcher': False},
        {'name': 'Strategic_Power_A', 'prefer_expensive_c': True, 'target_upside': True, 'boost_infield': False, 'star_of': True, 'expensive_pitcher': True},
        {'name': 'Strategic_Power_B', 'prefer_expensive_c': True, 'target_upside': True, 'boost_infield': True, 'star_of': True, 'expensive_pitcher': False},
        {'name': 'Strategic_Contrarian_A', 'prefer_expensive_c': False, 'value_1b': True, 'boost_infield': True, 'star_of': False, 'expensive_pitcher': False},
        {'name': 'Strategic_Contrarian_B', 'prefer_expensive_c': False, 'value_1b': False, 'boost_infield': True, 'star_of': False, 'expensive_pitcher': True}
    ]
    
    logger.info(f"Generating 10 strategic lineups from {len(filtered_df)} filtered players...")
    
    all_lineups = []
    
    for i, strategy_config in enumerate(strategies):
        lineup, score = optimize_strategic_lineup(filtered_df, pools, strategy_config)
        
        if lineup:
            lineup['Strategy'] = strategy_config['name']
            all_lineups.append(lineup)
            logger.info(f"Generated {strategy_config['name']:20}: {score:.1f} projected points (${lineup['total_salary']:,})")
        else:
            logger.warning(f"Failed to generate {strategy_config['name']}")
    
    # Save lineups for evaluation
    lineup_data = []
    for lineup in all_lineups:
        strategy = lineup['Strategy']
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'P']
        
        for pos in positions:
            if pos in lineup:
                lineup_data.append({
                    'Strategy': strategy,
                    'Position': pos.replace('OF1', 'OF').replace('OF2', 'OF').replace('OF3', 'OF'),
                    'Name': lineup[pos]['Name'],
                    'Salary': lineup[pos]['Salary'],
                    'FPPG': lineup[pos]['FPPG']
                })
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"10_STRATEGIC_LINEUPS_AUG12_{timestamp}.csv"
    pd.DataFrame(lineup_data).to_csv(filename, index=False)
    
    logger.info(f"SUCCESS: Generated {len(all_lineups)} strategic lineups")
    logger.info(f" Saved to: {filename}")
    
    print(f"\nNext step: Evaluate these lineups against actual August 12th results")
    print(f"These lineups use the REFINED 5-lineup methodology with strategic variations!")

if __name__ == "__main__":
    main()
