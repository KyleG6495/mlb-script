#!/usr/bin/env python3
"""
DAILY LINEUP GENERATOR
=====================
Generate 10 unique, high-quality DFS lineups using ONLY confirmed starters from current slate.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_current_slate():
    """Load current FanDuel slate using pre-filtered confirmed starters"""
    logger.info("DATA: Loading current FanDuel slate...")
    
    try:
        # First try to load starters-only file (pre-filtered)
        starters_file = "../data/fd_slate_starters_only.csv"
        
        try:
            slate_df = pd.read_csv(starters_file)
            logger.info(f"SUCCESS: Loaded {len(slate_df)} confirmed starters from pre-filtered file")
            logger.info("TARGET: Using validated starting lineups only - no complex filtering needed")
        except:
            # Fallback to main slate with filtering
            logger.warning("WARNING: Starters-only file not found, using main slate with filtering")
            slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
            logger.info(f"SUCCESS: Loaded {len(slate_df)} players from main slate")
            
            # CRITICAL: Filter to ONLY actual starters
            logger.info("TARGET: Filtering to ONLY confirmed starters...")
            
            # For pitchers: Only probable pitchers
            pitchers = slate_df[slate_df['Position'] == 'P'].copy()
            starting_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
            logger.info(f"   SUCCESS: Probable pitchers: {len(starting_pitchers)}")
            
            # For hitters: Only players with batting order (1-9)
            hitters = slate_df[slate_df['Position'] != 'P'].copy()
            starting_hitters = hitters[hitters['Batting Order'].notna() & (hitters['Batting Order'] != '')]
            logger.info(f"   SUCCESS: Hitters with batting order: {len(starting_hitters)}")
            
            # Combine confirmed starters only
            slate_df = pd.concat([starting_pitchers, starting_hitters], ignore_index=True)
            logger.info(f"LINEUP: CONFIRMED STARTERS: {len(slate_df)} players")
        
        # Clean and standardize data
        confirmed_starters = slate_df.copy()
        
        # Handle different column formats between files
        if 'Nickname' in confirmed_starters.columns:
            # Starters-only file format
            confirmed_starters['player_name'] = confirmed_starters['Nickname']
        elif 'First Name' in confirmed_starters.columns and 'Last Name' in confirmed_starters.columns:
            # Main slate file format
            confirmed_starters['player_name'] = confirmed_starters['First Name'] + ' ' + confirmed_starters['Last Name']
        else:
            logger.error("ERROR: Cannot find player name columns")
            return None
            
        confirmed_starters = confirmed_starters[['player_name', 'Position', 'Team', 'Salary', 'FPPG']].copy()
        confirmed_starters.columns = ['player_name', 'position', 'team', 'salary', 'projected_fppg']
        
        # Add ownership projections based on salary and FPPG
        confirmed_starters['ownership_proj'] = calculate_ownership_projections(confirmed_starters)
        
        # Log teams and positions available
        teams = sorted(confirmed_starters['team'].unique())
        positions = confirmed_starters['position'].value_counts()
        logger.info(f"    Teams: {teams}")
        logger.info(f"    Positions: {dict(positions)}")
        
        return confirmed_starters
        
    except Exception as e:
        logger.error(f"ERROR: Error loading slate: {e}")
        return None

def calculate_ownership_projections(df):
    """Calculate realistic ownership projections based on salary and FPPG"""
    # High salary + high FPPG = high ownership
    # Low salary + high value = medium ownership  
    # Expensive + low FPPG = low ownership
    
    df['value'] = df['projected_fppg'] / df['salary'] * 1000  # Value per $1K
    
    ownership = []
    for _, player in df.iterrows():
        if player['salary'] >= 8000:  # Expensive players
            if player['projected_fppg'] >= 30:  # High FPPG
                own = np.random.uniform(15, 35)  # Popular studs
            else:
                own = np.random.uniform(3, 12)   # Expensive but low projection
        elif player['salary'] <= 3000:  # Cheap players
            if player['value'] >= 3.5:  # Good value
                own = np.random.uniform(8, 20)   # Popular value plays
            else:
                own = np.random.uniform(2, 8)    # True punts
        else:  # Mid-range players
            own = np.random.uniform(5, 15)       # Medium ownership
        
        ownership.append(own)
    
    return ownership

def build_lineup(slate_df, strategy_num=1, salary_cap=35000):
    """Build a single optimized lineup with proper salary management"""
    
    # Set strategy seed for consistent but varied results
    np.random.seed(strategy_num * 17)
    
    lineup = []
    remaining_salary = salary_cap
    
    # Expand multi-position players for better availability
    expanded_slate = []
    for _, player in slate_df.iterrows():
        positions = player['position'].split('/')
        for pos in positions:
            if pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                new_row = player.copy()
                new_row['position'] = pos
                expanded_slate.append(new_row)
    
    slate_df = pd.DataFrame(expanded_slate)
    
    # Position requirements for FanDuel
    position_order = ['P', 'OF', 'OF', 'OF', '1B', '3B', 'SS', '2B', 'C']
    
    for i, pos in enumerate(position_order):
        available = slate_df[slate_df['position'] == pos].copy()
        
        if len(available) == 0:
            logger.warning(f"WARNING: No {pos} available")
            return None
            
        # Calculate budget management
        positions_left = len(position_order) - i - 1
        min_remaining_budget = positions_left * 2000  # $2K min per remaining position
        max_affordable = remaining_salary - min_remaining_budget
        
        # Filter by affordability
        affordable = available[available['salary'] <= max_affordable]
        
        if len(affordable) == 0:
            # Emergency: Take cheapest available
            affordable = available.nsmallest(1, 'salary')
            logger.warning(f"WARNING: Emergency selection for {pos}")
        
        # Strategy selection based on lineup number
        chosen = select_player_by_strategy(affordable, strategy_num, remaining_salary)
        
        if chosen is None:
            logger.warning(f"WARNING: No player selected for {pos}")
            return None
        
        # Add to lineup
        lineup.append({
            'player_name': chosen['player_name'],
            'position': chosen['position'],
            'team': chosen['team'],
            'salary': chosen['salary'],
            'projected_fppg': chosen['projected_fppg'],
            'ownership': chosen['ownership_proj']
        })
        
        remaining_salary -= chosen['salary']
        
        # Remove selected player from pool
        slate_df = slate_df[slate_df['player_name'] != chosen['player_name']]
    
    return lineup if len(lineup) == 9 else None

def select_player_by_strategy(affordable, strategy_num, remaining_salary):
    """Select player based on strategy"""
    
    if len(affordable) == 0:
        return None
    
    # Strategy rotation
    strategy_type = (strategy_num - 1) % 5
    
    if strategy_type == 0:  # Pure ceiling
        return affordable.nlargest(1, 'projected_fppg').iloc[0]
        
    elif strategy_type == 1:  # Pure value
        affordable['value'] = affordable['projected_fppg'] / affordable['salary']
        return affordable.nlargest(1, 'value').iloc[0]
        
    elif strategy_type == 2:  # Contrarian (low ownership)
        return affordable.nsmallest(1, 'ownership_proj').iloc[0]
        
    elif strategy_type == 3:  # Stars and scrubs
        if remaining_salary > 8000:  # Spend up on studs
            expensive = affordable[affordable['salary'] >= 6000]
            if len(expensive) > 0:
                return expensive.nlargest(1, 'projected_fppg').iloc[0]
        # Otherwise go cheap
        return affordable.nsmallest(1, 'salary').iloc[0]
        
    else:  # Balanced approach
        affordable['score'] = (affordable['projected_fppg'] * 0.6 + 
                             (affordable['projected_fppg'] / affordable['salary']) * 0.4)
        return affordable.nlargest(1, 'score').iloc[0]

def generate_daily_lineups(slate_df, num_lineups=10):
    """Generate multiple unique lineups for today"""
    logger.info(f"LINEUP: Generating {num_lineups} unique lineups...")
    
    lineups = []
    used_combinations = set()
    
    for i in range(1, num_lineups + 1):
        logger.info(f"Building lineup {i}...")
        
        attempts = 0
        max_attempts = 50
        
        while attempts < max_attempts:
            # Use fresh copy for each attempt
            slate_copy = slate_df.copy()
            lineup = build_lineup(slate_copy, i)
            
            if lineup and len(lineup) == 9:
                # Check for uniqueness
                player_names = tuple(sorted([p['player_name'] for p in lineup]))
                
                if player_names not in used_combinations:
                    used_combinations.add(player_names)
                    
                    total_salary = sum(p['salary'] for p in lineup)
                    total_projected = sum(p['projected_fppg'] for p in lineup)
                    avg_ownership = np.mean([p['ownership'] for p in lineup])
                    
                    lineups.append({
                        'lineup_id': f"daily_lineup_{i}",
                        'players': lineup,
                        'total_salary': total_salary,
                        'projected_fppg': total_projected,
                        'avg_ownership': avg_ownership
                    })
                    
                    logger.info(f"SUCCESS: Lineup {i}: ${total_salary:,} salary, {total_projected:.1f} FPPG")
                    break
            
            attempts += 1
        
        if attempts >= max_attempts:
            logger.warning(f"WARNING: Could not generate unique lineup {i}")
    
    logger.info(f"SUCCESS: Generated {len(lineups)} unique lineups")
    return lineups

def save_daily_lineups(lineups):
    """Save lineups in FanDuel format and detailed analysis"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. FanDuel submission format
    fanduel_lineups = []
    for lineup_data in lineups:
        players = lineup_data['players']
        
        # Create FanDuel row
        fd_row = {'Lineup': lineup_data['lineup_id']}
        
        for player in players:
            pos = player['position']
            if pos == 'OF':
                # Handle multiple OF positions
                of_count = sum(1 for p in players[:players.index(player)] if p['position'] == 'OF')
                pos = f"OF{of_count + 1}"
            
            fd_row[pos] = f"{player['player_name']} ({player['team']})"
        
        fd_row['Total_Salary'] = lineup_data['total_salary']
        fd_row['Projected_FPPG'] = round(lineup_data['projected_fppg'], 1)
        fd_row['Avg_Ownership'] = round(lineup_data['avg_ownership'], 1)
        
        fanduel_lineups.append(fd_row)
    
    # Save FanDuel format
    fd_df = pd.DataFrame(fanduel_lineups)
    fd_file = f"../data/daily_lineups_fanduel_{timestamp}.csv"
    fd_df.to_csv(fd_file, index=False)
    
    # 2. Detailed analysis format
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
                'ownership_proj': player['ownership'],
                'value': round(player['projected_fppg'] / player['salary'] * 1000, 2)
            })
    
    details_df = pd.DataFrame(lineup_details)
    details_file = f"../data/daily_lineup_details_{timestamp}.csv"
    details_df.to_csv(details_file, index=False)
    
    # 3. Summary statistics
    summary_stats = {
        'timestamp': timestamp,
        'total_lineups': len(lineups),
        'avg_salary': np.mean([l['total_salary'] for l in lineups]),
        'avg_projected_fppg': np.mean([l['projected_fppg'] for l in lineups]),
        'avg_ownership': np.mean([l['avg_ownership'] for l in lineups]),
        'salary_range': f"${min([l['total_salary'] for l in lineups]):,} - ${max([l['total_salary'] for l in lineups]):,}",
        'fppg_range': f"{min([l['projected_fppg'] for l in lineups]):.1f} - {max([l['projected_fppg'] for l in lineups]):.1f}"
    }
    
    logger.info(f" Saved FanDuel format: {fd_file}")
    logger.info(f" Saved detailed analysis: {details_file}")
    
    return fd_file, details_file, summary_stats

def main():
    """Main execution for daily lineup generation"""
    
    logger.info("TARGET: DAILY LINEUP GENERATOR")
    logger.info("=" * 50)
    
    # Load current slate with confirmed starters only
    slate_df = load_current_slate()
    
    if slate_df is None or len(slate_df) == 0:
        logger.error("ERROR: No confirmed starters available - cannot generate lineups")
        return
    
    # Generate lineups
    lineups = generate_daily_lineups(slate_df, num_lineups=10)
    
    if len(lineups) == 0:
        logger.error("ERROR: No lineups generated")
        return
    
    # Save results
    fd_file, details_file, stats = save_daily_lineups(lineups)
    
    # Display summary
    print(f"\nLINEUP: DAILY LINEUP GENERATION COMPLETE")
    print("=" * 60)
    print(f"DATA: Generated: {stats['total_lineups']} unique lineups")
    print(f"MONEY: Avg Salary: ${stats['avg_salary']:,.0f} ({stats['salary_range']})")
    print(f"TARGET: Avg FPPG: {stats['avg_projected_fppg']:.1f} ({stats['fppg_range']})")
    print(f"OWNERSHIP: Avg Ownership: {stats['avg_ownership']:.1f}%")
    print(f" FanDuel Format: {fd_file}")
    print(f" Detailed Analysis: {details_file}")
    
    logger.info("SUCCESS: Daily lineups ready for submission!")

if __name__ == "__main__":
    main()
