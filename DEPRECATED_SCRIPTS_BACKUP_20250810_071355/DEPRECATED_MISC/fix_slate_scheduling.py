#!/usr/bin/env python3
"""
BACKTEST LINEUP GENERATOR FOR 8/7/25
====================================
Generate 10 unique lineups using 8/7/25 slate and backtest vs actual results.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from itertools import combinations
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_fanduel_points(row):
    """Calculate FanDuel points from stats"""
    if row['position'] == 'P':
        # Pitcher scoring
        points = (
            row.get('innings_pitched', 0) * 3 +  # 3 pts per IP
            row.get('wins', 0) * 6 +             # 6 pts per win
            row.get('strikeouts', 0) * 3 -       # 3 pts per K
            row.get('hits_allowed', 0) * 0.6 -   # -0.6 per hit
            row.get('earned_runs', 0) * 3        # -3 per ER
        )
    else:
        # Hitter scoring
        points = (
            row.get('at_bats', 0) * 0 +          # 0 pts for AB
            row.get('hits', 0) * 3 +             # 3 pts per hit
            row.get('runs', 0) * 3.2 +           # 3.2 pts per run
            row.get('rbis', 0) * 3.5 +           # 3.5 pts per RBI
            row.get('home_runs', 0) * 10 +       # 10 pts per HR
            row.get('stolen_bases', 0) * 6 +     # 6 pts per SB
            row.get('walks', 0) * 3 +            # 3 pts per walk
            row.get('doubles', 0) * 6 +          # 6 pts per 2B  
            row.get('triples', 0) * 12           # 12 pts per 3B
        )
    return max(0, points)  # No negative scores

def load_yesterdays_data():
    """Load 8/7/25 slate and actual results"""
    logger.info("📊 Loading 8/7/25 data for backtest...")
    
    # Load FanDuel slate from yesterday (this contains positions and salaries)
    try:
        slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        logger.info(f"✅ Loaded {len(slate_df)} players from FD slate")
        
        # Clean up the slate data
        slate_df['player_name'] = slate_df['First Name'] + ' ' + slate_df['Last Name']
        slate_df['position'] = slate_df['Position']
        slate_df['team'] = slate_df['Team']
        slate_df['fanduel_salary'] = slate_df['Salary']
        slate_df['fppg_avg'] = slate_df['FPPG']
        
        # Teams that actually played on 8/7/25 (from the slate)
        playing_teams = set(slate_df['team'].unique())
        logger.info(f"🏟️ Teams on slate: {sorted(playing_teams)}")
        
        # Add some projected FPPG and ownership (simplified for backtest)
        slate_df['projected_fppg'] = slate_df['fppg_avg'] * np.random.uniform(0.8, 1.2, len(slate_df))
        slate_df['ownership_proj'] = np.random.uniform(2, 30, len(slate_df))
        
        # Filter to essential columns
        slate_df = slate_df[['player_name', 'position', 'team', 'fanduel_salary', 'projected_fppg', 'ownership_proj', 'fppg_avg']].copy()
        
    except Exception as e:
        logger.error(f"❌ Could not load FD slate: {e}")
        return None, None
    
    # Load actual results from 8/7
    try:
        actual_df = pd.read_csv("../data/actual_results_20250807.csv")
        logger.info(f"✅ Loaded {len(actual_df)} actual results from 8/7")
        
        # Calculate actual FanDuel points
        actual_df['actual_fppg'] = actual_df.apply(calculate_fanduel_points, axis=1)
        
    except Exception as e:
        logger.error(f"❌ Could not load actual results: {e}")
        return slate_df, None
    
    return slate_df, actual_df

def generate_10_unique_lineups(slate_df, salary_cap=35000):
    """Generate 10 unique, high-quality lineups"""
    logger.info("🏆 Generating 10 unique lineups...")
    
    if slate_df is None or len(slate_df) == 0:
        logger.error("❌ No player data available")
        return []
    
    lineups = []
    used_combinations = set()
    
    for lineup_num in range(1, 11):
        logger.info(f"Building lineup {lineup_num}...")
        
        attempts = 0
        max_attempts = 100
        
        while attempts < max_attempts:
            lineup = build_single_lineup(slate_df.copy(), salary_cap, lineup_num)
            
            if lineup is None:
                attempts += 1
                continue
            
            # Create signature for uniqueness check
            player_names = tuple(sorted([p['player_name'] for p in lineup]))
            
            if player_names not in used_combinations:
                used_combinations.add(player_names)
                lineups.append({
                    'lineup_id': f"lineup_{lineup_num}",
                    'players': lineup,
                    'total_salary': sum(p['salary'] for p in lineup),
                    'projected_fppg': sum(p['projected_fppg'] for p in lineup),
                    'avg_ownership': np.mean([p['ownership'] for p in lineup])
                })
                break
            
            attempts += 1
        
        if attempts >= max_attempts:
            logger.warning(f"⚠️ Could not generate unique lineup {lineup_num}")
    
    logger.info(f"✅ Generated {len(lineups)} unique lineups")
    return lineups

def build_single_lineup(df, salary_cap, strategy_seed):
    """Build a single lineup with variation based on strategy"""
    
    # Set random seed for reproducible but different results
    np.random.seed(strategy_seed * 42)
    
    lineup = []
    remaining_salary = salary_cap
    positions_needed = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Strategy variations
    strategies = [
        'max_projected',  # Pure projection ceiling
        'value_play',     # Best value per dollar
        'low_ownership',  # Contrarian plays
        'balanced',       # Mix of projection and value
        'stars_scrubs',   # Expensive studs + cheap fills
    ]
    
    strategy = strategies[(strategy_seed - 1) % len(strategies)]
    
    for pos in positions_needed:
        available = df[df['position'] == pos].copy()
        
        if len(available) == 0:
            logger.warning(f"⚠️ No players available for position {pos}")
            return None
        
        # Filter by remaining salary
        affordable = available[available['fanduel_salary'] <= remaining_salary]
        
        if len(affordable) == 0:
            logger.warning(f"⚠️ No affordable players for position {pos} (${remaining_salary} left)")
            return None
        
        # Apply strategy
        if strategy == 'max_projected':
            chosen = affordable.nlargest(1, 'projected_fppg').iloc[0]
        elif strategy == 'value_play':
            affordable['value'] = affordable['projected_fppg'] / affordable['fanduel_salary']
            chosen = affordable.nlargest(1, 'value').iloc[0]
        elif strategy == 'low_ownership':
            chosen = affordable.nsmallest(1, 'ownership_proj').iloc[0]
        elif strategy == 'stars_scrubs':
            if remaining_salary > 8000:  # Spend up
                expensive = affordable[affordable['fanduel_salary'] >= 6000]
                if len(expensive) > 0:
                    chosen = expensive.nlargest(1, 'projected_fppg').iloc[0]
                else:
                    chosen = affordable.nlargest(1, 'projected_fppg').iloc[0]
            else:  # Find cheap fills
                cheap = affordable[affordable['fanduel_salary'] <= 4000]
                if len(cheap) > 0:
                    cheap['value'] = cheap['projected_fppg'] / cheap['fanduel_salary']
                    chosen = cheap.nlargest(1, 'value').iloc[0]
                else:
                    chosen = affordable.nlargest(1, 'projected_fppg').iloc[0]
        else:  # balanced
            affordable['score'] = (affordable['projected_fppg'] * 0.7 + 
                                 (affordable['projected_fppg'] / affordable['fanduel_salary']) * 0.3)
            chosen = affordable.nlargest(1, 'score').iloc[0]
        
        lineup.append({
            'player_name': chosen['player_name'],
            'position': chosen['position'],
            'team': chosen['team'],
            'salary': chosen['fanduel_salary'],
            'projected_fppg': chosen['projected_fppg'],
            'ownership': chosen['ownership_proj']
        })
        
        remaining_salary -= chosen['fanduel_salary']
        
        # Remove chosen player from available pool
        df = df[df['player_name'] != chosen['player_name']]
    
    return lineup

def backtest_lineups(lineups, actual_df):
    """Backtest lineups against actual 8/7 results"""
    logger.info("🔍 Backtesting lineups against actual results...")
    
    results = []
    
    for lineup_data in lineups:
        lineup_id = lineup_data['lineup_id']
        players = lineup_data['players']
        
        total_actual = 0
        players_found = 0
        
        for player in players:
            # Match player to actual results
            actual_match = actual_df[actual_df['name'].str.contains(player['player_name'], case=False, na=False)]
            
            if len(actual_match) > 0:
                actual_points = actual_match.iloc[0]['actual_fppg']
                players_found += 1
            else:
                actual_points = 0  # Player didn't play or not found
            
            total_actual += actual_points
        
        accuracy = (total_actual / lineup_data['projected_fppg'] * 100) if lineup_data['projected_fppg'] > 0 else 0
        
        results.append({
            'lineup_id': lineup_id,
            'projected_fppg': lineup_data['projected_fppg'],
            'actual_fppg': total_actual,
            'difference': total_actual - lineup_data['projected_fppg'],
            'accuracy_pct': accuracy,
            'players_found': players_found,
            'total_players': len(players),
            'total_salary': lineup_data['total_salary'],
            'avg_ownership': lineup_data['avg_ownership']
        })
    
    return pd.DataFrame(results)

def save_backtest_results(lineups, backtest_results):
    """Save lineup details and backtest results"""
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
                'ownership_proj': player['ownership']
            })
    
    details_df = pd.DataFrame(lineup_details)
    details_file = f"../data/backtest_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    logger.info(f"💾 Saved lineup details: {details_file}")
    
    # Save backtest summary
    summary_file = f"../data/backtest_summary_{timestamp}.csv"
    backtest_results.to_csv(summary_file, index=False)
    logger.info(f"💾 Saved backtest summary: {summary_file}")
    
    return details_file, summary_file

def main():
    """Main function to run backtest"""
    
    logger.info("🎯 BACKTESTING 8/7/25 LINEUPS")
    logger.info("=" * 50)
    
    # Load data
    slate_df, actual_df = load_yesterdays_data()
    
    if slate_df is None:
        logger.error("❌ Cannot proceed without slate data")
        return
    
    # Generate lineups
    lineups = generate_10_unique_lineups(slate_df)
    
    if len(lineups) == 0:
        logger.error("❌ No lineups generated")
        return
    
    # Backtest if we have actual results
    if actual_df is not None:
        backtest_results = backtest_lineups(lineups, actual_df)
        
        # Save results
        details_file, summary_file = save_backtest_results(lineups, backtest_results)
        
        # Print summary
        print(f"\n🏆 BACKTEST RESULTS SUMMARY")
        print("=" * 50)
        print(backtest_results.to_string(index=False))
        
        avg_accuracy = backtest_results['accuracy_pct'].mean()
        best_lineup = backtest_results.loc[backtest_results['actual_fppg'].idxmax()]
        
        print(f"\n📊 PERFORMANCE METRICS:")
        print(f"   Average Accuracy: {avg_accuracy:.1f}%")
        print(f"   Best Lineup: {best_lineup['lineup_id']} ({best_lineup['actual_fppg']:.1f} FPPG)")
        print(f"   Avg Players Found: {backtest_results['players_found'].mean():.1f}/9")
        
    else:
        logger.warning("⚠️ No actual results available for backtesting")
    
    logger.info("✅ Backtest complete!")

if __name__ == "__main__":
    main()
