#!/usr/bin/env python3
"""
DIVERSIFIED DAILY PROPS SYSTEM
==============================
Input your prop bet decisions and generate DIVERSE optimized lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_player_data():
    """Load the latest player projections using proven data source"""
    
    try:
        # Use the same data source as your working system
        slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        logger.info(f"SUCCESS: Loaded {len(slate_df)} players from slate")
        
        # FILTER TO ONLY ACTUAL STARTERS (same as SIMPLE_CLEAN_GENERATOR)
        logger.info("TARGET: Filtering to ONLY players who actually started...")
        
        # For pitchers: Only probable pitchers
        pitchers = slate_df[slate_df['Position'] == 'P'].copy()
        starting_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
        logger.info(f"   Probable pitchers: {len(starting_pitchers)}")
        
        # For hitters: Only players with batting order (1-9)
        hitters = slate_df[slate_df['Position'] != 'P'].copy()
        starting_hitters = hitters[hitters['Batting Order'].notna() & (hitters['Batting Order'] != '')]
        logger.info(f"   Hitters with batting order: {len(starting_hitters)}")
        
        # Combine starters only
        df = pd.concat([starting_pitchers, starting_hitters], ignore_index=True)
        logger.info(f"LINEUP: FILTERED to {len(df)} ACTUAL STARTERS")
        
        # Clean and standardize column names
        df['name'] = df['First Name'] + ' ' + df['Last Name']
        df = df[['name', 'Position', 'Team', 'Salary', 'FPPG']].copy()
        df.columns = ['name', 'position', 'team', 'salary', 'fppg']
        
        # Add ownership projections
        np.random.seed(42)  # Consistent results
        df['ownership'] = np.random.uniform(3, 25, len(df))
        
        return df
        
    except FileNotFoundError:
        logger.error("ERROR: fd_slate_today.csv not found!")
        return None

def get_prop_decisions():
    """Interactive prop bet input"""
    
    print("\nTARGET: DAILY PROP BET INPUT")
    print("=" * 40)
    print("Enter your prop bet decisions for today's slate")
    print("Press Enter with empty player name when done")
    print()
    
    props = []
    
    while True:
        player_name = input("Player Name (or Enter to finish): ").strip()
        if not player_name:
            break
        
        print(f"\nProp options for {player_name}:")
        print("1. Hits")
        print("2. Runs") 
        print("3. RBIs")
        print("4. Home Runs")
        print("5. Walks")
        print("6. Stolen Bases")
        print("7. Strikeouts (pitcher)")
        
        prop_choice = input("Select prop type (1-7): ").strip()
        prop_types = {
            '1': 'hits', '2': 'runs', '3': 'rbis', 
            '4': 'home_runs', '5': 'walks', '6': 'stolen_bases', 
            '7': 'strikeouts'
        }
        
        if prop_choice not in prop_types:
            print("Invalid choice, skipping...")
            continue
        
        prop_type = prop_types[prop_choice]
        
        try:
            line = float(input(f"Line for {prop_type}: "))
            pick = input("Your pick (over/under): ").strip().upper()
            confidence = int(input("Confidence (1-5): "))
            
            if pick not in ['OVER', 'UNDER']:
                print("Invalid pick, skipping...")
                continue
            
            if confidence < 1 or confidence > 5:
                print("Invalid confidence, skipping...")
                continue
            
            props.append({
                'player_name': player_name,
                'prop_type': prop_type,
                'line': line,
                'my_pick': pick,
                'confidence': confidence
            })
            
            print(f"SUCCESS: Added: {player_name} {prop_type} {pick} {line} (confidence: {confidence})")
            
        except ValueError:
            print("Invalid input, skipping...")
            continue
    
    return props

def apply_prop_boosts(df, props):
    """Apply confidence-based boosts to players with props"""
    
    df_boosted = df.copy()
    applied_boosts = []
    
    for prop in props:
        player_name = prop['player_name']
        confidence = prop['confidence']
        
        # Find matching players (fuzzy match)
        mask = df_boosted['name'].str.contains(player_name, case=False, na=False)
        matching_players = df_boosted[mask]
        
        if len(matching_players) > 0:
            # Apply boost: 10% per confidence point
            boost_multiplier = 1 + (confidence * 0.10)
            
            # Update the FPPG projection
            player_idx = matching_players.index[0]
            original_fppg = df_boosted.loc[player_idx, 'fppg']
            boosted_fppg = original_fppg * boost_multiplier
            
            df_boosted.loc[player_idx, 'fppg'] = boosted_fppg
            
            applied_boosts.append({
                'player_name': df_boosted.loc[player_idx, 'name'],
                'prop_type': prop['prop_type'],
                'line': prop['line'],
                'my_pick': prop['my_pick'],
                'confidence': confidence,
                'original_fppg': original_fppg,
                'boosted_fppg': boosted_fppg,
                'boost_pct': (boost_multiplier - 1) * 100
            })
            
            logger.info(f"SUCCESS: Boosted {player_name}: {original_fppg:.1f}  {boosted_fppg:.1f} FPPG ({(boost_multiplier-1)*100:.0f}% boost)")
        else:
            logger.warning(f"ERROR: Player not found: {player_name}")
    
    return df_boosted, applied_boosts

def generate_diversified_lineups(df, num_lineups=5):
    """Generate diverse lineups using different optimization strategies"""
    
    lineups = []
    used_combinations = set()
    
    for i in range(num_lineups):
        logger.info(f"Generating diversified lineup {i+1}...")
        
        # Apply different diversity strategies
        if i == 0:
            # Strategy 1: Pure optimization (baseline)
            lineup_df = df.copy()
            strategy = "Optimal"
        elif i == 1:
            # Strategy 2: Boost mid-tier players
            lineup_df = df.copy()
            mid_tier_mask = (lineup_df['fppg'] >= lineup_df['fppg'].quantile(0.3)) & (lineup_df['fppg'] <= lineup_df['fppg'].quantile(0.7))
            lineup_df.loc[mid_tier_mask, 'fppg'] *= 1.15
            strategy = "Mid-Tier Boost"
        elif i == 2:
            # Strategy 3: Salary efficiency focus
            lineup_df = df.copy()
            lineup_df['efficiency'] = lineup_df['fppg'] / lineup_df['salary']
            efficiency_boost = lineup_df['efficiency'].quantile(0.8)
            high_efficiency_mask = lineup_df['efficiency'] >= efficiency_boost
            lineup_df.loc[high_efficiency_mask, 'fppg'] *= 1.20
            strategy = "High Efficiency"
        elif i == 3:
            # Strategy 4: Contrarian (boost lower-owned players)
            lineup_df = df.copy()
            if 'ownership' in lineup_df.columns:
                low_owned_mask = lineup_df['ownership'] <= lineup_df['ownership'].quantile(0.4)
                lineup_df.loc[low_owned_mask, 'fppg'] *= 1.25
            else:
                # Random slight adjustments if no ownership data
                random_mask = np.random.choice([True, False], size=len(lineup_df), p=[0.3, 0.7])
                lineup_df.loc[random_mask, 'fppg'] *= 1.10
            strategy = "Contrarian"
        else:
            # Strategy 5: Chaos mode (random adjustments)
            lineup_df = df.copy()
            chaos_adjustments = np.random.uniform(0.9, 1.3, size=len(lineup_df))
            lineup_df['fppg'] *= chaos_adjustments
            strategy = "Chaos"
        
        # Generate lineup using greedy optimization with salary constraints
        lineup = optimize_lineup(lineup_df)
        
        if lineup:
            # Check for uniqueness
            lineup_signature = tuple(sorted([p['name'] for p in lineup]))
            
            if lineup_signature not in used_combinations:
                used_combinations.add(lineup_signature)
                lineup_info = format_lineup(lineup, strategy, i+1)
                lineups.append(lineup_info)
                logger.info(f"SUCCESS: Generated unique lineup {i+1} using {strategy} strategy")
            else:
                logger.warning(f"WARNING: Lineup {i+1} was duplicate, keeping anyway")
                lineup_info = format_lineup(lineup, f"{strategy} (Duplicate)", i+1)
                lineups.append(lineup_info)
    
    return lineups

def optimize_lineup(df):
    """Greedy lineup optimization with salary cap"""
    
    SALARY_CAP = 35000
    POSITIONS = {
        'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 
        'SS': 1, 'OF': 3
    }
    
    # Sort by FPPG efficiency (FPPG per $1000 salary)
    df = df.copy()
    df['efficiency'] = df['fppg'] / (df['salary'] / 1000)
    df = df.sort_values('efficiency', ascending=False)
    
    lineup = []
    remaining_salary = SALARY_CAP
    position_needs = POSITIONS.copy()
    
    # Fill each position with best available player
    for position in ['P', 'C', '1B', '2B', '3B', 'SS']:
        available = df[
            (df['position'] == position) & 
            (df['salary'] <= remaining_salary) &
            (~df['name'].isin([p['name'] for p in lineup]))
        ]
        
        if len(available) > 0:
            best_player = available.iloc[0]
            lineup.append({
                'name': best_player['name'],
                'position': position,
                'salary': best_player['salary'],
                'fppg': best_player['fppg'],
                'team': best_player.get('team', 'UNK')
            })
            remaining_salary -= best_player['salary']
            position_needs[position] -= 1
    
    # Fill OF positions
    for of_num in range(3):
        available = df[
            (df['position'] == 'OF') & 
            (df['salary'] <= remaining_salary) &
            (~df['name'].isin([p['name'] for p in lineup]))
        ]
        
        if len(available) > 0:
            best_player = available.iloc[0]
            lineup.append({
                'name': best_player['name'],
                'position': f'OF{of_num+1}',
                'salary': best_player['salary'],
                'fppg': best_player['fppg'],
                'team': best_player.get('team', 'UNK')
            })
            remaining_salary -= best_player['salary']
    
    return lineup if len(lineup) == 9 else None

def format_lineup(lineup, strategy, lineup_num):
    """Format lineup for output"""
    
    total_salary = sum(p['salary'] for p in lineup)
    total_fppg = sum(p['fppg'] for p in lineup)
    
    formatted = {
        'Lineup': f'diversified_lineup_{lineup_num}',
        'Strategy': strategy,
        'Total_Salary': total_salary,
        'Projected_FPPG': total_fppg
    }
    
    # Add players by position
    position_map = {'P': 'P', 'C': 'C', '1B': '1B', '2B': '2B', '3B': '3B', 'SS': 'SS'}
    
    for player in lineup:
        if player['position'] in position_map:
            pos_key = position_map[player['position']]
        else:  # OF positions
            pos_key = player['position']  # OF1, OF2, OF3
        
        formatted[pos_key] = f"{player['name']} ({player['team']})"
    
    return formatted

def save_results(props, boosts, lineups):
    """Save all results to CSV files"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save prop decisions
    if props:
        props_df = pd.DataFrame(props)
        props_file = f"../data/diversified_prop_summary_{timestamp}.csv"
        props_df.to_csv(props_file, index=False)
        logger.info(f" Prop decisions saved: {props_file}")
    
    # Save applied boosts
    if boosts:
        boosts_df = pd.DataFrame(boosts)
        boosts_file = f"../data/diversified_prop_boosts_{timestamp}.csv"
        boosts_df.to_csv(boosts_file, index=False)
        logger.info(f" Prop boosts saved: {boosts_file}")
    
    # Save lineups
    if lineups:
        lineups_df = pd.DataFrame(lineups)
        lineups_file = f"../data/diversified_prop_lineups_{timestamp}.csv"
        lineups_df.to_csv(lineups_file, index=False)
        logger.info(f" Diversified lineups saved: {lineups_file}")
        
        # Also save in FanDuel format
        fd_lineups = []
        for lineup in lineups:
            fd_lineup = {
                'P': lineup.get('P', ''),
                'C': lineup.get('C', ''),
                '1B': lineup.get('1B', ''),
                '2B': lineup.get('2B', ''),
                '3B': lineup.get('3B', ''),
                'SS': lineup.get('SS', ''),
                'OF': lineup.get('OF1', ''),
                'OF': lineup.get('OF2', ''),
                'OF': lineup.get('OF3', '')
            }
            fd_lineups.append(fd_lineup)
        
        fd_file = f"../fd_current_slate/Diversified_Lineups_FD_Format_{timestamp}.csv"
        pd.DataFrame(fd_lineups).to_csv(fd_file, index=False)
        logger.info(f" FanDuel format saved: {fd_file}")

def main():
    """Main execution"""
    
    print("\nTARGET: DIVERSIFIED DAILY PROPS SYSTEM")
    print("=" * 50)
    
    # Load player data
    df = load_player_data()
    if df is None:
        return
    
    # Get prop decisions
    props = get_prop_decisions()
    
    if not props:
        print("\nWARNING: No props entered, generating standard diversified lineups...")
        boosts = []
        df_final = df
    else:
        # Apply prop boosts
        df_final, boosts = apply_prop_boosts(df, props)
        
        print(f"\nSUCCESS: Applied {len(boosts)} prop boosts")
        for boost in boosts:
            print(f"   START: {boost['player_name']}: +{boost['boost_pct']:.0f}% boost")
    
    # Generate diversified lineups
    print(f"\nTARGET: Generating 5 diversified lineups...")
    lineups = generate_diversified_lineups(df_final)
    
    # Display results
    print(f"\nDATA: DIVERSIFIED LINEUP SUMMARY:")
    print("-" * 50)
    for lineup in lineups:
        print(f"LINEUP: {lineup['Lineup']} ({lineup['Strategy']})")
        print(f"   MONEY: Salary: ${lineup['Total_Salary']:,}")
        print(f"   TARGET: Projected: {lineup['Projected_FPPG']:.1f} FPPG")
        print()
    
    # Save results
    save_results(props, boosts, lineups)
    
    print("SUCCESS: Diversified prop system complete!")

if __name__ == "__main__":
    main()
