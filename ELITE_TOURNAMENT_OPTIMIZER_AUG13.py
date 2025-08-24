#!/usr/bin/env python3
"""
ELITE TOURNAMENT OPTIMIZER FOR AUGUST 13TH
Build proper elite lineups using August 13th projections with ownership modeling
"""

import pandas as pd
import numpy as np
import logging
from itertools import combinations
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_ownership_from_salary(salary, position):
    """Simulate ownership based on salary and position"""
    # Higher salaries generally have higher ownership
    base_ownership = min(30, (salary / 300))  # Cap at 30%
    
    # Position adjustments (pitchers tend to have more concentrated ownership)
    if position == 'P':
        base_ownership *= 1.5  # Pitchers have higher ownership variance
    elif position in ['SS', '2B', '3B']:
        base_ownership *= 0.8  # Middle infield slightly lower ownership
    
    # Add some randomness to simulate variance
    variance = random.uniform(0.7, 1.3)
    simulated_ownership = max(0.5, min(40, base_ownership * variance))
    
    return round(simulated_ownership, 1)

def calculate_player_correlation(player1_row, player2_row):
    """Calculate correlation between two players"""
    correlation = 0.0
    
    # Same team correlation
    if player1_row['Team'] == player2_row['Team']:
        # Batting order correlation (closer in order = higher correlation)
        if pd.notna(player1_row['Batting Order']) and pd.notna(player2_row['Batting Order']):
            order_diff = abs(player1_row['Batting Order'] - player2_row['Batting Order'])
            if order_diff <= 1:
                correlation += 0.25
            elif order_diff <= 2:
                correlation += 0.15
            else:
                correlation += 0.05
        else:
            correlation += 0.1  # Base same-team correlation
    
    # Same position correlation (slightly negative due to substitution)
    if player1_row['Position'] == player2_row['Position'] and player1_row['Position'] != 'P':
        correlation -= 0.05
    
    return correlation

def generate_ceiling_projection(base_projection, variance_factor=1.8):
    """Generate ceiling projection based on base projection"""
    # Higher projections have higher ceilings
    ceiling_multiplier = variance_factor + (base_projection / 50) * 0.3
    return base_projection * ceiling_multiplier

def build_elite_lineups_aug13():
    """Build elite tournament lineups for August 13th"""
    
    logger.info("START: BUILDING ELITE TOURNAMENT LINEUPS FOR AUGUST 13TH")
    logger.info("=" * 60)
    
    # Load August 13th projections
    projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
    logger.info(f"SUCCESS: Loaded {len(projections)} player projections")
    
    # Create full player names
    projections['Player'] = projections['First Name'] + ' ' + projections['Last Name']
    
    # Filter out injured players and low-projection players
    active_players = projections[
        (projections['Injury Indicator'].isna() | (projections['Injury Indicator'] == '')) &
        (projections['enhanced_fppg'] >= 5.0)  # Minimum projection threshold
    ].copy()
    
    logger.info(f"SUCCESS: {len(active_players)} active players after filters")
    
    # Simulate ownership for each player
    active_players['Simulated_Ownership'] = active_players.apply(
        lambda row: simulate_ownership_from_salary(row['Salary'], row['Position']), axis=1
    )
    
    # Generate ceiling projections
    active_players['Ceiling_Projection'] = active_players['enhanced_fppg'].apply(
        lambda x: generate_ceiling_projection(x)
    )
    
    # Calculate value metrics
    active_players['Value_Score'] = active_players['enhanced_fppg'] / (active_players['Salary'] / 1000)
    active_players['Ownership_Value'] = active_players['enhanced_fppg'] / (active_players['Simulated_Ownership'] + 1)
    
    # Identify top teams for stacking
    team_scores = active_players.groupby('Team').agg({
        'enhanced_fppg': 'sum',
        'Simulated_Ownership': 'mean',
        'Value_Score': 'mean'
    }).reset_index()
    
    team_scores['Stack_Score'] = (
        team_scores['enhanced_fppg'] * 0.4 +
        (100 - team_scores['Simulated_Ownership']) * 0.3 +  # Lower ownership is better
        team_scores['Value_Score'] * 0.3
    )
    
    top_teams = team_scores.nlargest(8, 'Stack_Score')['Team'].tolist()
    logger.info(f"TARGET: Top stacking teams: {top_teams}")
    
    # Check if Miami is in top teams
    if 'MIA' in top_teams:
        miami_rank = top_teams.index('MIA') + 1
        logger.info(f"LINEUP: MIAMI ranked #{miami_rank} for stacking!")
    else:
        logger.info("WARNING: Miami not in top 8 stacking teams")
        # Let's see Miami's ranking
        miami_score = team_scores[team_scores['Team'] == 'MIA']['Stack_Score'].iloc[0] if len(team_scores[team_scores['Team'] == 'MIA']) > 0 else 0
        miami_rank = (team_scores['Stack_Score'] > miami_score).sum() + 1
        logger.info(f"DATA: Miami ranks #{miami_rank} overall with score {miami_score:.2f}")
    
    elite_lineups = []
    
    # Build lineups for each top team
    for team in top_teams[:6]:  # Focus on top 6 teams
        team_players = active_players[active_players['Team'] == team]
        other_players = active_players[active_players['Team'] != team]
        
        if len(team_players) < 3:  # Need at least 3 for a stack
            continue
            
        # Select 4-player stack from team
        hitters = team_players[team_players['Position'] != 'P'].nlargest(6, 'Ownership_Value')
        stack_combos = list(combinations(hitters.index, 4))
        
        for combo in stack_combos[:2]:  # Top 2 combinations per team
            lineup_players = []
            used_salary = 0
            used_positions = set()
            
            # Add stack players
            for idx in combo:
                player = active_players.loc[idx]
                lineup_players.append(player)
                used_salary += player['Salary']
                used_positions.add(player['Position'])
            
            # Fill remaining positions
            remaining_salary = 35000 - used_salary
            needed_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            
            # Remove positions we already have
            for pos in used_positions:
                if pos in needed_positions:
                    needed_positions.remove(pos)
            
            # Fill remaining positions with best available players
            for pos in needed_positions:
                if pos == 'OF':
                    available = other_players[
                        (other_players['Position'] == 'OF') &
                        (other_players['Salary'] <= remaining_salary * 0.8)
                    ]
                else:
                    available = other_players[
                        (other_players['Position'] == pos) &
                        (other_players['Salary'] <= remaining_salary * 0.8)
                    ]
                
                if len(available) > 0:
                    best_player = available.nlargest(1, 'Ownership_Value').iloc[0]
                    lineup_players.append(best_player)
                    used_salary += best_player['Salary']
                    remaining_salary = 35000 - used_salary
                    
                    # Remove this player from other_players
                    other_players = other_players[other_players.index != best_player.name]
            
            # Only add complete lineups (9 players)
            if len(lineup_players) == 9 and used_salary <= 35000:
                lineup_dict = {
                    'players': lineup_players,
                    'total_salary': used_salary,
                    'total_projection': sum(p['enhanced_fppg'] for p in lineup_players),
                    'total_ceiling': sum(p['Ceiling_Projection'] for p in lineup_players),
                    'avg_ownership': np.mean([p['Simulated_Ownership'] for p in lineup_players]),
                    'stack_team': team,
                    'stack_count': 4
                }
                elite_lineups.append(lineup_dict)
    
    # Sort by tournament score (projection / ownership)
    for lineup in elite_lineups:
        lineup['tournament_score'] = lineup['total_projection'] / (lineup['avg_ownership'] + 1)
    
    elite_lineups.sort(key=lambda x: x['tournament_score'], reverse=True)
    
    # Take top 15 unique lineups
    elite_lineups = elite_lineups[:15]
    
    logger.info(f"LINEUP: Generated {len(elite_lineups)} elite lineups")
    
    # Create output DataFrame
    output_data = []
    for i, lineup in enumerate(elite_lineups, 1):
        players_str = ' | '.join([f"{p['Player']} ({p['Team']}) ${p['Salary']}" for p in lineup['players']])
        
        output_data.append({
            'Lineup': i,
            'Total_Salary': lineup['total_salary'],
            'Projected_Points': round(lineup['total_projection'], 1),
            'Ceiling_Projection': round(lineup['total_ceiling'], 1),
            'Avg_Ownership': round(lineup['avg_ownership'], 1),
            'Tournament_Score': round(lineup['tournament_score'], 1),
            'Players': players_str,
            'P1': lineup['players'][0]['Player'],
            'P2': lineup['players'][1]['Player'] if len(lineup['players']) > 1 else '',
            'Stack_Team': f"{lineup['stack_team']} ({lineup['stack_count']})"
        })
    
    output_df = pd.DataFrame(output_data)
    
    # Save elite lineups
    timestamp = "20250814_140000"
    output_file = f"../fd_current_slate/ELITE_AUG13_LINEUPS_{timestamp}.csv"
    output_df.to_csv(output_file, index=False)
    
    logger.info(f" Saved elite lineups to: {output_file}")
    
    # Show summary
    logger.info("\nTARGET: ELITE LINEUP SUMMARY:")
    logger.info("=" * 40)
    
    stack_teams = output_df['Stack_Team'].str.extract(r'(\w+)')[0].value_counts()
    for team, count in stack_teams.items():
        logger.info(f"    {team}: {count} lineups")
    
    if 'MIA' in stack_teams.index:
        logger.info(f"LINEUP: MIAMI INCLUDED: {stack_teams['MIA']} lineups!")
    else:
        logger.info("WARNING: Miami not selected in elite lineups")
    
    logger.info(f"\nDATA: Projection range: {output_df['Projected_Points'].min():.1f} - {output_df['Projected_Points'].max():.1f}")
    logger.info(f"DATA: Ownership range: {output_df['Avg_Ownership'].min():.1f}% - {output_df['Avg_Ownership'].max():.1f}%")
    
    return output_file

if __name__ == "__main__":
    build_elite_lineups_aug13()
