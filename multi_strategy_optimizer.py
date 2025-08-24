#!/usr/bin/env python3
"""
Fixed FanDuel Optimizer with OPTIONAL Stacking
Creates multiple lineup options: pure value, team stack, and game stack
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

def create_multiple_lineups():
    """Create multiple optimal lineups with different strategies"""
    
    print("START: FanDuel Multi-Strategy Lineup Optimizer")
    print("=" * 60)
    
    # Load data (using your existing logic)
    todays_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # CRITICAL: Filter out injured players and non-starters
    print(" FILTERING OUT INJURED PLAYERS AND NON-STARTERS...")
    
    # Remove players on IL or with injuries
    healthy_players = todays_slate[
        (todays_slate['Injury Indicator'].isna() | (todays_slate['Injury Indicator'] == '')) &
        (todays_slate['Injury Details'].isna() | (todays_slate['Injury Details'] == ''))
    ].copy()
    
    print(f"DATA: Injury Filter: {len(todays_slate)}  {len(healthy_players)} players (removed {len(todays_slate) - len(healthy_players)} injured)")
    
    # Additional starter verification for hitters (for pitchers, keep all healthy ones)
    if 'Batting Order' in healthy_players.columns:
        # Separate pitchers and hitters
        pitchers = healthy_players[healthy_players['Position'] == 'P'].copy()
        hitters = healthy_players[healthy_players['Position'] != 'P'].copy()
        
        # For hitters, prioritize those with confirmed batting orders
        confirmed_hitters = hitters[
            hitters['Batting Order'].notna() & (hitters['Batting Order'] > 0)
        ].copy()
        
        if len(confirmed_hitters) >= 25:  # If we have enough confirmed starters
            healthy_players = pd.concat([pitchers, confirmed_hitters], ignore_index=True)
            print(f"DATA: Starter Filter: Using {len(pitchers)} pitchers + {len(confirmed_hitters)} confirmed hitters")
    
    # Quick data prep with quality filters
    starters = healthy_players[
        (healthy_players['Salary'] >= 2000) & 
        (healthy_players['FPPG'].notna()) &
        (healthy_players['FPPG'] > 0)
    ].copy()
    
    # Smart position assignment based on scarcity
    def assign_positions_smartly(df):
        """Assign players to positions based on scarcity and eligibility"""
        df_copy = df.copy()
        
        # Get all possible positions for each player
        def get_eligible_positions(roster_pos):
            if pd.isna(roster_pos):
                return ['OF']  # Default unknown to OF
            
            pos_str = str(roster_pos).upper()
            positions = []
            
            # CRITICAL: Pitchers can ONLY play pitcher
            if pos_str == 'P' or 'P' in pos_str:
                return ['P']  # Pitchers cannot play other positions
            
            # Handle position players
            if 'C' in pos_str:
                positions.append('C')
            if '1B' in pos_str:
                positions.append('1B')
            if '2B' in pos_str:
                positions.append('2B')
            if '3B' in pos_str:
                positions.append('3B')
            if 'SS' in pos_str:
                positions.append('SS')
            if 'OF' in pos_str or not positions:  # Default to OF if no specific positions
                positions.append('OF')
                
            return positions
        
        df_copy['Eligible_Positions'] = df_copy['Roster Position'].apply(get_eligible_positions)
        
        # Count how many players are eligible for each position
        position_counts = {}
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
            count = sum(1 for positions in df_copy['Eligible_Positions'] if pos in positions)
            position_counts[pos] = count
        
        print(f"DATA: Position eligibility counts: {position_counts}")
        
        # Assign primary positions with better distribution
        position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        assigned_positions = {}
        
        # Handle special case: C/1B players
        # Split C/1B eligible players between C and 1B positions
        c1b_eligible = df_copy[df_copy['Eligible_Positions'].apply(lambda x: 'C' in x and '1B' in x)]
        if len(c1b_eligible) > 0:
            # Sort by FPPG and assign best ones to each position
            c1b_sorted = c1b_eligible.sort_values('FPPG', ascending=False)
            
            # Assign top half to 1B (rarer position), bottom half to C
            num_1b = min(10, len(c1b_sorted) // 2 + 1)  # At least 1 for 1B
            num_c = min(10, len(c1b_sorted) - num_1b)
            
            for i, (idx, player) in enumerate(c1b_sorted.iterrows()):
                if i < num_1b:
                    assigned_positions[idx] = '1B'
                elif i < num_1b + num_c:
                    assigned_positions[idx] = 'C'
        
        # Handle pitchers FIRST (they can only play P)
        pitchers = df_copy[df_copy['Eligible_Positions'].apply(lambda x: x == ['P'])]
        for idx in pitchers.index:
            assigned_positions[idx] = 'P'
        
        # Sort positions by scarcity (excluding P, OF, and already handled C/1B)
        remaining_positions = [pos for pos in position_counts.keys() if pos not in ['P', 'OF', 'C', '1B']]
        scarcity_order = sorted(remaining_positions, key=lambda x: position_counts[x])
        
        # Assign remaining positions
        for pos in scarcity_order + ['OF']:
            if pos in ['C', '1B', 'P']:
                continue  # Already handled above
                
            eligible_players = df_copy[df_copy['Eligible_Positions'].apply(lambda x: pos in x)].index
            # Exclude players already assigned
            eligible_players = [idx for idx in eligible_players if idx not in assigned_positions]
            
            if pos == 'OF':
                # For OF, assign many more players since we need 3
                pos_players = df_copy.loc[eligible_players].nlargest(min(50, len(eligible_players)), 'FPPG')
            else:
                # For other positions, assign top players for flexibility
                pos_players = df_copy.loc[eligible_players].nlargest(min(10, len(eligible_players)), 'FPPG')
            
            # Assign these players to this position
            for idx, player in pos_players.iterrows():
                if idx not in assigned_positions:
                    assigned_positions[idx] = pos
        
        # Assign remaining players to OF
        for idx in df_copy.index:
            if idx not in assigned_positions:
                assigned_positions[idx] = 'OF'
        
        df_copy['Primary_Position'] = df_copy.index.map(assigned_positions)
        return df_copy
    
    # Apply smart position assignment AFTER injury filtering
    starters = assign_positions_smartly(starters)
    
    # Show which injured players we filtered out
    injured_players = todays_slate[
        (~todays_slate['Injury Indicator'].isna() & (todays_slate['Injury Indicator'] != '')) |
        (~todays_slate['Injury Details'].isna() & (todays_slate['Injury Details'] != ''))
    ]
    
    if len(injured_players) > 0:
        print(f"\n FILTERED OUT {len(injured_players)} INJURED PLAYERS:")
        for _, player in injured_players.head(10).iterrows():
            injury_info = f"{player.get('Injury Indicator', 'N/A')} - {player.get('Injury Details', 'N/A')}"
            print(f"  ERROR: {player['Nickname']} ({player['Position']}): {injury_info}")
        if len(injured_players) > 10:
            print(f"  ... and {len(injured_players) - 10} more")
    starters['Projected_FPPG'] = starters['FPPG']
    
    # Ensure position balance
    pos_counts = starters['Primary_Position'].value_counts()
    print(f"DATA: Position availability:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        count = pos_counts.get(pos, 0)
        print(f"  {pos}: {count} players")
        if count == 0:
            print(f"  WARNING: No {pos} players - need to fix data")
    
    strategies = {
        'value': 'Pure Value (No Stacking)',
        'team_stack': 'Team Stack Preferred', 
        'game_stack': 'Game Stack Preferred'
    }
    
    results = {}
    
    for strategy_name, description in strategies.items():
        print(f"\nTARGET: OPTIMIZING: {description}")
        print("-" * 40)
        
        lineup = optimize_single_strategy(starters, strategy_name)
        
        if lineup is not None:
            results[strategy_name] = lineup
            analyze_lineup(lineup, strategy_name)
        else:
            print(f"ERROR: Failed to create {strategy_name} lineup")
    
    # Compare strategies
    if results:
        compare_strategies(results)
        
        # Save all lineups
        for strategy, lineup in results.items():
            filename = f"../data/lineup_{strategy}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
            lineup.to_csv(filename, index=False)
            print(f" Saved {strategy} lineup to {filename}")

def optimize_single_strategy(players_df, strategy):
    """Optimize lineup for a single strategy"""
    
    prob = LpProblem(f"FanDuel_{strategy}", LpMaximize)
    
    # Filter to ensure we have all positions
    position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    
    lineup_pool = players_df.copy()
    for pos, required in position_requirements.items():
        available = len(lineup_pool[lineup_pool['Primary_Position'] == pos])
        if available < required:
            print(f"WARNING: Only {available} {pos} players available, need {required}")
            # Try to reassign multi-position players
            if pos == 'C' and available == 0:
                # Look for C/1B players
                multi_pos = lineup_pool[lineup_pool['Roster Position'].str.contains('C', na=False)]
                if len(multi_pos) > 0:
                    lineup_pool.loc[multi_pos.index[0], 'Primary_Position'] = 'C'
                    print(f"SUCCESS: Reassigned {multi_pos.iloc[0]['Nickname']} to C")
    
    # Decision variables
    player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in lineup_pool.index}
    
    # Base objective
    base_objective = lpSum(lineup_pool.loc[i, 'Projected_FPPG'] * player_vars[i] for i in lineup_pool.index)
    
    # Strategy-specific bonuses
    bonus_objective = 0
    
    if strategy == 'team_stack':
        # Small bonus for team correlation (soft constraint)
        for team in lineup_pool['Team'].unique():
            team_hitters = lineup_pool[
                (lineup_pool['Team'] == team) & 
                (lineup_pool['Primary_Position'] != 'P')
            ].index
            
            if len(team_hitters) >= 3:
                # Bonus increases with more players from same team
                team_sum = lpSum(player_vars[i] for i in team_hitters)
                bonus_objective += team_sum * 0.5  # Small bonus per team player
    
    elif strategy == 'game_stack':
        # Bonus for game correlation
        for game in lineup_pool['Game'].unique():
            game_players = lineup_pool[
                (lineup_pool['Game'] == game) & 
                (lineup_pool['Primary_Position'] != 'P')
            ].index
            
            if len(game_players) >= 4:
                game_sum = lpSum(player_vars[i] for i in game_players)
                bonus_objective += game_sum * 0.3  # Bonus for game exposure
    
    # Combined objective
    prob += base_objective + bonus_objective
    
    # Constraints
    prob += lpSum(player_vars[i] for i in lineup_pool.index) == 9
    prob += lpSum(lineup_pool.loc[i, 'Salary'] * player_vars[i] for i in lineup_pool.index) <= 35000
    
    # Position constraints
    for pos, required in position_requirements.items():
        pos_players = lineup_pool[lineup_pool['Primary_Position'] == pos].index
        if len(pos_players) >= required:
            prob += lpSum(player_vars[i] for i in pos_players) == required
        else:
            print(f"ERROR: Cannot satisfy {pos} requirement: {len(pos_players)} < {required}")
            return None
    
    # Solve
    solver = PULP_CBC_CMD(msg=False)
    status = prob.solve(solver)
    
    if status == 1:
        selected_indices = [i for i in lineup_pool.index if player_vars[i].value() == 1]
        lineup = lineup_pool.loc[selected_indices].copy()
        return lineup
    else:
        return None

def analyze_lineup(lineup, strategy):
    """Analyze stacking in a lineup"""
    
    print(f"MONEY: Salary: ${lineup['Salary'].sum():,}")
    print(f"TARGET: Projection: {lineup['Projected_FPPG'].sum():.1f}")
    
    # Team analysis
    hitters = lineup[lineup['Primary_Position'] != 'P']
    team_counts = hitters['Team'].value_counts()
    
    print(f"DATA: Team Distribution:")
    for team, count in team_counts.items():
        if count >= 2:
            print(f"   {team}: {count} players (STACK)")
        else:
            print(f"  DATA: {team}: {count} player")
    
    # Game analysis
    game_counts = lineup['Game'].value_counts()
    game_stacks = game_counts[game_counts >= 2]
    
    if len(game_stacks) > 0:
        print(f" Game Stacks:")
        for game, count in game_stacks.items():
            print(f"   {game}: {count} players")

def compare_strategies(results):
    """Compare different lineup strategies"""
    
    print(f"\nLINEUP: STRATEGY COMPARISON")
    print("=" * 50)
    
    comparison_data = []
    
    for strategy, lineup in results.items():
        hitters = lineup[lineup['Primary_Position'] != 'P']
        team_stacks = (hitters['Team'].value_counts() >= 2).sum()
        max_team_stack = hitters['Team'].value_counts().max()
        
        comparison_data.append({
            'Strategy': strategy.replace('_', ' ').title(),
            'Projection': lineup['Projected_FPPG'].sum(),
            'Salary': lineup['Salary'].sum(),
            'Value': (lineup['Projected_FPPG'].sum() / lineup['Salary'].sum() * 1000),
            'Team Stacks': team_stacks,
            'Max Stack Size': max_team_stack
        })
    
    comp_df = pd.DataFrame(comparison_data)
    print(comp_df.to_string(index=False))
    
    # Recommend best strategy
    best_projection = comp_df.loc[comp_df['Projection'].idxmax()]
    best_value = comp_df.loc[comp_df['Value'].idxmax()]
    most_stacked = comp_df.loc[comp_df['Team Stacks'].idxmax()]
    
    print(f"\nPROGRESS: Recommendations:")
    print(f"  TARGET: Highest Projection: {best_projection['Strategy']} ({best_projection['Projection']:.1f})")
    print(f"  MONEY: Best Value: {best_value['Strategy']} ({best_value['Value']:.1f})")
    print(f"   Most Stacked: {most_stacked['Strategy']} ({most_stacked['Team Stacks']} stacks)")

if __name__ == "__main__":
    create_multiple_lineups()
