#!/usr/bin/env python3
"""
DYNAMIC STACK SELECTOR
Systematically choose which teams to stack based on multiple factors
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_stack_opportunities(df):
    """Analyze all teams for stacking potential using multiple criteria"""
    
    print(" DYNAMIC STACK ANALYSIS")
    print("=" * 40)
    
    # Filter to hitters only
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    team_analysis = []
    
    for team in hitters['Team'].unique():
        team_players = hitters[hitters['Team'] == team].copy()
        
        if len(team_players) < 4:  # Need minimum 4 players for stack
            continue
            
        # Calculate team metrics
        metrics = calculate_team_metrics(team_players)
        metrics['Team'] = team
        team_analysis.append(metrics)
    
    df_teams = pd.DataFrame(team_analysis)
    
    # Score teams using multiple factors
    df_teams['stack_score'] = calculate_stack_scores(df_teams)
    df_teams = df_teams.sort_values('stack_score', ascending=False)
    
    print(f"\nDATA: STACK RANKINGS:")
    print(df_teams[['Team', 'stack_score', 'value_players', 'avg_projection', 'salary_efficiency', 'contrarian_score']].head(10).to_string(index=False))
    
    return df_teams

def calculate_team_metrics(team_players):
    """Calculate comprehensive metrics for a team's stacking potential"""
    
    # Value player count (under $3,500)
    value_players = len(team_players[team_players['Salary'] <= 3500])
    
    # Projection metrics
    avg_projection = team_players['aggressive_projection'].mean()
    total_projection = team_players['aggressive_projection'].sum()
    
    # Salary efficiency
    avg_salary = team_players['Salary'].mean()
    salary_efficiency = avg_projection / (avg_salary / 1000)  # Points per $1K
    
    # Nuclear potential (players with 25+ projected points)
    nuclear_count = len(team_players[team_players['aggressive_projection'] >= 25])
    
    # Contrarian score (based on simulated ownership)
    avg_ownership = team_players['simulated_ownership'].mean()
    contrarian_score = max(0, 15 - avg_ownership)  # Higher score for lower ownership
    
    # Batting order strength (lower is better)
    avg_batting_order = team_players['Batting Order'].mean()
    order_score = max(0, 9 - avg_batting_order)
    
    # Vegas metrics (if available)
    vegas_score = 0
    if 'Implied Total' in team_players.columns:
        avg_implied_total = team_players['Implied Total'].mean()
        vegas_score = avg_implied_total - 4.5  # Above league average
    
    return {
        'player_count': len(team_players),
        'value_players': value_players,
        'avg_projection': avg_projection,
        'total_projection': total_projection,
        'avg_salary': avg_salary,
        'salary_efficiency': salary_efficiency,
        'nuclear_count': nuclear_count,
        'contrarian_score': contrarian_score,
        'order_score': order_score,
        'vegas_score': vegas_score
    }

def calculate_stack_scores(df_teams):
    """Calculate composite stack scores using weighted factors"""
    
    scores = np.zeros(len(df_teams))
    
    # Normalize each metric to 0-10 scale
    for col in ['avg_projection', 'salary_efficiency', 'contrarian_score', 'nuclear_count', 'order_score', 'vegas_score']:
        if col in df_teams.columns and df_teams[col].max() > 0:
            normalized = (df_teams[col] - df_teams[col].min()) / (df_teams[col].max() - df_teams[col].min()) * 10
            
            # Apply weights based on tournament strategy
            if col == 'contrarian_score':
                weight = 0.25  # High weight for contrarian value
            elif col == 'salary_efficiency':
                weight = 0.20  # Salary efficiency important
            elif col == 'nuclear_count':
                weight = 0.20  # Nuclear players key for tournaments
            elif col == 'avg_projection':
                weight = 0.15  # Projections helpful but not everything
            elif col == 'order_score':
                weight = 0.10  # Batting order matters
            elif col == 'vegas_score':
                weight = 0.10  # Vegas info when available
            else:
                weight = 0.0
                
            scores += normalized * weight
    
    return scores

def select_top_stacks(df_teams, num_stacks=3):
    """Select top teams for stacking based on scores"""
    
    top_teams = df_teams.head(num_stacks)
    
    print(f"\nTARGET: TOP {num_stacks} STACK TARGETS:")
    print("=" * 30)
    
    stack_strategies = []
    
    for idx, team_info in top_teams.iterrows():
        team = team_info['Team']
        score = team_info['stack_score']
        
        print(f"\n{len(stack_strategies)+1}. {team} (Score: {score:.2f})")
        print(f"   MONEY: {team_info['value_players']} value players ($3,500)")
        print(f"   PROGRESS: {team_info['avg_projection']:.1f} avg projection")
        print(f"    {team_info['nuclear_count']} nuclear targets (25 pts)")
        print(f"    {team_info['contrarian_score']:.1f} contrarian score")
        print(f"    {team_info['salary_efficiency']:.2f} pts/$1K")
        
        # Determine stack strategy
        if team_info['nuclear_count'] >= 2:
            strategy = "Nuclear Stack"
        elif team_info['contrarian_score'] >= 8:
            strategy = "Contrarian Stack" 
        elif team_info['value_players'] >= 5:
            strategy = "Value Stack"
        else:
            strategy = "Balanced Stack"
            
        stack_strategies.append({
            'team': team,
            'strategy': strategy,
            'score': score,
            'metrics': team_info
        })
        
        print(f"   TARGET: Strategy: {strategy}")
    
    return stack_strategies

def generate_stack_lineups(df, stack_strategies):
    """Generate lineups for each selected stack strategy"""
    
    print(f"\n BUILDING STACK LINEUPS:")
    print("=" * 35)
    
    lineups = []
    
    for stack_info in stack_strategies:
        team = stack_info['team']
        strategy = stack_info['strategy']
        
        print(f"\n Building {team} {strategy}...")
        
        lineup = build_team_stack_lineup(df, team, strategy)
        if lineup:
            lineups.append({
                'name': f"{team} {strategy}",
                'lineup': lineup,
                'strategy': strategy,
                'team': team
            })
            print(f"SUCCESS: {team} {strategy} completed")
        else:
            print(f"ERROR: {team} {strategy} failed - insufficient players")
    
    return lineups

def build_team_stack_lineup(df, target_team, strategy):
    """Build lineup focusing on specific team stack"""
    
    pitchers = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')].copy()
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    # Get non-target team pitcher (avoid pitcher from same team)
    available_pitchers = pitchers[pitchers['Team'] != target_team]
    
    if strategy == "Nuclear Stack":
        # Use value pitcher, focus on nuclear hitters
        pitcher_pool = available_pitchers[
            (available_pitchers['Salary'] >= 6000) & 
            (available_pitchers['Salary'] <= 10000)
        ].sort_values('aggressive_projection', ascending=False)
    elif strategy == "Contrarian Stack":
        # Use low ownership pitcher
        pitcher_pool = available_pitchers.sort_values('simulated_ownership', ascending=True)
    else:
        # Use cheapest viable pitcher for max hitter salary
        pitcher_pool = available_pitchers.sort_values('Salary', ascending=True)
    
    if len(pitcher_pool) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Select pitcher
    pitcher = pitcher_pool.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Build stack with target team
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    target_players = hitters[hitters['Team'] == target_team].sort_values('aggressive_projection', ascending=False)
    
    stacked_count = 0
    
    for pos in positions:
        # Try target team first
        team_option = find_player_for_position(pos, target_players, remaining_salary, used_players)
        
        if team_option is not None and stacked_count < 5:  # Max 5 from same team
            best_player = team_option
            stacked_count += 1
        else:
            # Fill with best available from any team
            best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def find_player_for_position(position, players, max_salary, used_players):
    """Find best available player for position from specific team"""
    
    eligible = get_eligible_for_position(position, players)
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    return available.sort_values('aggressive_projection', ascending=False).iloc[0]

def find_best_player_for_position(position, players, max_salary, used_players):
    """Find best available player for position from any team"""
    
    eligible = get_eligible_for_position(position, players)
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    return available.sort_values('aggressive_projection', ascending=False).iloc[0]

def get_eligible_for_position(position, players):
    """Get players eligible for a position"""
    
    if position == 'OF':
        return players[players['Position'] == 'OF']
    else:
        # Handle multi-position eligibility
        return players[players['Position'].str.contains(position, na=False)]

def run_dynamic_stack_analysis():
    """Main function to run dynamic stack analysis"""
    
    print("START: DYNAMIC STACK SELECTOR")
    print("=" * 50)
    
    try:
        # Load today's data (replace with current date file)
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        print(f"SUCCESS: Loaded projections: {len(df)} players")
        
        # Apply aggressive system
        df = apply_aggressive_enhancements(df)
        
        # Analyze stack opportunities
        team_rankings = analyze_stack_opportunities(df)
        
        # Select top stacks
        stack_strategies = select_top_stacks(team_rankings, num_stacks=3)
        
        # Generate lineups
        lineups = generate_stack_lineups(df, stack_strategies)
        
        print(f"\nSUCCESS: Generated {len(lineups)} stack lineups")
        return lineups
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

def apply_aggressive_enhancements(df):
    """Apply our aggressive projection enhancements"""
    
    df_enhanced = df.copy()
    df_enhanced['aggressive_projection'] = df_enhanced['enhanced_fppg'].fillna(df_enhanced['FPPG'])
    df_enhanced['simulated_ownership'] = simulate_ownership(df_enhanced)
    
    # Apply multipliers for value players
    value_players = df_enhanced[
        (df_enhanced['Salary'] <= 3500) & 
        (df_enhanced['Position'] != 'P')
    ]
    
    for idx, player in value_players.iterrows():
        multiplier = 1.0
        
        if player['Salary'] <= 2500:
            multiplier += 0.6
        elif player['Salary'] <= 3000:
            multiplier += 0.4
        elif player['Salary'] <= 3500:
            multiplier += 0.2
            
        df_enhanced.at[idx, 'aggressive_projection'] *= multiplier
    
    return df_enhanced

def simulate_ownership(df):
    """Simulate ownership based on salary"""
    
    ownership = []
    for _, player in df.iterrows():
        salary = player['Salary']
        
        if salary <= 2500:
            own = np.random.uniform(1, 5)
        elif salary <= 3000:
            own = np.random.uniform(3, 8)
        elif salary <= 3500:
            own = np.random.uniform(5, 12)
        else:
            own = np.random.uniform(8, 25)
            
        ownership.append(own)
    
    return ownership

if __name__ == "__main__":
    run_dynamic_stack_analysis()
