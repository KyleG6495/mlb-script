#!/usr/bin/env python3
"""
UNIFIED DFS OPTIMIZATION SYSTEM
===============================
Single, comprehensive DFS lineup optimizer that consolidates all approaches.
This replaces all other DFS optimizer scripts.

Features:
- Multi-strategy optimization (floor/balanced/ceiling)
- Proper FanDuel constraints (P + C + 1B + 2B + 3B + SS + 3OF = 9 players)
- Enhanced projections with weather/park/matchup factors
- Lineup diversity enforcement
- Real-time validation and output formatting
- Single source of truth for all DFS optimization
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import logging
from datetime import datetime
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent / "data"
SCRIPTS_DIR = Path(__file__).resolve().parent
FD_SLATE_DIR = Path(__file__).resolve().parent.parent / "fd_current_slate"

# Input files
SLATE_FILE = FD_SLATE_DIR / "fd_slate_today.csv"
HITTER_FEATURES = BASE_DIR / "fd_hitter_features_final.csv" 
PITCHER_FEATURES = BASE_DIR / "fd_pitcher_features_final.csv"
WEATHER_PARK = BASE_DIR / "merged_weather_park.csv"

# Output files
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_LINEUPS = BASE_DIR / f"unified_dfs_lineups_{TIMESTAMP}.csv"
OUTPUT_SUMMARY = BASE_DIR / f"unified_dfs_summary_{TIMESTAMP}.csv" 
OUTPUT_FANDUEL = BASE_DIR / f"fanduel_submission_{TIMESTAMP}.csv"

# FanDuel salary cap and lineup structure
SALARY_CAP = 35000
LINEUP_SIZE = 9
POSITION_REQUIREMENTS = {
    'P': 1,
    'C': 1, 
    '1B': 1,
    '2B': 1,
    '3B': 1,
    'SS': 1,
    'OF': 3
}

# Strategy configurations
STRATEGIES = {
    'floor': {'count': 3, 'ceiling_weight': 0.1, 'floor_weight': 0.6, 'value_weight': 0.3},
    'balanced': {'count': 14, 'ceiling_weight': 0.3, 'floor_weight': 0.3, 'value_weight': 0.4},
    'ceiling': {'count': 3, 'ceiling_weight': 0.7, 'floor_weight': 0.1, 'value_weight': 0.2}
}

# =============================================================================
# LOGGING SETUP
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / f'dfs_optimization_{TIMESTAMP}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================================================================
# DATA LOADING AND PREPARATION
# =============================================================================
def load_slate_data():
    """Load and prepare FanDuel slate data"""
    logger.info("Loading FanDuel slate data...")
    
    if not SLATE_FILE.exists():
        raise FileNotFoundError(f"Slate file not found: {SLATE_FILE}")
        
    slate = pd.read_csv(SLATE_FILE)
    logger.info(f"Loaded {len(slate)} players from slate")
    
    # Filter for active players (exclude those with Batting Order = '0')
    # BUT keep starting pitchers (Probable Pitcher = 'Yes') regardless of batting order
    if 'Batting Order' in slate.columns:
        initial_count = len(slate)
        # Convert to string and handle various "0" representations
        slate['Batting Order'] = slate['Batting Order'].astype(str).str.strip()
        
        # Keep starting pitchers regardless of batting order
        starting_pitchers = slate[(slate['Position'] == 'P') & (slate['Probable Pitcher'] == 'Yes')]
        
        # Keep non-pitchers who have valid batting orders (not "0")
        active_non_pitchers = slate[
            (slate['Position'] != 'P') & 
            (~slate['Batting Order'].isin(['0', '0.0', 'nan', '']))
        ]
        
        # Combine active players
        slate = pd.concat([starting_pitchers, active_non_pitchers], ignore_index=True)
        filtered_count = len(slate)
        logger.info(f"After filtering out inactive players: {filtered_count} players (removed {initial_count - filtered_count})")
        logger.info(f"Kept {len(starting_pitchers)} starting pitchers and {len(active_non_pitchers)} active non-pitchers")
    
    # Extract player_id from FanDuel ID format (e.g., "118469-198625" -> "198625")
    if 'Id' in slate.columns:
        slate['player_id'] = slate['Id'].astype(str).str.split('-').str[1]
    elif 'player_id' not in slate.columns:
        raise ValueError("No player_id or Id column found in slate data")
    
    # Standardize salary column
    salary_col = 'Salary' if 'Salary' in slate.columns else 'salary'
    if salary_col not in slate.columns:
        raise ValueError("No salary column found in slate data")
    slate['salary'] = slate[salary_col].astype(int)
    
    # Standardize position column  
    pos_col = 'Position' if 'Position' in slate.columns else 'position'
    if pos_col not in slate.columns:
        raise ValueError("No position column found in slate data")
    slate['position'] = slate[pos_col]
    
    # Create display name
    if 'Nickname' in slate.columns and slate['Nickname'].notna().any():
        slate['name'] = slate['Nickname']
    elif 'First Name' in slate.columns and 'Last Name' in slate.columns:
        slate['name'] = slate['First Name'] + ' ' + slate['Last Name']
    else:
        slate['name'] = slate.get('Name', 'Unknown')
    
    return slate[['player_id', 'name', 'position', 'salary', 'Team']].copy()

def load_projections():
    """Load and merge projection data"""
    logger.info("Loading projection data...")
    
    # Load hitter projections
    hitters = pd.DataFrame()
    if HITTER_FEATURES.exists():
        hitters = pd.read_csv(HITTER_FEATURES)
        hitters['player_type'] = 'hitter'
        logger.info(f"Loaded {len(hitters)} hitter projections")
    
    # Load pitcher projections  
    pitchers = pd.DataFrame()
    if PITCHER_FEATURES.exists():
        pitchers = pd.read_csv(PITCHER_FEATURES)
        pitchers['player_type'] = 'pitcher'
        logger.info(f"Loaded {len(pitchers)} pitcher projections")
    
    # Combine projections
    if len(hitters) > 0 and len(pitchers) > 0:
        projections = pd.concat([hitters, pitchers], ignore_index=True)
    elif len(hitters) > 0:
        projections = hitters
    elif len(pitchers) > 0:
        projections = pitchers
    else:
        raise FileNotFoundError("No projection files found")
    
    # Ensure player_id is string
    projections['player_id'] = projections['player_id'].astype(str)
    
    return projections

def enhance_projections(df):
    """Apply enhancement factors to base projections"""
    logger.info("Enhancing projections...")
    
    # Base projection column (try multiple names)
    proj_cols = ['projected_fppg', 'FPPG', 'fppg', 'projection', 'proj_points', 'ml_projected_fppg', 'enhanced_fppg']
    proj_col = None
    for col in proj_cols:
        if col in df.columns:
            proj_col = col
            break
    
    if proj_col is None:
        raise ValueError(f"No projection column found. Available: {df.columns.tolist()}")
    
    df['base_fppg'] = df[proj_col].fillna(0)
    
    # Enhanced projection methodology
    try:
        df['salary_tier'] = pd.qcut(df['salary'], q=4, labels=['bargain', 'value', 'solid', 'premium'], duplicates='drop')
    except ValueError:
        # Fallback if we still have issues - use rank-based approach
        df['salary_rank'] = df['salary'].rank(pct=True)
        df['salary_tier'] = pd.cut(df['salary_rank'], 
                                  bins=[0, 0.25, 0.5, 0.75, 1.0], 
                                  labels=['bargain', 'value', 'solid', 'premium'])
    
    # Salary tier multipliers
    tier_multipliers = {'bargain': 1.15, 'value': 1.10, 'solid': 1.05, 'premium': 1.02}
    df['tier_multiplier'] = df['salary_tier'].map(tier_multipliers).astype(float)
    
    # Position scarcity (fewer available players = higher multiplier)
    pos_counts = df['primary_position'].value_counts()
    df['scarcity_multiplier'] = df['primary_position'].map(
        lambda x: 1.0 + (0.05 * (30 - pos_counts.get(x, 30)) / 30)
    ).astype(float)
    
    # Ensure base_fppg is numeric
    df['base_fppg'] = pd.to_numeric(df['base_fppg'], errors='coerce').fillna(0)
    
    # Calculate enhanced projections
    df['enhanced_fppg'] = (df['base_fppg'] * 
                          df['tier_multiplier'] * 
                          df['scarcity_multiplier'])
    
    # Ceiling/floor calculations
    df['ceiling_fppg'] = df['enhanced_fppg'] * 1.4
    df['floor_fppg'] = df['enhanced_fppg'] * 0.7
    
    # Value score
    df['value_score'] = df['enhanced_fppg'] / (df['salary'] / 1000)
    
    logger.info(f"Enhanced projections for {len(df)} players")
    return df

def prepare_optimization_data():
    """Load and prepare all data for optimization"""
    logger.info("Preparing optimization data...")
    
    # Load slate and projections
    slate = load_slate_data()
    projections = load_projections()
    
    # Merge slate with projections
    df = slate.merge(projections, on='player_id', how='left', suffixes=('', '_proj'))
    
    # Debug: Check pitcher data before filtering
    pitcher_count_before = len(df[df['position'].str.contains('P', na=False)])
    logger.info(f"Pitchers in slate before filtering: {pitcher_count_before}")
    
    # Handle missing projections - create base_fppg column if it doesn't exist
    if 'base_fppg' not in df.columns:
        # Try common projection column names
        proj_cols = ['projected_fppg', 'FPPG', 'fppg', 'projection', 'ml_projected_fppg', 'proj_points', 'enhanced_fppg']
        proj_col = None
        for col in proj_cols:
            if col in df.columns:
                proj_col = col
                break
        
        if proj_col is not None:
            df['base_fppg'] = df[proj_col].fillna(0)
            logger.info(f"Using {proj_col} as base projection column")
        else:
            logger.warning("No projection column found, creating base_fppg with salary-based estimates")
            # Use different salary multipliers for pitchers vs hitters
            df['base_fppg'] = df.apply(lambda row: 
                (row['salary'] / 1000 * 1.5) if 'P' in row['position'] else (row['salary'] / 1000 * 2.5), 
                axis=1)
    
    # Ensure base_fppg column exists and fill missing values
    if 'base_fppg' not in df.columns:
        logger.warning("base_fppg column still missing, creating from salary")
        df['base_fppg'] = df.apply(lambda row: 
            (row['salary'] / 1000 * 1.5) if 'P' in row['position'] else (row['salary'] / 1000 * 2.5), 
            axis=1)
    
    # Fill remaining missing projections (especially important for pitchers)
    missing_proj = df['base_fppg'].isna().sum()
    zero_proj = (df['base_fppg'] == 0).sum()
    if missing_proj > 0 or zero_proj > 0:
        logger.warning(f"{missing_proj} players missing projections, {zero_proj} with zero projections - EXCLUDING these players")
        # EXCLUDE players with zero/missing projections instead of using salary estimates
        # This prevents players like Rich Hill with 0.0 projections from being included
        df = df[df['base_fppg'] > 0].copy()
        logger.info(f"After excluding zero projection players: {len(df)} players remaining")
    
    # Create primary position (first position for multi-position players)
    df['primary_position'] = df['position'].str.split('/').str[0]
    
    # Debug: Check pitcher data after primary position creation
    pitcher_count_primary = len(df[df['primary_position'] == 'P'])
    logger.info(f"Pitchers after primary position creation: {pitcher_count_primary}")
    
    # Debug pitcher data before filtering
    pitcher_data_before = df[df['primary_position'] == 'P']
    logger.info(f"Sample pitcher data before filtering:")
    logger.info(f"  Sample salaries: {pitcher_data_before['salary'].head().tolist()}")
    logger.info(f"  Sample base_fppg: {pitcher_data_before['base_fppg'].head().tolist()}")
    logger.info(f"  base_fppg stats: min={pitcher_data_before['base_fppg'].min()}, max={pitcher_data_before['base_fppg'].max()}")
    
    # Filter valid players (now redundant base_fppg > 0 check but keeping for safety)
    df = df[
        (df['salary'] >= 2000) & 
        (df['salary'] <= 15000) &
        (df['base_fppg'] > 0) &
        (df['primary_position'].isin(['P', 'C', '1B', '2B', '3B', 'SS', 'OF']))
    ].copy()
    
    # Debug: Check pitcher data after filtering
    pitcher_count_after = len(df[df['primary_position'] == 'P'])
    logger.info(f"Pitchers after filtering: {pitcher_count_after}")
    
    # Debug: Check what's filtering out pitchers
    if pitcher_count_after == 0:
        pitcher_data = df[df['primary_position'] == 'P']
        logger.info(f"Debug - Pitcher filtering analysis:")
        logger.info(f"  Total pitchers before filter: {len(pitcher_data)}")
        logger.info(f"  Pitchers with salary >= 2000: {len(pitcher_data[pitcher_data['salary'] >= 2000])}")
        logger.info(f"  Pitchers with salary <= 15000: {len(pitcher_data[pitcher_data['salary'] <= 15000])}")
        logger.info(f"  Pitchers with base_fppg > 0: {len(pitcher_data[pitcher_data['base_fppg'] > 0])}")
        logger.info(f"  Sample pitcher base_fppg values: {pitcher_data['base_fppg'].head().tolist()}")
    
    logger.info(f"Sample pitcher data: {df[df['primary_position'] == 'P'][['name', 'salary', 'base_fppg']].head()}")
    
    # Enhance projections
    df = enhance_projections(df)
    
    logger.info(f"Prepared {len(df)} players for optimization")
    
    # Log position availability
    for pos in POSITION_REQUIREMENTS.keys():
        count = len(df[df['primary_position'] == pos])
        logger.info(f"Available {pos}: {count} players")
    
    return df

# =============================================================================
# OPTIMIZATION ENGINE
# =============================================================================
def optimize_lineup(df, strategy='balanced', exclude_players=None):
    """Optimize a single lineup using specified strategy"""
    
    if exclude_players is None:
        exclude_players = set()
    
    # Filter out excluded players
    available_df = df[~df['player_id'].isin(exclude_players)].copy()
    
    # Strategy weights
    weights = STRATEGIES[strategy]
    
    # Calculate composite score
    available_df['composite_score'] = (
        weights['ceiling_weight'] * available_df['ceiling_fppg'] +
        weights['floor_weight'] * available_df['floor_fppg'] + 
        weights['value_weight'] * available_df['value_score'] * 10
    )
    
    # Create optimization problem
    prob = LpProblem(f"FanDuel_Lineup_{strategy}", LpMaximize)
    
    # Decision variables
    player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in available_df.index}
    
    # Objective: maximize composite score
    prob += lpSum(available_df.loc[i, 'composite_score'] * player_vars[i] for i in available_df.index)
    
    # Constraints
    prob += lpSum(player_vars[i] for i in available_df.index) == LINEUP_SIZE
    prob += lpSum(available_df.loc[i, 'salary'] * player_vars[i] for i in available_df.index) <= SALARY_CAP
    
    # Position constraints
    for pos, required in POSITION_REQUIREMENTS.items():
        pos_players = available_df[available_df['primary_position'] == pos].index
        prob += lpSum(player_vars[i] for i in pos_players) == required
    
    # Solve
    solver = PULP_CBC_CMD(msg=False)
    prob.solve(solver)
    
    if prob.status != 1:  # Not optimal
        logger.warning(f"Optimization failed for {strategy} strategy")
        return None
    
    # Extract lineup
    selected_indices = [i for i in available_df.index if player_vars[i].value() == 1]
    lineup = available_df.loc[selected_indices].copy()
    
    # Add strategy info
    lineup['strategy'] = strategy
    lineup['lineup_total_salary'] = lineup['salary'].sum()
    lineup['lineup_enhanced_fppg'] = lineup['enhanced_fppg'].sum()
    lineup['lineup_ceiling_fppg'] = lineup['ceiling_fppg'].sum()
    lineup['lineup_floor_fppg'] = lineup['floor_fppg'].sum()
    
    return lineup

def generate_all_lineups(df):
    """Generate all lineups across strategies with diversity"""
    logger.info("Generating optimized lineups...")
    
    all_lineups = []
    used_players = set()
    lineup_id = 1
    
    for strategy, config in STRATEGIES.items():
        logger.info(f"Generating {config['count']} {strategy} lineups...")
        
        for i in range(config['count']):
            # Add some used players to exclusion for diversity
            exclude_set = set()
            if i > 0:  # Don't exclude on first lineup of each strategy
                # Exclude most frequently used players to force diversity
                player_usage = pd.Series(list(used_players)).value_counts()
                if len(player_usage) > 0:
                    most_used = player_usage.head(3).index.tolist()
                    exclude_set.update(most_used)
            
            lineup = optimize_lineup(df, strategy, exclude_set)
            
            if lineup is not None:
                lineup['lineup_id'] = lineup_id
                lineup['slot'] = range(1, len(lineup) + 1)
                all_lineups.append(lineup)
                
                # Track used players for diversity
                used_players.update(lineup['player_id'].tolist())
                lineup_id += 1
                
                logger.info(f"Generated {strategy} lineup {i+1}: "
                          f"${lineup['salary'].sum():,} salary, "
                          f"{lineup['enhanced_fppg'].sum():.1f} FPPG")
            else:
                logger.warning(f"Failed to generate {strategy} lineup {i+1}")
    
    if not all_lineups:
        raise ValueError("No valid lineups generated")
    
    return pd.concat(all_lineups, ignore_index=True)

# =============================================================================
# OUTPUT FORMATTING
# =============================================================================
def create_fanduel_submission(lineups_df):
    """Convert lineups to FanDuel submission format"""
    logger.info("Creating FanDuel submission format...")
    
    submission_data = []
    
    for lineup_id in lineups_df['lineup_id'].unique():
        lineup = lineups_df[lineups_df['lineup_id'] == lineup_id].copy()
        
        # Sort by position for consistent ordering
        position_order = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        lineup_ordered = []
        
        for pos in position_order:
            if pos == 'OF':
                of_players = lineup[lineup['primary_position'] == 'OF']
                if len(of_players) > 0:
                    lineup_ordered.append(of_players.iloc[0])
                    lineup = lineup.drop(of_players.iloc[0].name)
            else:
                pos_players = lineup[lineup['primary_position'] == pos]
                if len(pos_players) > 0:
                    lineup_ordered.append(pos_players.iloc[0])
                    lineup = lineup.drop(pos_players.iloc[0].name)
        
        if len(lineup_ordered) == 9:
            submission_row = {
                'P': lineup_ordered[0]['name'],
                'C': lineup_ordered[1]['name'], 
                '1B': lineup_ordered[2]['name'],
                '2B': lineup_ordered[3]['name'],
                '3B': lineup_ordered[4]['name'],
                'SS': lineup_ordered[5]['name'],
                'OF': lineup_ordered[6]['name'],
                'OF2': lineup_ordered[7]['name'],
                'OF3': lineup_ordered[8]['name'],
                'Lineup_ID': f"{lineup_ordered[0]['strategy'].upper()}_{lineup_id}",
                'Total_Salary': sum(p['salary'] for p in lineup_ordered),
                'Total_FPPG': sum(p['enhanced_fppg'] for p in lineup_ordered)
            }
            submission_data.append(submission_row)
    
    return pd.DataFrame(submission_data)

def save_outputs(lineups_df):
    """Save all output files"""
    logger.info("Saving optimization results...")
    
    # Save detailed lineups
    lineups_df.to_csv(OUTPUT_LINEUPS, index=False)
    logger.info(f"Detailed lineups saved: {OUTPUT_LINEUPS}")
    
    # Create and save summary
    summary_data = []
    for lineup_id in lineups_df['lineup_id'].unique():
        lineup = lineups_df[lineups_df['lineup_id'] == lineup_id]
        summary_data.append({
            'Lineup_ID': lineup_id,
            'Strategy': lineup['strategy'].iloc[0],
            'Total_Salary': lineup['salary'].sum(),
            'Total_Enhanced_FPPG': lineup['enhanced_fppg'].sum(),
            'Total_Ceiling_FPPG': lineup['ceiling_fppg'].sum(), 
            'Total_Floor_FPPG': lineup['floor_fppg'].sum(),
            'Avg_Value_Score': lineup['value_score'].mean(),
            'Players': ', '.join(lineup['name'].tolist())
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(OUTPUT_SUMMARY, index=False)
    logger.info(f"Summary saved: {OUTPUT_SUMMARY}")
    
    # Create and save FanDuel submission
    submission_df = create_fanduel_submission(lineups_df)
    submission_df.to_csv(OUTPUT_FANDUEL, index=False)
    logger.info(f"FanDuel submission saved: {OUTPUT_FANDUEL}")
    
    return summary_df

# =============================================================================
# MAIN EXECUTION
# =============================================================================
def main():
    """Main execution function"""
    logger.info("="*60)
    logger.info("UNIFIED DFS OPTIMIZATION SYSTEM - STARTING")
    logger.info("="*60)
    
    try:
        # Prepare data
        df = prepare_optimization_data()
        
        # Generate lineups
        lineups_df = generate_all_lineups(df)
        
        # Save outputs
        summary_df = save_outputs(lineups_df)
        
        # Print results summary
        print("\n" + "="*60)
        print("OPTIMIZATION COMPLETE - RESULTS SUMMARY")
        print("="*60)
        print(f"Total lineups generated: {len(summary_df)}")
        print(f"Average projected FPPG: {summary_df['Total_Enhanced_FPPG'].mean():.1f}")
        print(f"Salary range: ${summary_df['Total_Salary'].min():,} - ${summary_df['Total_Salary'].max():,}")
        print(f"Files created:")
        print(f"  DATA: Detailed lineups: {OUTPUT_LINEUPS.name}")
        print(f"  INFO: Summary: {OUTPUT_SUMMARY.name}")
        print(f"  TARGET: FanDuel submission: {OUTPUT_FANDUEL.name}")
        
        # Strategy breakdown
        print(f"\nStrategy breakdown:")
        for strategy in STRATEGIES.keys():
            strategy_lineups = summary_df[summary_df['Strategy'] == strategy]
            if len(strategy_lineups) > 0:
                avg_fppg = strategy_lineups['Total_Enhanced_FPPG'].mean()
                print(f"  {strategy.upper()}: {len(strategy_lineups)} lineups, avg {avg_fppg:.1f} FPPG")
        
        print("\nSTART: Ready for FanDuel submission!")
        print("="*60)
        
        logger.info("UNIFIED DFS OPTIMIZATION COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        logger.error(f"Optimization failed: {str(e)}")
        print(f"\nERROR: ERROR: {str(e)}")
        print("Check the log file for details.")
        raise

if __name__ == "__main__":
    main()
