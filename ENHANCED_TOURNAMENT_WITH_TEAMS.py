#!/usr/bin/env python3
"""
ENHANCED TOURNAMENT OPTIMIZER WITH DYNAMIC TEAM SELECTION
Combines your existing game stacking with systematic team ranking
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

# We'll implement our own versions of the functions instead of importing
# from ELITE_TOURNAMENT_OPTIMIZER import identify_game_stacks, add_contrarian_weights

def identify_game_stacks(df):
    """Identify high-scoring games for stacking based on projections"""
    
    # Get unique games
    games = df['Game'].unique()
    game_info = []
    
    for game in games:
        if pd.isna(game):
            continue
            
        game_players = df[df['Game'] == game]
        
        # Calculate average projections for game
        avg_projection = game_players['FPPG'].mean()
        total_players = len(game_players)
        
        # Identify teams in game
        teams = game_players['Team'].unique()
        
        game_info.append({
            'game': game,
            'avg_projection': avg_projection,
            'total_players': total_players,
            'teams': teams
        })
    
    # Sort by average projection (proxy for high-scoring games)
    game_info.sort(key=lambda x: x['avg_projection'], reverse=True)
    
    print(" TOP GAME STACKING TARGETS:")
    for i, game in enumerate(game_info[:3]):
        print(f"  {i+1}. {game['game']} - Avg: {game['avg_projection']:.1f} FPPG ({game['total_players']} players)")
    
    return game_info

def build_game_stack_lineup(df, game_info):
    """Build lineup focusing on players from high-scoring game"""
    
    target_game = game_info['game']
    
    pitchers = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')].copy()
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    # Get players from target game
    game_players = df[df['Game'] == target_game]
    game_pitchers = game_players[game_players['Position'] == 'P']
    game_hitters = game_players[game_players['Position'] != 'P']
    
    if len(game_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Select pitcher from game
    pitcher = game_pitchers.sort_values('aggressive_projection', ascending=False).iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Fill positions prioritizing game players
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    game_count = 0
    
    for pos in positions:
        # Try game players first (up to 6 total from game including pitcher)
        if game_count < 5:
            game_option = find_player_for_position(pos, game_hitters, remaining_salary, used_players)
            if game_option is not None:
                best_player = game_option
                game_count += 1
            else:
                best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        else:
            best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def run_enhanced_tournament_system():
    """Enhanced system combining game stacks + dynamic team selection"""
    
    print("START: ENHANCED TOURNAMENT SYSTEM")
    print("=" * 50)
    print("Combining game stacking + dynamic team ranking")
    
    try:
        # Load August 13th data for testing
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        print(f"SUCCESS: Loaded August 13th projections: {len(df)} players")
        
        # Apply aggressive enhancements
        df = apply_aggressive_system(df)
        
        # 1. Your existing game stack analysis
        print(f"\nTARGET: GAME STACKING ANALYSIS:")
        game_stacks = identify_game_stacks(df)
        
        # 2. NEW: Dynamic team ranking
        print(f"\nLINEUP: DYNAMIC TEAM RANKING:")
        team_rankings = analyze_team_stacking_opportunities(df)
        
        # 3. Generate combined strategies
        strategies = [
            # Your existing strategies
            ("Top Game Stack", lambda: build_game_stack_lineup(df, game_stacks[0])),
            ("Second Game Stack", lambda: build_game_stack_lineup(df, game_stacks[1])),
            
            # NEW: Top team stacks
            ("Top Team Stack", lambda: build_team_stack_lineup(df, team_rankings.iloc[0])),
            ("Contrarian Team Stack", lambda: build_contrarian_team_lineup(df, team_rankings)),
            ("Value Team Stack", lambda: build_value_team_lineup(df, team_rankings)),
            
            # Combined approaches
            ("Hybrid Stack", lambda: build_hybrid_lineup(df, game_stacks[0], team_rankings.iloc[0]))
        ]
        
        # Build all lineups
        lineups = []
        for strategy_name, build_func in strategies:
            print(f"\n Building: {strategy_name}")
            try:
                lineup = build_func()
                if lineup:
                    lineups.append((strategy_name, lineup))
                    print(f"SUCCESS: {strategy_name} completed")
                else:
                    print(f"ERROR: {strategy_name} failed")
            except Exception as e:
                print(f"ERROR: {strategy_name} error: {e}")
        
        # Display results
        print(f"\nLINEUP: GENERATED {len(lineups)} TOURNAMENT LINEUPS")
        for strategy, lineup in lineups:
            display_lineup_summary(strategy, lineup)
            
        return lineups
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

def analyze_team_stacking_opportunities(df):
    """Systematic team analysis for stacking (from DYNAMIC_STACK_SELECTOR)"""
    
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    team_analysis = []
    
    for team in hitters['Team'].unique():
        team_players = hitters[hitters['Team'] == team].copy()
        
        if len(team_players) < 4:  # Need minimum 4 players
            continue
            
        # Calculate comprehensive metrics
        metrics = {
            'Team': team,
            'player_count': len(team_players),
            'value_players': len(team_players[team_players['Salary'] <= 3500]),
            'avg_projection': team_players['aggressive_projection'].mean(),
            'total_projection': team_players['aggressive_projection'].sum(),
            'avg_salary': team_players['Salary'].mean(),
            'salary_efficiency': team_players['aggressive_projection'].mean() / (team_players['Salary'].mean() / 1000),
            'nuclear_count': len(team_players[team_players['aggressive_projection'] >= 25]),
            'contrarian_score': max(0, 15 - team_players['simulated_ownership'].mean())
        }
        
        team_analysis.append(metrics)
    
    df_teams = pd.DataFrame(team_analysis)
    
    # Calculate composite scores
    scores = np.zeros(len(df_teams))
    
    weights = {
        'contrarian_score': 0.25,
        'salary_efficiency': 0.20,
        'nuclear_count': 0.20,
        'avg_projection': 0.15,
        'value_players': 0.20
    }
    
    for col, weight in weights.items():
        if col in df_teams.columns and df_teams[col].max() > 0:
            normalized = (df_teams[col] - df_teams[col].min()) / (df_teams[col].max() - df_teams[col].min()) * 10
            scores += normalized * weight
    
    df_teams['stack_score'] = scores
    df_teams = df_teams.sort_values('stack_score', ascending=False)
    
    print(f"TOP 5 TEAM STACK TARGETS:")
    for idx, team_info in df_teams.head(5).iterrows():
        print(f"  {team_info['Team']} (Score: {team_info['stack_score']:.2f})")
        print(f"    MONEY: {team_info['value_players']} value players")
        print(f"    PROGRESS: {team_info['avg_projection']:.1f} avg projection")
        print(f"     {team_info['nuclear_count']} nuclear targets")
    
    return df_teams

def build_team_stack_lineup(df, team_info):
    """Build lineup focusing on top-ranked team"""
    
    target_team = team_info['Team']
    
    pitchers = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')].copy()
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    # Use non-target team pitcher
    available_pitchers = pitchers[pitchers['Team'] != target_team]
    value_pitchers = available_pitchers[
        (available_pitchers['Salary'] >= 6000) & 
        (available_pitchers['Salary'] <= 10000)
    ].sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Select pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Build stack with target team
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    target_players = hitters[hitters['Team'] == target_team].sort_values('aggressive_projection', ascending=False)
    
    stacked_count = 0
    
    for pos in positions:
        if stacked_count < 5:  # Try to get 5 from target team
            team_option = find_player_for_position(pos, target_players, remaining_salary, used_players)
            if team_option is not None:
                best_player = team_option
                stacked_count += 1
            else:
                best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        else:
            best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def build_contrarian_team_lineup(df, team_rankings):
    """Build lineup using team with highest contrarian score"""
    
    # Find team with highest contrarian score
    contrarian_team = team_rankings.sort_values('contrarian_score', ascending=False).iloc[0]
    return build_team_stack_lineup(df, contrarian_team)

def build_value_team_lineup(df, team_rankings):
    """Build lineup using team with most value players"""
    
    # Find team with most value players
    value_team = team_rankings.sort_values('value_players', ascending=False).iloc[0]
    return build_team_stack_lineup(df, value_team)

def build_hybrid_lineup(df, top_game, top_team):
    """Combine game stacking concept with specific team focus"""
    
    target_team = top_team['Team']
    
    pitchers = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')].copy()
    hitters = df[(df['Position'] != 'P') & (df['Batting Order'] > 0)].copy()
    
    # Use pitcher from top game if not from target team
    game_pitchers = pitchers[pitchers['Game'] == top_game['game']]
    non_target_pitchers = game_pitchers[game_pitchers['Team'] != target_team]
    
    if len(non_target_pitchers) > 0:
        pitcher = non_target_pitchers.sort_values('aggressive_projection', ascending=False).iloc[0]
    else:
        # Fall back to value pitcher
        value_pitchers = pitchers[
            (pitchers['Salary'] >= 6000) & 
            (pitchers['Salary'] <= 10000) &
            (pitchers['Team'] != target_team)
        ].sort_values('aggressive_projection', ascending=False)
        pitcher = value_pitchers.iloc[0] if len(value_pitchers) > 0 else None
    
    if pitcher is None:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Mix target team players with game players
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    target_players = hitters[hitters['Team'] == target_team]
    game_players = hitters[hitters['Game'] == top_game['game']]
    
    target_count = 0
    game_count = 0
    
    for pos in positions:
        best_player = None
        
        # Prioritize target team up to 4 players
        if target_count < 4:
            team_option = find_player_for_position(pos, target_players, remaining_salary, used_players)
            if team_option is not None:
                best_player = team_option
                target_count += 1
        
        # Then try game players
        if best_player is None and game_count < 3:
            game_option = find_player_for_position(pos, game_players, remaining_salary, used_players)
            if game_option is not None:
                best_player = game_option
                game_count += 1
        
        # Fall back to best available
        if best_player is None:
            best_player = find_best_player_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def apply_aggressive_system(df):
    """Apply aggressive projection enhancements"""
    
    df_enhanced = df.copy()
    df_enhanced['aggressive_projection'] = df_enhanced.get('enhanced_fppg', df_enhanced['FPPG'])
    df_enhanced['simulated_ownership'] = simulate_ownership(df_enhanced)
    
    # Apply value multipliers
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

# Helper functions
def find_player_for_position(position, players, max_salary, used_players):
    """Find best available player for position from specific player pool"""
    
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
        return players[players['Position'].str.contains(position, na=False)]

def display_lineup_summary(strategy, lineup):
    """Display lineup summary"""
    
    total_salary = sum(player[1]['Salary'] for player in lineup)
    total_projection = sum(player[1]['aggressive_projection'] for player in lineup)
    
    print(f"\n{strategy}:")
    print(f"  MONEY: ${total_salary:,} salary")
    print(f"  PROGRESS: {total_projection:.1f} projected points")
    
    teams = {}
    for pos, player in lineup:
        team = player['Team']
        teams[team] = teams.get(team, 0) + 1
    
    stacks = [f"{team}({count})" for team, count in teams.items() if count >= 2]
    if stacks:
        print(f"   Stacks: {', '.join(stacks)}")

if __name__ == "__main__":
    run_enhanced_tournament_system()
