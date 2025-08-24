#!/usr/bin/env python3
"""
Enhanced FanDuel Lineup Optimizer with Stacking
Adds team/game stacking strategies to the existing optimizer
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
from itertools import combinations

class StackingOptimizer:
    def __init__(self, players_df):
        self.players = players_df.copy()
        self.stacking_strategies = {
            'team_stack_4': {'min_players': 4, 'bonus': 1.15},  # 15% bonus for 4-player team stack
            'team_stack_3': {'min_players': 3, 'bonus': 1.10},  # 10% bonus for 3-player team stack
            'game_stack': {'min_players': 2, 'bonus': 1.08},    # 8% bonus for game stack (both teams)
            'pitcher_stack': {'min_players': 2, 'bonus': 1.05}  # 5% bonus for pitcher + offense stack
        }
    
    def identify_stack_opportunities(self):
        """Identify the best stacking opportunities"""
        
        print("\n🎯 ANALYZING STACKING OPPORTUNITIES")
        print("=" * 50)
        
        stack_opportunities = []
        
        # 1. Team Stacks
        team_stacks = self.analyze_team_stacks()
        stack_opportunities.extend(team_stacks)
        
        # 2. Game Stacks  
        game_stacks = self.analyze_game_stacks()
        stack_opportunities.extend(game_stacks)
        
        # 3. Pitcher Stacks
        pitcher_stacks = self.analyze_pitcher_stacks()
        stack_opportunities.extend(pitcher_stacks)
        
        return stack_opportunities
    
    def analyze_team_stacks(self):
        """Find best team stacking opportunities"""
        
        team_stacks = []
        
        # Group hitters by team
        hitters = self.players[self.players['Primary_Position'] != 'P']
        
        for team in hitters['Team'].unique():
            team_players = hitters[hitters['Team'] == team].copy()
            
            if len(team_players) >= 3:  # Need at least 3 for a stack
                # Calculate team metrics
                avg_projection = team_players['Projected_FPPG'].mean()
                total_salary = team_players['Salary'].sum()
                avg_value = (team_players['Projected_FPPG'] / team_players['Salary'] * 1000).mean()
                
                # Check for batting order correlation (if available)
                batting_order_bonus = 0
                if 'Batting Order' in team_players.columns:
                    has_top_order = any(team_players['Batting Order'].fillna(10) <= 3)
                    has_mid_order = any((team_players['Batting Order'].fillna(10) >= 4) & 
                                      (team_players['Batting Order'].fillna(10) <= 6))
                    if has_top_order and has_mid_order:
                        batting_order_bonus = 0.05  # 5% bonus for order diversity
                
                # Stack score calculation
                stack_score = avg_projection * (1 + batting_order_bonus)
                
                team_stacks.append({
                    'type': 'team_stack',
                    'team': team,
                    'players': team_players.index.tolist(),
                    'player_count': len(team_players),
                    'avg_projection': avg_projection,
                    'stack_score': stack_score,
                    'avg_value': avg_value,
                    'batting_order_bonus': batting_order_bonus
                })
        
        # Sort by stack score
        team_stacks = sorted(team_stacks, key=lambda x: x['stack_score'], reverse=True)
        
        print(f"📊 Top Team Stack Opportunities:")
        for i, stack in enumerate(team_stacks[:5], 1):
            print(f"  {i}. {stack['team']}: {stack['player_count']} players, "
                  f"{stack['avg_projection']:.1f} avg proj, "
                  f"{stack['avg_value']:.0f} avg value")
        
        return team_stacks
    
    def analyze_game_stacks(self):
        """Find best game stacking opportunities (high-scoring games)"""
        
        game_stacks = []
        
        for game in self.players['Game'].unique():
            game_players = self.players[self.players['Game'] == game]
            hitters = game_players[game_players['Primary_Position'] != 'P']
            
            if len(hitters) >= 4:  # Need multiple players from both teams
                # Calculate game metrics
                total_projection = hitters['Projected_FPPG'].sum()
                avg_projection = hitters['Projected_FPPG'].mean()
                
                # Check team distribution
                teams_in_game = hitters['Team'].nunique()
                
                if teams_in_game >= 2:  # Both teams represented
                    game_stacks.append({
                        'type': 'game_stack',
                        'game': game,
                        'players': hitters.index.tolist(),
                        'player_count': len(hitters),
                        'total_projection': total_projection,
                        'avg_projection': avg_projection,
                        'teams_count': teams_in_game
                    })
        
        game_stacks = sorted(game_stacks, key=lambda x: x['total_projection'], reverse=True)
        
        print(f"\n📊 Top Game Stack Opportunities:")
        for i, stack in enumerate(game_stacks[:3], 1):
            print(f"  {i}. {stack['game']}: {stack['player_count']} players, "
                  f"{stack['total_projection']:.1f} total proj")
        
        return game_stacks
    
    def analyze_pitcher_stacks(self):
        """Find pitcher + offense stacking opportunities"""
        
        pitcher_stacks = []
        
        pitchers = self.players[self.players['Primary_Position'] == 'P']
        
        for _, pitcher in pitchers.iterrows():
            pitcher_team = pitcher['Team']
            
            # Find offensive players from same team
            team_hitters = self.players[
                (self.players['Team'] == pitcher_team) & 
                (self.players['Primary_Position'] != 'P')
            ]
            
            if len(team_hitters) >= 2:  # Need at least 2 hitters to stack with pitcher
                combined_projection = pitcher['Projected_FPPG'] + team_hitters['Projected_FPPG'].sum()
                
                pitcher_stacks.append({
                    'type': 'pitcher_stack',
                    'pitcher': pitcher.name,
                    'pitcher_name': pitcher['Nickname'],
                    'team': pitcher_team,
                    'hitters': team_hitters.index.tolist(),
                    'combined_projection': combined_projection,
                    'pitcher_projection': pitcher['Projected_FPPG'],
                    'hitter_count': len(team_hitters)
                })
        
        pitcher_stacks = sorted(pitcher_stacks, key=lambda x: x['combined_projection'], reverse=True)
        
        print(f"\n📊 Top Pitcher Stack Opportunities:")
        for i, stack in enumerate(pitcher_stacks[:3], 1):
            print(f"  {i}. {stack['pitcher_name']} + {stack['hitter_count']} hitters: "
                  f"{stack['combined_projection']:.1f} combined proj")
        
        return pitcher_stacks
    
    def optimize_with_stacking(self, stack_strategy='team_stack_3'):
        """Optimize lineup with specific stacking strategy"""
        
        print(f"\n🎯 OPTIMIZING WITH {stack_strategy.upper()} STRATEGY")
        print("=" * 50)
        
        prob = LpProblem(f"FanDuel_Stack_{stack_strategy}", LpMaximize)
        
        # Decision variables
        player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in self.players.index}
        
        # Base objective: projected FPPG
        base_objective = lpSum(self.players.loc[i, 'Projected_FPPG'] * player_vars[i] for i in self.players.index)
        
        # Add stacking bonuses
        stacking_bonus = self.create_stacking_constraints(prob, player_vars, stack_strategy)
        
        # Combined objective
        prob += base_objective + stacking_bonus
        
        # Standard constraints
        prob += lpSum(player_vars[i] for i in self.players.index) == 9  # 9 players
        prob += lpSum(self.players.loc[i, 'Salary'] * player_vars[i] for i in self.players.index) <= 35000  # Salary cap
        
        # Position constraints
        position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        
        for pos, required in position_requirements.items():
            pos_players = self.players[self.players['Primary_Position'] == pos].index
            if len(pos_players) >= required:
                prob += lpSum(player_vars[i] for i in pos_players) == required
        
        # Solve
        solver = PULP_CBC_CMD(msg=False)
        status = prob.solve(solver)
        
        if status == 1:
            selected_indices = [i for i in self.players.index if player_vars[i].value() == 1]
            lineup = self.players.loc[selected_indices].copy()
            
            # Analyze the stack
            stack_analysis = self.analyze_lineup_stacks(lineup)
            
            return lineup, stack_analysis
        else:
            return None, None
    
    def create_stacking_constraints(self, prob, player_vars, strategy):
        """Create stacking bonus constraints"""
        
        stacking_bonus = 0
        
        if strategy == 'team_stack_3':
            # Bonus for having 3+ players from same team
            for team in self.players['Team'].unique():
                team_hitters = self.players[
                    (self.players['Team'] == team) & 
                    (self.players['Primary_Position'] != 'P')
                ].index
                
                if len(team_hitters) >= 3:
                    # Create binary variable for this team stack
                    stack_var = LpVariable(f"team_stack_{team}", cat='Binary')
                    
                    # If stack_var = 1, then we have 3+ players from this team
                    prob += lpSum(player_vars[i] for i in team_hitters) >= 3 * stack_var
                    prob += lpSum(player_vars[i] for i in team_hitters) <= 8 * stack_var + 2  # Upper bound
                    
                    # Add bonus to objective
                    stack_bonus += stack_var * 5  # 5 point bonus for team stack
        
        elif strategy == 'game_stack':
            # Bonus for having players from high-scoring games
            for game in self.players['Game'].unique():
                game_hitters = self.players[
                    (self.players['Game'] == game) & 
                    (self.players['Primary_Position'] != 'P')
                ].index
                
                if len(game_hitters) >= 4:
                    game_stack_var = LpVariable(f"game_stack_{game.replace('@', '_')}", cat='Binary')
                    
                    prob += lpSum(player_vars[i] for i in game_hitters) >= 4 * game_stack_var
                    prob += lpSum(player_vars[i] for i in game_hitters) <= 8 * game_stack_var + 3
                    
                    stacking_bonus += game_stack_var * 3  # 3 point bonus for game stack
        
        return stacking_bonus
    
    def analyze_lineup_stacks(self, lineup):
        """Analyze what stacks are present in the final lineup"""
        
        analysis = {
            'team_stacks': {},
            'game_stacks': {},
            'correlations': []
        }
        
        # Check team stacks
        hitters = lineup[lineup['Primary_Position'] != 'P']
        for team in hitters['Team'].unique():
            team_count = len(hitters[hitters['Team'] == team])
            if team_count >= 2:
                analysis['team_stacks'][team] = team_count
        
        # Check game representation
        for game in lineup['Game'].unique():
            game_count = len(lineup[lineup['Game'] == game])
            if game_count >= 2:
                analysis['game_stacks'][game] = game_count
        
        return analysis

def main():
    """Demo the stacking optimizer"""
    
    # Load data (same as existing optimizer)
    todays_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # Simplified data prep (you'd use your existing logic)
    players = todays_slate.copy()
    players['Primary_Position'] = players['Position']  # Simplified
    players['Projected_FPPG'] = players.get('FPPG', players['Salary'] / 300)
    
    # Initialize stacking optimizer
    stack_optimizer = StackingOptimizer(players)
    
    # Analyze opportunities
    opportunities = stack_optimizer.identify_stack_opportunities()
    
    # Optimize with different strategies
    strategies = ['team_stack_3', 'game_stack']
    
    for strategy in strategies:
        lineup, analysis = stack_optimizer.optimize_with_stacking(strategy)
        
        if lineup is not None:
            print(f"\n🏆 {strategy.upper()} LINEUP:")
            print(f"Total Salary: ${lineup['Salary'].sum():,}")
            print(f"Total Projection: {lineup['Projected_FPPG'].sum():.1f}")
            print(f"Stacks: {analysis}")

if __name__ == "__main__":
    main()
