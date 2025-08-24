#!/usr/bin/env python3
"""
AGGRESSIVE UPSIDE PROJECTION ENHANCER
Learns from August 13th winning patterns to create more aggressive projections
Focus: Tournament upside over conservative projections
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def enhance_projections_with_upside():
    """Enhance existing projections with aggressive upside scenarios"""
    
    logger.info("START: AGGRESSIVE UPSIDE PROJECTION ENHANCER")
    logger.info("=" * 60)
    logger.info("Learning from August 13th winning patterns...")
    
    try:
        # Load today's enhanced projections
        projection_files = [
            "../data/enhanced_projections_20250813_175916.csv",
            "../data/enhanced_projections_20250813_135026.csv",
            "../data/enhanced_projections_latest.csv"
        ]
        
        df_projections = None
        for file in projection_files:
            try:
                df_projections = pd.read_csv(file)
                logger.info(f"SUCCESS: Loaded projections: {file}")
                break
            except FileNotFoundError:
                continue
        
        if df_projections is None:
            logger.error("ERROR: No projection files found")
            return None
        
        # Load today's slate for context
        df_slate = pd.read_csv("../data/fd_slate_today.csv")
        logger.info(f"SUCCESS: Loaded slate: {len(df_slate)} players")
        
        # Merge projections with slate data
        df_merged = df_slate.merge(df_projections[['Id', 'enhanced_fppg']], on='Id', how='left')
        # Fill missing enhanced projections with base FPPG
        df_merged['enhanced_projection'] = df_merged['enhanced_fppg'].fillna(df_merged['FPPG'])
        logger.info(f"SUCCESS: Merged data: {len(df_merged)} players")
        
        # Apply aggressive upside adjustments
        df_enhanced = apply_upside_adjustments(df_merged)
        
        # Save enhanced projections
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/aggressive_upside_projections_{timestamp}.csv"
        df_enhanced.to_csv(output_file, index=False)
        
        logger.info(f" Saved aggressive projections: {output_file}")
        return df_enhanced
        
    except Exception as e:
        logger.error(f"Error enhancing projections: {e}")
        return None

def apply_upside_adjustments(df):
    """Apply aggressive upside adjustments based on August 13th learnings"""
    
    df_enhanced = df.copy()
    
    logger.info("TARGET: Applying upside adjustments...")
    
    # 1. VALUE PLAYER UPSIDE BOOST
    # Target: Players under $3,500 with 25+ upside potential
    value_players = df_enhanced[
        (df_enhanced['Salary'] <= 3500) & 
        (df_enhanced['Position'] != 'P')
    ].copy()
    
    logger.info(f" Found {len(value_players)} value players (<= $3,500)")
    
    # Boost projections for value players in good spots
    for idx, player in value_players.iterrows():
        original_proj = player.get('enhanced_projection', player.get('Projected_FPPG', 10))
        
        # Apply upside multipliers based on game environment
        upside_multiplier = calculate_upside_multiplier(player)
        enhanced_proj = original_proj * upside_multiplier
        
        df_enhanced.at[idx, 'aggressive_projection'] = enhanced_proj
        df_enhanced.at[idx, 'upside_boost'] = enhanced_proj - original_proj
        
        if enhanced_proj > 25:  # Potential tournament winner
            logger.info(f" HIGH UPSIDE: {player['Nickname']} {player['Last Name']} "
                       f"(${player['Salary']}) - {original_proj:.1f}  {enhanced_proj:.1f} pts")
    
    # 2. GAME STACK CORRELATION BOOST
    df_enhanced = apply_game_stack_boost(df_enhanced)
    
    # 3. PITCHER VALUE TARGETING
    df_enhanced = apply_pitcher_value_strategy(df_enhanced)
    
    # 4. CONTRARIAN OWNERSHIP BOOST
    df_enhanced = apply_contrarian_boost(df_enhanced)
    
    return df_enhanced

def calculate_upside_multiplier(player):
    """Calculate upside multiplier based on game environment factors"""
    
    base_multiplier = 1.0
    
    # Salary-based upside (cheaper = more upside potential)
    if player['Salary'] <= 2500:
        base_multiplier += 0.6  # 60% boost for min salary players
    elif player['Salary'] <= 3000:
        base_multiplier += 0.4  # 40% boost
    elif player['Salary'] <= 3500:
        base_multiplier += 0.2  # 20% boost
    
    # Position-based adjustments
    if player['Position'] in ['OF', 'SS', '2B']:  # Positions with SB upside
        base_multiplier += 0.1
    
    # Batting order boost (if available)
    batting_order = player.get('Batting Order', 5)
    if batting_order <= 3:  # Top of order
        base_multiplier += 0.15
    elif batting_order <= 5:  # Heart of order
        base_multiplier += 0.1
    
    # Cap maximum multiplier
    return min(base_multiplier, 2.0)  # Max 100% boost

def apply_game_stack_boost(df):
    """Apply correlation boost for players from same teams/games"""
    
    logger.info(" Applying game stack correlation boosts...")
    
    # Group by team to identify stacking opportunities
    team_groups = df.groupby('Team')
    
    for team, team_players in team_groups:
        if len(team_players) >= 3:  # Stackable team
            # Boost all players from teams with 4+ available players
            team_avg_proj = team_players.get('aggressive_projection', 
                                           team_players.get('enhanced_projection', 10)).mean()
            
            if team_avg_proj > 15:  # Good offensive environment
                stack_boost = 1.1  # 10% correlation boost
                
                for idx in team_players.index:
                    current_proj = df.at[idx, 'aggressive_projection']
                    if pd.notna(current_proj):
                        df.at[idx, 'aggressive_projection'] = current_proj * stack_boost
                        df.at[idx, 'stack_boost'] = current_proj * (stack_boost - 1)
                
                logger.info(f" Stack boost applied to {team} ({len(team_players)} players)")
    
    return df

def apply_pitcher_value_strategy(df):
    """Adjust pitcher projections to emphasize value over expensive aces"""
    
    logger.info("BASEBALL: Applying pitcher value strategy...")
    
    pitchers = df[df['Position'] == 'P'].copy()
    
    for idx, pitcher in pitchers.iterrows():
        salary = pitcher['Salary']
        original_proj = pitcher.get('aggressive_projection', 
                                  pitcher.get('enhanced_projection', 20))
        
        # Value pitcher boost (August 13th winners used $6K-$10K pitchers)
        if 6000 <= salary <= 10000:
            value_boost = 1.15  # 15% boost for value pitchers
            df.at[idx, 'aggressive_projection'] = original_proj * value_boost
            df.at[idx, 'pitcher_value_boost'] = original_proj * (value_boost - 1)
            
            logger.info(f" Pitcher value boost: {pitcher['Nickname']} {pitcher['Last Name']} "
                       f"(${salary}) - {original_proj:.1f}  {original_proj * value_boost:.1f} pts")
        
        # Expensive pitcher penalty (encourage salary savings)
        elif salary >= 11000:
            expensive_penalty = 0.95  # 5% penalty for expensive aces
            df.at[idx, 'aggressive_projection'] = original_proj * expensive_penalty
    
    return df

def apply_contrarian_boost(df):
    """Boost projections for likely low-owned players"""
    
    logger.info(" Applying contrarian ownership boosts...")
    
    # Simulate ownership based on salary and name recognition
    df['simulated_ownership'] = simulate_ownership(df)
    
    # Boost low-owned players with upside
    low_owned = df[df['simulated_ownership'] < 5.0].copy()  # <5% projected ownership
    
    for idx, player in low_owned.iterrows():
        current_proj = player.get('aggressive_projection', 
                                player.get('enhanced_projection', 10))
        
        if current_proj > 15:  # Has upside potential
            contrarian_boost = 1.2  # 20% boost for contrarian plays
            df.at[idx, 'aggressive_projection'] = current_proj * contrarian_boost
            df.at[idx, 'contrarian_boost'] = current_proj * (contrarian_boost - 1)
            
            if current_proj * contrarian_boost > 25:
                logger.info(f" Contrarian gem: {player['Nickname']} {player['Last Name']} "
                           f"(${player['Salary']}, ~{player['simulated_ownership']:.1f}% owned) "
                           f"- {current_proj:.1f}  {current_proj * contrarian_boost:.1f} pts")
    
    return df

def simulate_ownership(df):
    """Simulate likely ownership percentages"""
    
    # Simple ownership simulation based on salary and position
    ownership = []
    
    for _, player in df.iterrows():
        salary = player['Salary']
        position = player['Position']
        
        # Base ownership by salary tier
        if salary >= 4500:
            base_own = 15 + (salary - 4500) / 100  # High salary = high ownership
        elif salary >= 3500:
            base_own = 8 + (salary - 3500) / 200
        elif salary >= 2500:
            base_own = 3 + (salary - 2500) / 300
        else:
            base_own = 1 + salary / 1000  # Min salary = very low ownership
        
        # Position adjustments
        if position == 'P':
            base_own *= 0.8  # Pitchers generally lower owned
        elif position in ['SS', 'OF']:
            base_own *= 1.1  # Premium positions higher owned
        
        # Add randomness
        final_own = max(0.1, base_own + np.random.uniform(-2, 2))
        ownership.append(min(final_own, 50))  # Cap at 50%
    
    return ownership

def create_tournament_lineups():
    """Create tournament lineups using aggressive projections"""
    
    df_enhanced = enhance_projections_with_upside()
    if df_enhanced is None:
        return
    
    logger.info("\nLINEUP: CREATING AGGRESSIVE TOURNAMENT LINEUPS")
    logger.info("=" * 50)
    
    # Filter to playable players (healthy, starting, probable)
    df_playable = filter_playable_players(df_enhanced)
    
    # Create multiple tournament strategies
    strategies = [
        ('Nuclear Value Hunt', create_nuclear_value_lineup),
        ('Game Stack Attack', create_game_stack_lineup),
        ('Contrarian Crusher', create_contrarian_lineup),
        ('Value Pitcher Special', create_value_pitcher_lineup)
    ]
    
    lineups = []
    for strategy_name, strategy_func in strategies:
        lineup = strategy_func(df_playable)
        if lineup:
            lineups.append((strategy_name, lineup))
    
    # Display results
    for strategy, lineup in lineups:
        display_lineup(strategy, lineup)
    
    # Save lineups
    save_aggressive_lineups(lineups)

def filter_playable_players(df):
    """Filter to only playable players"""
    
    # Remove injured players
    injury_indicators = ['IL', 'DTD', 'O']
    df_healthy = df[~df['Injury Indicator'].isin(injury_indicators)].copy()
    
    # Probable pitchers only
    df_probable_pitchers = df_healthy[
        (df_healthy['Position'] == 'P') & 
        (df_healthy['Probable Pitcher'] == 'Yes')
    ]
    
    # Starting hitters only
    df_starting_hitters = df_healthy[
        (df_healthy['Position'] != 'P') & 
        (df_healthy['Batting Order'] > 0)
    ]
    
    return pd.concat([df_probable_pitchers, df_starting_hitters], ignore_index=True)

def create_nuclear_value_lineup(df):
    """Create lineup targeting nuclear value plays"""
    
    # Target high upside/salary ratio
    df['value_ratio'] = df['aggressive_projection'] / (df['Salary'] / 1000)
    value_targets = df.nlargest(20, 'value_ratio')
    
    return build_optimal_lineup(value_targets, 'Nuclear Value')

def create_game_stack_lineup(df):
    """Create lineup with heavy team stacking"""
    
    # Find best stacking opportunities
    team_stacks = df.groupby('Team')['aggressive_projection'].sum().nlargest(5)
    best_team = team_stacks.index[0]
    
    team_players = df[df['Team'] == best_team].nlargest(10, 'aggressive_projection')
    other_players = df[df['Team'] != best_team].nlargest(10, 'aggressive_projection')
    
    combined = pd.concat([team_players, other_players])
    return build_optimal_lineup(combined, 'Game Stack')

def create_contrarian_lineup(df):
    """Create lineup with contrarian plays"""
    
    contrarian = df[df['simulated_ownership'] < 10].nlargest(15, 'aggressive_projection')
    return build_optimal_lineup(contrarian, 'Contrarian')

def create_value_pitcher_lineup(df):
    """Create lineup with value pitcher strategy"""
    
    # Start with value pitcher
    value_pitchers = df[
        (df['Position'] == 'P') & 
        (df['Salary'] <= 9000)
    ].nlargest(3, 'aggressive_projection')
    
    if len(value_pitchers) > 0:
        pitcher = value_pitchers.iloc[0]
        remaining_salary = 35000 - pitcher['Salary']
        
        # Get best hitters within remaining salary
        hitters = df[df['Position'] != 'P'].copy()
        affordable_hitters = hitters[hitters['Salary'] <= remaining_salary // 8]
        
        lineup_players = affordable_hitters.nlargest(15, 'aggressive_projection')
        combined = pd.concat([pd.DataFrame([pitcher]), lineup_players])
        
        return build_optimal_lineup(combined, 'Value Pitcher')
    
    return None

def build_optimal_lineup(df_pool, strategy_name):
    """Build optimal 9-player lineup from player pool"""
    
    # Simple greedy optimization (can be improved with proper optimization)
    lineup = []
    remaining_salary = 35000
    positions_needed = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Sort by projection descending
    df_sorted = df_pool.sort_values('aggressive_projection', ascending=False)
    
    for pos in positions_needed:
        if pos == 'C':
            pos_players = df_sorted[df_sorted['Position'].str.contains('C')]
        elif pos == '1B':
            pos_players = df_sorted[df_sorted['Position'].str.contains('1B')]
        elif pos in ['2B', '3B', 'SS']:
            pos_players = df_sorted[df_sorted['Position'].str.contains(pos)]
        elif pos == 'OF':
            pos_players = df_sorted[df_sorted['Position'].str.contains('OF')]
        else:  # P
            pos_players = df_sorted[df_sorted['Position'] == 'P']
        
        # Find affordable player
        for _, player in pos_players.iterrows():
            if (player['Salary'] <= remaining_salary and 
                player['Id'] not in [p['Id'] for p in lineup]):
                lineup.append(player.to_dict())
                remaining_salary -= player['Salary']
                break
    
    return lineup if len(lineup) == 9 else None

def display_lineup(strategy, lineup):
    """Display lineup details"""
    
    if not lineup:
        logger.info(f"ERROR: {strategy}: Could not create valid lineup")
        return
    
    total_salary = sum(p['Salary'] for p in lineup)
    total_projection = sum(p['aggressive_projection'] for p in lineup)
    
    logger.info(f"\nSTART: {strategy.upper()}")
    logger.info(f"Total Projection: {total_projection:.1f} points")
    logger.info(f"Total Salary: ${total_salary:,}")
    logger.info(f"Remaining: ${35000 - total_salary:,}")
    
    positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
    for i, player in enumerate(lineup):
        pos = positions[i] if i < len(positions) else 'UTIL'
        logger.info(f"  {pos}: {player['Nickname']} {player['Last Name']} "
                   f"(${player['Salary']}) - {player['aggressive_projection']:.1f} pts")

def save_aggressive_lineups(lineups):
    """Save aggressive lineups to file"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/aggressive_tournament_lineups_{timestamp}.csv"
    
    all_lineups = []
    for strategy, lineup in lineups:
        if lineup:
            for i, player in enumerate(lineup):
                all_lineups.append({
                    'Strategy': strategy,
                    'Position': ['P', 'C/1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'UTIL'][i],
                    'Player_Id': player['Id'],
                    'Name': f"{player['Nickname']} {player['Last Name']}",
                    'Salary': player['Salary'],
                    'Projection': player['aggressive_projection']
                })
    
    if all_lineups:
        df_output = pd.DataFrame(all_lineups)
        df_output.to_csv(output_file, index=False)
        logger.info(f" Saved aggressive lineups: {output_file}")

if __name__ == "__main__":
    create_tournament_lineups()
