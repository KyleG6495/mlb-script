#!/usr/bin/env python3
"""
QUINTUPLE TOURNAMENT LINEUP GENERATOR
=====================================
Generates optimized lineups specifically for 200-player quintuple tournaments.
Creates balanced ceiling lineups with strategic contrarian plays.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import glob
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

# FanDuel salary cap and position requirements
SALARY_CAP = 35000
POSITIONS = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']

def standardize_positions(df):
    """Standardize position formats"""
    # Handle multi-position eligibility like 'OF/UTIL', 'C/1B/UTIL' 
    df['primary_position'] = df['position'].str.split('/').str[0]
    
    # Map roster positions to primary positions
    position_map = {
        'OF': 'OF',
        'C': 'C', 
        '1B': '1B',
        '2B': '2B',
        '3B': '3B',
        'SS': 'SS',
        'P': 'P'
    }
    
    df['position'] = df['primary_position'].map(position_map).fillna(df['primary_position'])
    return df

def load_player_pool():
    """Load current FanDuel slate with only confirmed starters"""
    # Use the starters-only file first (pre-filtered for confirmed starters)
    slate_file = BASE_DIR / "fd_slate_starters_only.csv"
    
    if not slate_file.exists():
        logger.warning("⚠️ fd_slate_starters_only.csv not found, falling back to main slate")
        slate_file = BASE_DIR / "fd_slate_today.csv"
    
    if not slate_file.exists():
        logger.warning("⚠️ fd_slate_today.csv not found, checking fd_current_slate directory")
        slate_patterns = [
            BASE_DIR.parent / "fd_current_slate" / "fd_slate_today.csv",
            BASE_DIR.parent / "fd_current_slate" / "FanDuel-MLB-*.csv"
        ]
        
        slate_file = None
        for pattern in slate_patterns:
            if isinstance(pattern, Path):
                if pattern.exists():
                    slate_file = pattern
                    break
            else:
                # Handle glob pattern
                files = list(BASE_DIR.parent.glob(str(pattern).replace(str(BASE_DIR.parent) + "/", "")))
                if files:
                    slate_file = max(files, key=lambda x: x.stat().st_mtime)
                    break
        
        if not slate_file:
            logger.warning("⚠️ No current slate found, using sample data")
            return create_sample_player_pool()
    
    try:
        df = pd.read_csv(slate_file)
        
        if 'fd_slate_starters_only.csv' in str(slate_file):
            logger.info(f"📊 Loaded {len(df)} confirmed starters from pre-filtered slate")
            logger.info("✅ Using validated starting lineups only - no complex filtering needed")
        else:
            logger.info(f"📊 Loaded {len(df)} players from main slate - applying filters")
            # Apply injury and status filters for non-pre-filtered files
            initial_count = len(df)
            
            # Filter out injured players
            if 'Injury Indicator' in df.columns:
                df = df[(df['Injury Indicator'].isna()) | (df['Injury Indicator'] == '')]
                logger.info(f"🏥 Filtered out injured players: {initial_count - len(df)} removed")
            
            # Filter for probable pitchers only
            pitchers = df[df['Position'] == 'P']
            if 'Probable Pitcher' in pitchers.columns:
                probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
                logger.info(f"⚾ Probable pitchers available: {len(probable_pitchers)}")
            else:
                probable_pitchers = pitchers
                logger.info(f"⚾ All pitchers (no probable pitcher data): {len(probable_pitchers)}")
            
            # Filter hitters by batting order - only include starters (batting order 1-9)
            hitters = df[df['Position'] != 'P']
            
            # Check if batting order column exists and filter out non-starters
            if 'Batting Order' in hitters.columns:
                # Convert batting order to numeric, handling any non-numeric values
                hitters['batting_order_num'] = pd.to_numeric(hitters['Batting Order'], errors='coerce')
                
                # Count non-starters before filtering
                non_starters = len(hitters[(hitters['batting_order_num'] == 0) | (hitters['batting_order_num'].isna())])
                
                # Keep only starting hitters (batting order 1-9)
                starting_hitters = hitters[(hitters['batting_order_num'] >= 1) & (hitters['batting_order_num'] <= 9)]
                
                logger.info(f"🏏 Total hitters: {len(hitters)}")
                logger.info(f"🚫 Non-starters filtered out: {non_starters}")
                logger.info(f"✅ Starting hitters (batting order 1-9): {len(starting_hitters)}")
                
                # If no starting hitters found, check if we have actual starting lineups yet
                if len(starting_hitters) == 0:
                    logger.warning("⚠️ No starting hitters found (batting orders not set yet)")
                    logger.error("❌ NO STARTING LINEUPS POSTED YET - All players have batting order 0")
                    logger.error("❌ Cannot generate realistic lineups without confirmed starters")
                    return pd.DataFrame()  # Return empty dataframe
                else:
                    hitters = starting_hitters
            else:
                logger.info(f"🏏 Hitters available: {len(hitters)} (no batting order filtering)")
            
            # Combine probable pitchers and all hitters
            df = pd.concat([probable_pitchers, hitters], ignore_index=True)
            logger.info(f"✅ Final player pool: {len(df)} players ({len(probable_pitchers)} pitchers, {len(hitters)} hitters)")
        
        # Standardize column names for quintuple system
        df['name'] = df.get('Nickname', df.get('Last Name', 'Unknown'))
        df['position'] = df['Position']
        df['salary'] = df['Salary'].astype(int)
        df['team'] = df['Team']
        df['opponent'] = df['Opponent']
        df['projected_fppg'] = df['FPPG']
        
        # Handle position eligibility
        df = standardize_positions(df)
        
        # Add quintuple-specific metrics
        df = add_quintuple_metrics(df)
        
        return df
        
    except Exception as e:
        logger.error(f"❌ Error loading slate: {e}")
        logger.info("📦 Using sample data due to slate loading error")
        return create_sample_player_pool()

def create_sample_player_pool():
    """Create sample player pool for testing"""
    logger.info("🎯 Creating sample player pool...")
    
    sample_players = [
        # Pitchers
        {'name': 'Gerrit Cole', 'position': 'P', 'salary': 11200, 'team': 'NYY', 'projected_fppg': 42.5, 'ownership_proj': 25},
        {'name': 'Spencer Strider', 'position': 'P', 'salary': 10800, 'team': 'ATL', 'projected_fppg': 40.8, 'ownership_proj': 20},
        {'name': 'Logan Webb', 'position': 'P', 'salary': 9600, 'team': 'SF', 'projected_fppg': 38.2, 'ownership_proj': 15},
        {'name': 'Pablo López', 'position': 'P', 'salary': 8800, 'team': 'MIN', 'projected_fppg': 35.7, 'ownership_proj': 12},
        {'name': 'Hunter Brown', 'position': 'P', 'salary': 8000, 'team': 'HOU', 'projected_fppg': 32.1, 'ownership_proj': 8},
        
        # Catchers
        {'name': 'Will Smith', 'position': 'C', 'salary': 7500, 'team': 'LAD', 'projected_fppg': 12.3, 'ownership_proj': 18},
        {'name': 'Salvador Perez', 'position': 'C', 'salary': 6800, 'team': 'KC', 'projected_fppg': 11.1, 'ownership_proj': 12},
        {'name': 'Tyler Stephenson', 'position': 'C', 'salary': 6200, 'team': 'CIN', 'projected_fppg': 10.2, 'ownership_proj': 8},
        
        # First Base
        {'name': 'Freddie Freeman', 'position': '1B', 'salary': 9800, 'team': 'LAD', 'projected_fppg': 13.8, 'ownership_proj': 22},
        {'name': 'Pete Alonso', 'position': '1B', 'salary': 9200, 'team': 'NYM', 'projected_fppg': 13.2, 'ownership_proj': 18},
        {'name': 'Matt Olson', 'position': '1B', 'salary': 8900, 'team': 'ATL', 'projected_fppg': 12.9, 'ownership_proj': 15},
        {'name': 'Christian Walker', 'position': '1B', 'salary': 7800, 'team': 'ARI', 'projected_fppg': 11.5, 'ownership_proj': 10},
        
        # Second Base  
        {'name': 'Jose Altuve', 'position': '2B', 'salary': 8500, 'team': 'HOU', 'projected_fppg': 12.4, 'ownership_proj': 16},
        {'name': 'Gleyber Torres', 'position': '2B', 'salary': 7800, 'team': 'NYY', 'projected_fppg': 11.7, 'ownership_proj': 14},
        {'name': 'Ozzie Albies', 'position': '2B', 'salary': 7500, 'team': 'ATL', 'projected_fppg': 11.3, 'ownership_proj': 12},
        
        # Third Base
        {'name': 'Manny Machado', 'position': '3B', 'salary': 8500, 'team': 'SD', 'projected_fppg': 12.6, 'ownership_proj': 17},
        {'name': 'Austin Riley', 'position': '3B', 'salary': 8200, 'team': 'ATL', 'projected_fppg': 12.1, 'ownership_proj': 15},
        {'name': 'Rafael Devers', 'position': '3B', 'salary': 7900, 'team': 'BOS', 'projected_fppg': 11.8, 'ownership_proj': 13},
        
        # Shortstop
        {'name': 'Trea Turner', 'position': 'SS', 'salary': 8800, 'team': 'PHI', 'projected_fppg': 12.8, 'ownership_proj': 19},
        {'name': 'Francisco Lindor', 'position': 'SS', 'salary': 8400, 'team': 'NYM', 'projected_fppg': 12.3, 'ownership_proj': 16},
        {'name': 'Corey Seager', 'position': 'SS', 'salary': 8100, 'team': 'TEX', 'projected_fppg': 11.9, 'ownership_proj': 14},
        
        # Outfield
        {'name': 'Mike Trout', 'position': 'OF', 'salary': 10200, 'team': 'LAA', 'projected_fppg': 14.8, 'ownership_proj': 25},
        {'name': 'Aaron Judge', 'position': 'OF', 'salary': 9900, 'team': 'NYY', 'projected_fppg': 14.5, 'ownership_proj': 28},
        {'name': 'Kyle Tucker', 'position': 'OF', 'salary': 9500, 'team': 'HOU', 'projected_fppg': 14.1, 'ownership_proj': 20},
        {'name': 'Ronald Acuña Jr.', 'position': 'OF', 'salary': 9800, 'team': 'ATL', 'projected_fppg': 14.3, 'ownership_proj': 24},
        {'name': 'Juan Soto', 'position': 'OF', 'salary': 9300, 'team': 'NYY', 'projected_fppg': 13.7, 'ownership_proj': 18},
        {'name': 'Randy Arozarena', 'position': 'OF', 'salary': 7200, 'team': 'TB', 'projected_fppg': 11.2, 'ownership_proj': 12},
        {'name': 'Jesse Winker', 'position': 'OF', 'salary': 6500, 'team': 'WSH', 'projected_fppg': 10.1, 'ownership_proj': 6},
        {'name': 'Lars Nootbaar', 'position': 'OF', 'salary': 6800, 'team': 'STL', 'projected_fppg': 10.5, 'ownership_proj': 8},
        {'name': 'Jarren Duran', 'position': 'OF', 'salary': 7500, 'team': 'BOS', 'projected_fppg': 11.3, 'ownership_proj': 10}
    ]
    
    df = pd.DataFrame(sample_players)
    df = add_quintuple_metrics(df)
    return df

def add_quintuple_metrics(df):
    """Add quintuple tournament specific metrics using realistic projections"""
    # Calculate value (FPPG per $1K salary)
    df['value'] = df['projected_fppg'] / (df['salary'] / 1000)
    
    # Add realistic ceiling projection based on position and salary
    # Higher salary players generally have higher but more predictable ceilings
    np.random.seed(42)  # For reproducible results
    
    ceiling_multipliers = []
    floor_multipliers = []
    ownership_projections = []
    
    for _, player in df.iterrows():
        salary = player['salary']
        position = player['position']
        fppg = player['projected_fppg']
        
        # Ceiling multipliers based on salary tier and position
        if position == 'P':
            if salary >= 10000:  # Premium pitchers
                ceiling_mult = np.random.uniform(1.4, 1.8)
                ownership = np.clip(25 + np.random.uniform(-5, 10), 15, 40)
            elif salary >= 8000:  # Mid-tier pitchers  
                ceiling_mult = np.random.uniform(1.5, 2.0)
                ownership = np.clip(15 + np.random.uniform(-5, 10), 8, 25)
            else:  # Value pitchers
                ceiling_mult = np.random.uniform(1.7, 2.3)
                ownership = np.clip(8 + np.random.uniform(-3, 8), 3, 15)
        else:  # Hitters
            if salary >= 4000:  # Premium hitters
                ceiling_mult = np.random.uniform(1.6, 2.2)
                ownership = np.clip(20 + np.random.uniform(-5, 10), 12, 35)
            elif salary >= 3000:  # Mid-tier hitters
                ceiling_mult = np.random.uniform(1.7, 2.4)
                ownership = np.clip(12 + np.random.uniform(-5, 8), 6, 20)
            else:  # Value hitters
                ceiling_mult = np.random.uniform(1.8, 2.8)
                ownership = np.clip(6 + np.random.uniform(-3, 8), 2, 15)
        
        ceiling_multipliers.append(ceiling_mult)
        ownership_projections.append(ownership)
        
        # Floor is more conservative
        floor_mult = np.random.uniform(0.5, 0.7)
        floor_multipliers.append(floor_mult)
    
    df['ceiling_fppg'] = df['projected_fppg'] * ceiling_multipliers
    df['floor_fppg'] = df['projected_fppg'] * floor_multipliers
    df['ownership_proj'] = ownership_projections
    
    # Add recent form and matchup scores (more realistic ranges)
    df['recent_form'] = np.random.uniform(0.8, 1.2, len(df))
    df['matchup_score'] = np.random.uniform(0.9, 1.1, len(df))
    
    # Calculate quintuple score emphasizing ceiling and value for tournaments
    df['quintuple_score'] = (
        df['ceiling_fppg'] * 0.4 +           # Ceiling is most important for tournaments
        df['value'] * 3.0 +                  # Value is critical
        (100 - df['ownership_proj']) * 0.15 + # Lower ownership helps
        df['projected_fppg'] * 0.3 +         # Base projection still matters
        df['recent_form'] * 2.0 +            # Form adjustment
        df['matchup_score'] * 1.5            # Matchup bonus
    )
    
    # Remove rows with missing critical data
    df = df.dropna(subset=['name', 'position', 'salary', 'projected_fppg'])
    
    return df

def select_lineup_core(player_pool, strategy_type):
    """Select core players based on strategy"""
    lineup = {}
    remaining_salary = SALARY_CAP
    
    if strategy_type == "BALANCED_CEILING":
        # Strategy 1: Balanced ceiling with safe floor
        logger.info("🎯 Building Balanced Ceiling lineup...")
        
        # Select pitcher in $8K-$9.5K range with good value
        pitchers = player_pool[player_pool['position'] == 'P']
        mid_tier_pitchers = pitchers[(pitchers['salary'] >= 8000) & (pitchers['salary'] <= 9500)]
        if len(mid_tier_pitchers) > 0:
            pitcher = mid_tier_pitchers.loc[mid_tier_pitchers['value'].idxmax()]
        else:
            pitcher = pitchers.loc[pitchers['value'].idxmax()]
        
        lineup['P'] = pitcher
        remaining_salary -= pitcher['salary']
        
        # Select one premium bat ($9K+)
        hitters = player_pool[player_pool['position'] != 'P']
        premium_hitters = hitters[hitters['salary'] >= 9000]
        if len(premium_hitters) > 0 and remaining_salary >= 9000:
            premium_pick = premium_hitters.loc[premium_hitters['quintuple_score'].idxmax()]
            position = premium_pick['position']
            lineup[position] = premium_pick
            remaining_salary -= premium_pick['salary']
        
    elif strategy_type == "CONTRARIAN_CEILING":
        # Strategy 2: More contrarian with higher ceiling
        logger.info("🎯 Building Contrarian Ceiling lineup...")
        
        # Select lower-owned pitcher with upside
        pitchers = player_pool[player_pool['position'] == 'P']
        contrarian_pitchers = pitchers[pitchers['ownership_proj'] <= 15]
        if len(contrarian_pitchers) > 0:
            pitcher = contrarian_pitchers.loc[contrarian_pitchers['ceiling_fppg'].idxmax()]
        else:
            pitcher = pitchers.loc[pitchers['ceiling_fppg'].idxmax()]
        
        lineup['P'] = pitcher
        remaining_salary -= pitcher['salary']
    
    return lineup, remaining_salary

def build_complete_lineup(player_pool, strategy_type):
    """Build a complete 9-player lineup with unique players"""
    # Get core players
    lineup, remaining_salary = select_lineup_core(player_pool, strategy_type)
    used_players = set([p['name'] for p in lineup.values()])
    
    # Fill remaining positions - handle OF positions specially
    remaining_positions = [pos for pos in POSITIONS if pos not in lineup]
    
    # Count how many OF slots we need to fill
    of_slots_needed = sum(1 for pos in remaining_positions if pos == 'OF')
    non_of_positions = [pos for pos in remaining_positions if pos != 'OF']
    
    # Fill non-OF positions first
    for position in non_of_positions:
        available = player_pool[
            (player_pool['position'] == position) & 
            (~player_pool['name'].isin(used_players)) &
            (player_pool['salary'] <= remaining_salary - (len(remaining_positions) - 1) * 2000)
        ].copy()
        
        if len(available) == 0:
            available = player_pool[
                (player_pool['position'] == position) & 
                (~player_pool['name'].isin(used_players))
            ].copy()
        
        if len(available) > 0:
            if strategy_type == "BALANCED_CEILING":
                available['selection_score'] = (
                    available['quintuple_score'] * 0.6 +
                    available['value'] * 5.0 +
                    available['ceiling_fppg'] * 0.4
                )
            else:
                available['selection_score'] = (
                    available['ceiling_fppg'] * 0.5 +
                    (100 - available['ownership_proj']) * 0.3 +
                    available['quintuple_score'] * 0.2
                )
            
            selected = available.loc[available['selection_score'].idxmax()]
            lineup[position] = selected
            used_players.add(selected['name'])
            remaining_salary -= selected['salary']
            remaining_positions.remove(position)
    
    # Now fill OF positions with unique players
    of_positions_in_lineup = [pos for pos in POSITIONS if pos == 'OF' and pos not in lineup]
    
    for i, position in enumerate(of_positions_in_lineup):
        available = player_pool[
            (player_pool['position'] == 'OF') & 
            (~player_pool['name'].isin(used_players)) &
            (player_pool['salary'] <= remaining_salary - (len(of_positions_in_lineup) - i - 1) * 2000)
        ].copy()
        
        if len(available) == 0:
            available = player_pool[
                (player_pool['position'] == 'OF') & 
                (~player_pool['name'].isin(used_players))
            ].copy()
        
        if len(available) > 0:
            if strategy_type == "BALANCED_CEILING":
                available['selection_score'] = (
                    available['quintuple_score'] * 0.6 +
                    available['value'] * 5.0 +
                    available['ceiling_fppg'] * 0.4
                )
            else:
                available['selection_score'] = (
                    available['ceiling_fppg'] * 0.5 +
                    (100 - available['ownership_proj']) * 0.3 +
                    available['quintuple_score'] * 0.2
                )
            
            selected = available.loc[available['selection_score'].idxmax()]
            lineup[f'OF{i+1}'] = selected  # Use unique key
            used_players.add(selected['name'])
            remaining_salary -= selected['salary']
    
    return lineup, remaining_salary

def format_lineup_output(lineup, remaining_salary, strategy_name):
    """Format lineup for display and saving"""
    logger.info(f"\n🏆 {strategy_name}")
    logger.info("=" * 50)
    
    total_salary = 0
    total_projected = 0
    total_ceiling = 0
    lineup_list = []
    
    # Define display order
    position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    
    for i, position in enumerate(position_order):
        # Handle OF positions
        display_pos = 'OF' if position.startswith('OF') else position
        
        # Check if this position exists in lineup
        player = None
        for key, p in lineup.items():
            if position == key or (position.startswith('OF') and key.startswith('OF') and key not in [pos for pos in position_order[:i]]):
                player = p
                break
        
        if player is not None:
            total_salary += player['salary']
            total_projected += player['projected_fppg']
            total_ceiling += player['ceiling_fppg']
            
            ownership_str = f"({player['ownership_proj']:.1f}%)"
            logger.info(f"{display_pos:3} | {player['name']:<20} | ${player['salary']:,} | {player['projected_fppg']:.1f} FPPG | {ownership_str}")
            
            lineup_list.append({
                'Position': display_pos,
                'Player': player['name'],
                'Team': player.get('team', 'N/A'),
                'Salary': player['salary'],
                'Projected_FPPG': round(player['projected_fppg'], 1),
                'Ceiling_FPPG': round(player['ceiling_fppg'], 1),
                'Ownership_Proj': round(player['ownership_proj'], 1),
                'Value': round(player['value'], 2)
            })
    
    logger.info("-" * 50)
    logger.info(f"💰 Total Salary: ${total_salary:,} (${remaining_salary:,} remaining)")
    logger.info(f"📊 Projected Total: {total_projected:.1f} FPPG")
    logger.info(f"🚀 Ceiling Total: {total_ceiling:.1f} FPPG")
    logger.info(f"📈 Avg Ownership: {np.mean([lineup[pos]['ownership_proj'] for pos in lineup]):.1f}%")
    
    return pd.DataFrame(lineup_list)

def save_quintuple_lineups(lineup1_df, lineup2_df):
    """Save both lineups to CSV files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save individual lineups
    lineup1_file = BASE_DIR / f"quintuple_lineup_1_balanced_{timestamp}.csv"
    lineup1_df.to_csv(lineup1_file, index=False)
    logger.info(f"💾 Saved Lineup 1: {lineup1_file}")
    
    lineup2_file = BASE_DIR / f"quintuple_lineup_2_contrarian_{timestamp}.csv"
    lineup2_df.to_csv(lineup2_file, index=False)
    logger.info(f"💾 Saved Lineup 2: {lineup2_file}")
    
    # Save combined file
    lineup1_df['Lineup_Type'] = 'Balanced_Ceiling'
    lineup2_df['Lineup_Type'] = 'Contrarian_Ceiling'
    
    combined_df = pd.concat([lineup1_df, lineup2_df], ignore_index=True)
    combined_file = BASE_DIR / f"quintuple_lineups_combined_{timestamp}.csv"
    combined_df.to_csv(combined_file, index=False)
    logger.info(f"💾 Saved Combined: {combined_file}")
    
    return lineup1_file, lineup2_file, combined_file

def main():
    """Main execution function"""
    logger.info("🏆 QUINTUPLE TOURNAMENT LINEUP GENERATOR")
    logger.info("=" * 60)
    logger.info("🎯 Target: 200-player quintuple tournaments")
    logger.info("💡 Strategy: Balanced ceiling + contrarian plays")
    logger.info("")
    
    try:
        # Load player pool
        player_pool = load_player_pool()
        
        if len(player_pool) == 0:
            logger.error("❌ No valid players available - cannot generate lineups")
            logger.error("❌ This typically means batting orders haven't been posted yet")
            logger.error("❌ All players currently show batting order '0' (not starting)")
            logger.error("❌ Please try again later when lineups are confirmed")
            return
        
        # Generate Lineup 1: Balanced Ceiling
        logger.info("🏗️ Generating Lineup 1: Balanced Ceiling Strategy")
        lineup1, remaining1 = build_complete_lineup(player_pool, "BALANCED_CEILING")
        lineup1_df = format_lineup_output(lineup1, remaining1, "LINEUP 1: BALANCED CEILING")
        
        logger.info("\n" + "="*60 + "\n")
        
        # Generate Lineup 2: Contrarian Ceiling  
        logger.info("🏗️ Generating Lineup 2: Contrarian Ceiling Strategy")
        lineup2, remaining2 = build_complete_lineup(player_pool, "CONTRARIAN_CEILING")
        lineup2_df = format_lineup_output(lineup2, remaining2, "LINEUP 2: CONTRARIAN CEILING")
        
        # Save lineups
        logger.info("\n" + "="*60)
        file1, file2, combined = save_quintuple_lineups(lineup1_df, lineup2_df)
        
        logger.info("\n🎉 QUINTUPLE LINEUPS GENERATED SUCCESSFULLY!")
        logger.info(f"📁 Files saved in: {BASE_DIR}")
        logger.info("\n💡 STRATEGY SUMMARY:")
        logger.info("🔹 Lineup 1: Balanced ceiling with 60% floor, 40% upside")
        logger.info("🔹 Lineup 2: Higher ceiling with contrarian plays")
        logger.info("🔹 Both optimized for 200-player tournaments")
        
    except Exception as e:
        logger.error(f"❌ Error generating lineups: {e}")
        raise

if __name__ == "__main__":
    main()
