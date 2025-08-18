#!/usr/bin/env python3
"""
SIMPLE CLEAN LINEUP GENERATOR
============================
Generate 10 unique, quality lineups using 8/7/25 slate with proper salary management.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_slate_and_results():
    """Load FD slate and actual results for backtesting"""
    logger.info("DATA: Loading slate and actual results...")
    
    # Load yesterday's slate
    slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    logger.info(f"SUCCESS: Loaded {len(slate_df)} players from slate")
    
    # FILTER TO ONLY ACTUAL STARTERS!
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
    slate_df = pd.concat([starting_pitchers, starting_hitters], ignore_index=True)
    logger.info(f"LINEUP: FILTERED to {len(slate_df)} ACTUAL STARTERS")
    
    # Clean player data
    slate_df['player_name'] = slate_df['First Name'] + ' ' + slate_df['Last Name']
    slate_df = slate_df[['player_name', 'Position', 'Team', 'Salary', 'FPPG']].copy()
    slate_df.columns = ['player_name', 'position', 'team', 'salary', 'projected_fppg']
    
    # Add ownership projections (simplified)
    np.random.seed(42)  # Consistent results
    slate_df['ownership'] = np.random.uniform(3, 25, len(slate_df))
    
    # Load actual results
    actual_df = pd.read_csv("../data/actual_results_20250809.csv")  # Updated to latest available data
    actual_df['actual_fppg'] = actual_df['fanduel_points']
    logger.info(f"SUCCESS: Loaded {len(actual_df)} actual results")
    
    return slate_df, actual_df

def build_lineup(slate_df, strategy_num=1, salary_cap=35000):
    """Build a single lineup with proper salary management"""
    
    np.random.seed(strategy_num * 17)  # Different seed for each lineup
    
    lineup = []
    remaining_salary = salary_cap
    
    # Position requirements
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Strategy: Start with most expensive positions and work down
    position_order = ['P', 'OF', 'OF', 'OF', '1B', '3B', 'SS', '2B', 'C']
    
    for i, pos in enumerate(position_order):
        available = slate_df[slate_df['position'] == pos].copy()
        
        if len(available) == 0:
            continue
            
        # Calculate max affordable salary for this position
        positions_left = len(position_order) - i - 1
        min_salary_needed = positions_left * 2000  # Assume $2K minimum per remaining position
        max_affordable = remaining_salary - min_salary_needed
        
        # Filter by affordability
        affordable = available[available['salary'] <= max_affordable]
        
        if len(affordable) == 0:
            # Emergency: Just get cheapest available
            affordable = available.nsmallest(1, 'salary')
        
        # Selection strategy based on lineup number
        if strategy_num <= 3:  # Pure projection
            chosen = affordable.nlargest(1, 'projected_fppg')
        elif strategy_num <= 6:  # Value play
            affordable['value'] = affordable['projected_fppg'] / affordable['salary']
            chosen = affordable.nlargest(1, 'value')
        else:  # Mixed strategy
            affordable['score'] = (affordable['projected_fppg'] * 0.6 + 
                                 (affordable['projected_fppg'] / affordable['salary']) * 0.4)
            chosen = affordable.nlargest(1, 'score')
        
        if len(chosen) > 0:
            player = chosen.iloc[0]
            lineup.append({
                'player_name': player['player_name'],
                'position': player['position'],
                'team': player['team'],
                'salary': player['salary'],
                'projected_fppg': player['projected_fppg'],
                'ownership': player['ownership']
            })
            
            remaining_salary -= player['salary']
            # Remove player from pool
            slate_df = slate_df[slate_df['player_name'] != player['player_name']]
    
    return lineup if len(lineup) == 9 else None

def generate_10_lineups(slate_df):
    """Generate 10 unique lineups"""
    logger.info("LINEUP: Generating 10 lineups...")
    
    lineups = []
    
    for i in range(1, 11):
        logger.info(f"Building lineup {i}...")
        
        # Use fresh copy of slate for each lineup
        slate_copy = slate_df.copy()
        lineup = build_lineup(slate_copy, i)
        
        if lineup and len(lineup) == 9:
            total_salary = sum(p['salary'] for p in lineup)
            total_projected = sum(p['projected_fppg'] for p in lineup)
            avg_ownership = np.mean([p['ownership'] for p in lineup])
            
            lineups.append({
                'lineup_id': f"lineup_{i}",
                'players': lineup,
                'total_salary': total_salary,
                'projected_fppg': total_projected,
                'avg_ownership': avg_ownership
            })
            
            logger.info(f"SUCCESS: Lineup {i}: ${total_salary:,} salary, {total_projected:.1f} FPPG")
        else:
            logger.warning(f"WARNING: Failed to build lineup {i}")
    
    return lineups

def backtest_lineups(lineups, actual_df):
    """Backtest lineups against actual results"""
    logger.info(" Backtesting lineups...")
    
    results = []
    
    for lineup_data in lineups:
        total_actual = 0
        players_found = 0
        
        for player in lineup_data['players']:
            # Simple name matching
            matches = actual_df[actual_df['name'].str.contains(
                player['player_name'].split()[-1], case=False, na=False)]  # Match by last name
            
            if len(matches) > 0:
                actual_fppg = matches.iloc[0]['actual_fppg']
                players_found += 1
            else:
                actual_fppg = 0
            
            total_actual += actual_fppg
        
        accuracy = (total_actual / lineup_data['projected_fppg'] * 100) if lineup_data['projected_fppg'] > 0 else 0
        
        results.append({
            'lineup_id': lineup_data['lineup_id'],
            'projected_fppg': lineup_data['projected_fppg'],
            'actual_fppg': total_actual,
            'difference': total_actual - lineup_data['projected_fppg'],
            'accuracy_pct': accuracy,
            'players_found': players_found,
            'total_salary': lineup_data['total_salary'],
            'avg_ownership': lineup_data['avg_ownership']
        })
    
    return pd.DataFrame(results)

def save_results(lineups, backtest_df):
    """Save lineup details and results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save lineup details
    lineup_details = []
    for lineup_data in lineups:
        for player in lineup_data['players']:
            lineup_details.append({
                'lineup_id': lineup_data['lineup_id'],
                'player_name': player['player_name'],
                'position': player['position'],
                'team': player['team'],
                'salary': player['salary'],
                'projected_fppg': player['projected_fppg'],
                'ownership': player['ownership']
            })
    
    details_df = pd.DataFrame(lineup_details)
    details_file = f"../data/clean_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    # Save backtest results
    summary_file = f"../data/clean_backtest_summary_{timestamp}.csv"
    backtest_df.to_csv(summary_file, index=False)
    
    logger.info(f" Saved: {details_file}")
    logger.info(f" Saved: {summary_file}")
    
    return details_file, summary_file

def main():
    """Main execution"""
    logger.info("TARGET: CLEAN LINEUP GENERATOR")
    logger.info("=" * 40)
    
    # Load data
    slate_df, actual_df = load_slate_and_results()
    
    # Generate lineups
    lineups = generate_10_lineups(slate_df)
    
    if len(lineups) == 0:
        logger.error("ERROR: No lineups generated")
        return
    
    logger.info(f"SUCCESS: Generated {len(lineups)} lineups")
    
    # Backtest
    backtest_df = backtest_lineups(lineups, actual_df)
    
    # Save results
    save_results(lineups, backtest_df)
    
    # Display summary
    print(f"\nLINEUP: BACKTEST RESULTS")
    print("=" * 50)
    print(backtest_df[['lineup_id', 'projected_fppg', 'actual_fppg', 'accuracy_pct', 'players_found']].to_string(index=False))
    
    print(f"\nDATA: SUMMARY:")
    print(f"   Average Accuracy: {backtest_df['accuracy_pct'].mean():.1f}%")
    print(f"   Best Lineup: {backtest_df.loc[backtest_df['actual_fppg'].idxmax()]['lineup_id']} ({backtest_df['actual_fppg'].max():.1f} FPPG)")
    print(f"   Average Players Found: {backtest_df['players_found'].mean():.1f}/9")
    print(f"   Average Salary Used: ${backtest_df['total_salary'].mean():,.0f}")

if __name__ == "__main__":
    main()
