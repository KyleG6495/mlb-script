#!/usr/bin/env python3
"""
Dynamic Stacking Engine for MLB DFS

Advanced stacking strategies:
1. Correlation-based team stacking
2. Game environment stacking (weather, park factors)
3. Batting order correlation modeling
4. Pitcher vulnerability targeting
5. Leverage situation awareness
6. Anti-correlation for GPP differentiation
"""

import pandas as pd
import numpy as np
from scipy.stats import pearsonr
import networkx as nx
from sklearn.cluster import KMeans
from pulp import LpVariable, lpSum

class DynamicStackingEngine:
    def __init__(self):
        self.correlation_matrix = None
        self.stack_recommendations = {}
        self.anti_stack_targets = {}
        
    def calculate_correlation_matrix(self, historical_data):
        """Calculate player correlation matrix from historical data"""
        print("📊 Building correlation matrix...")
        
        # Pivot data to get player x game matrix
        player_game_matrix = historical_data.pivot_table(
            index='date', 
            columns='player_name', 
            values='fantasy_points'
        ).fillna(0)
        
        # Calculate correlations
        self.correlation_matrix = player_game_matrix.corr()
        
        return self.correlation_matrix
    
    def identify_optimal_stacks(self, player_pool, weather_data, vegas_totals):
        """Identify optimal stacking opportunities"""
        print("🔥 Identifying optimal stack combinations...")
        
        stacks = {}
        
        # 1. HIGH-TOTAL GAME STACKS
        high_total_games = vegas_totals[vegas_totals['total'] >= 9.0]
        for _, game in high_total_games.iterrows():
            teams = [game['home_team'], game['away_team']]
            stacks[f"high_total_{game['game_id']}"] = {
                'teams': teams,
                'reason': f"High total: {game['total']}",
                'weight': game['total'] / 12.0,  # Normalize
                'type': 'game_stack'
            }
        
        # 2. WEATHER-DRIVEN STACKS
        for _, weather in weather_data.iterrows():
            wind_factor = self.calculate_wind_factor(weather)
            temp_factor = self.calculate_temperature_factor(weather)
            
            if wind_factor > 1.1 or temp_factor > 1.1:  # Favorable conditions
                game_teams = self.get_teams_for_game(weather['game_id'], player_pool)
                stacks[f"weather_{weather['game_id']}"] = {
                    'teams': game_teams,
                    'reason': f"Favorable weather (Wind: {wind_factor:.2f}, Temp: {temp_factor:.2f})",
                    'weight': wind_factor * temp_factor,
                    'type': 'weather_stack'
                }
        
        # 3. PITCHER VULNERABILITY STACKS
        vulnerable_pitchers = self.identify_vulnerable_pitchers(player_pool)
        for pitcher_info in vulnerable_pitchers:
            opposing_team = pitcher_info['opposing_team']
            stacks[f"anti_pitcher_{pitcher_info['name']}"] = {
                'teams': [opposing_team],
                'reason': f"vs Vulnerable pitcher {pitcher_info['name']} (ERA: {pitcher_info['era']:.2f})",
                'weight': pitcher_info['vulnerability_score'],
                'type': 'anti_pitcher_stack'
            }
        
        # 4. BATTING ORDER CORRELATION STACKS
        order_stacks = self.identify_batting_order_stacks(player_pool)
        stacks.update(order_stacks)
        
        # 5. CONTRARIAN STACKS (for GPP)
        contrarian_stacks = self.identify_contrarian_stacks(player_pool, stacks)
        stacks.update(contrarian_stacks)
        
        self.stack_recommendations = stacks
        return stacks
    
    def calculate_wind_factor(self, weather):
        """Calculate wind impact on scoring"""
        wind_speed = weather.get('wind_speed', 0)
        wind_direction = weather.get('wind_direction', 0)
        
        # Outgoing wind boosts offense
        if 90 <= wind_direction <= 270:  # Roughly outgoing
            return 1.0 + (wind_speed / 100)  # Each mph = 1% boost
        else:  # Incoming wind
            return 1.0 - (wind_speed / 200)  # Each mph = 0.5% penalty
    
    def calculate_temperature_factor(self, weather):
        """Calculate temperature impact on offense"""
        temp = weather.get('temperature', 70)
        
        # Optimal temperature around 75-80°F
        if 75 <= temp <= 80:
            return 1.1  # 10% boost
        elif temp >= 85:
            return 1.05  # Hot weather helps
        elif temp <= 50:
            return 0.9   # Cold weather hurts
        else:
            return 1.0   # Neutral
    
    def identify_vulnerable_pitchers(self, player_pool):
        """Find pitchers to target"""
        pitchers = player_pool[player_pool['Position'] == 'P']
        vulnerable = []
        
        for _, pitcher in pitchers.iterrows():
            vulnerability_score = 0
            
            # High ERA
            era = pitcher.get('ERA', 4.50)
            if era >= 5.0:
                vulnerability_score += 0.3
            elif era >= 4.5:
                vulnerability_score += 0.2
            
            # High WHIP
            whip = pitcher.get('WHIP', 1.30)
            if whip >= 1.40:
                vulnerability_score += 0.2
            
            # Recent struggles
            recent_era = pitcher.get('recent_era', era)
            if recent_era > era * 1.2:
                vulnerability_score += 0.2
            
            # Platoon splits
            vs_handedness = pitcher.get('vs_opposite_hand_ops', 0.750)
            if vs_handedness >= 0.800:
                vulnerability_score += 0.15
            
            if vulnerability_score >= 0.3:  # Threshold for targeting
                vulnerable.append({
                    'name': pitcher['Nickname'],
                    'era': era,
                    'whip': whip,
                    'vulnerability_score': vulnerability_score,
                    'opposing_team': self.get_opposing_team(pitcher)
                })
        
        return vulnerable
    
    def identify_batting_order_stacks(self, player_pool):
        """Find optimal batting order combinations"""
        stacks = {}
        
        # Group by team and batting order
        hitters = player_pool[player_pool['Position'] != 'P']
        
        for team in hitters['Team'].unique():
            team_hitters = hitters[hitters['Team'] == team]
            
            if 'Batting Order' in team_hitters.columns:
                team_hitters = team_hitters.dropna(subset=['Batting Order'])
                
                # Top of order stack (1-4)
                top_order = team_hitters[team_hitters['Batting Order'].isin([1, 2, 3, 4])]
                if len(top_order) >= 3:
                    stacks[f"top_order_{team}"] = {
                        'players': top_order.index.tolist(),
                        'reason': f"Top of order correlation ({team})",
                        'weight': 1.2,
                        'type': 'batting_order_stack'
                    }
                
                # Power stack (3-6)
                power_order = team_hitters[team_hitters['Batting Order'].isin([3, 4, 5, 6])]
                if len(power_order) >= 3:
                    stacks[f"power_order_{team}"] = {
                        'players': power_order.index.tolist(),
                        'reason': f"Power portion of order ({team})",
                        'weight': 1.15,
                        'type': 'batting_order_stack'
                    }
        
        return stacks
    
    def identify_contrarian_stacks(self, player_pool, existing_stacks):
        """Find contrarian stacking opportunities"""
        contrarian = {}
        
        # Find teams NOT in popular stacks
        popular_teams = set()
        for stack_info in existing_stacks.values():
            if 'teams' in stack_info:
                popular_teams.update(stack_info['teams'])
        
        all_teams = set(player_pool['Team'].unique())
        contrarian_teams = all_teams - popular_teams
        
        for team in contrarian_teams:
            team_players = player_pool[
                (player_pool['Team'] == team) & 
                (player_pool['Position'] != 'P')
            ]
            
            if len(team_players) >= 3:
                # Calculate contrarian value
                avg_ownership = team_players.get('projected_ownership', pd.Series([0.1] * len(team_players))).mean()
                
                if avg_ownership < 0.15:  # Low owned team
                    contrarian[f"contrarian_{team}"] = {
                        'teams': [team],
                        'reason': f"Contrarian team stack (Avg own: {avg_ownership:.1%})",
                        'weight': 1.0 - avg_ownership,  # Higher weight for lower ownership
                        'type': 'contrarian_stack'
                    }
        
        return contrarian
    
    def create_stack_constraints(self, prob, player_vars, player_pool, stack_type='balanced'):
        """Create optimization constraints for stacking"""
        stack_constraints = []
        
        if stack_type == 'aggressive':
            # Force at least one 4+ team stack
            for team in player_pool['Team'].unique():
                team_hitters = player_pool[
                    (player_pool['Team'] == team) & 
                    (player_pool['Position'] != 'P')
                ].index
                
                if len(team_hitters) >= 4:
                    # Create binary variable for this stack
                    team_stack_var = LpVariable(f"team_stack_{team}", cat='Binary')
                    
                    # If stack activated, take at least 4 players
                    stack_constraints.append(
                        lpSum(player_vars[i] for i in team_hitters) >= 4 * team_stack_var
                    )
        
        elif stack_type == 'game_stack':
            # Force game stacking
            for game in player_pool['Game'].unique():
                game_players = player_pool[
                    (player_pool['Game'] == game) & 
                    (player_pool['Position'] != 'P')
                ].index
                
                if len(game_players) >= 5:
                    # Require at least 5 players from this game
                    stack_constraints.append(
                        lpSum(player_vars[i] for i in game_players) >= 5
                    )
        
        elif stack_type == 'mini_stack':
            # Force multiple mini-stacks
            mini_stacks = 0
            for team in player_pool['Team'].unique():
                team_hitters = player_pool[
                    (player_pool['Team'] == team) & 
                    (player_pool['Position'] != 'P')
                ].index
                
                if len(team_hitters) >= 2:
                    team_stack_var = LpVariable(f"mini_stack_{team}", cat='Binary')
                    
                    # At least 2 players to activate mini stack
                    stack_constraints.append(
                        lpSum(player_vars[i] for i in team_hitters) >= 2 * team_stack_var
                    )
                    
                    mini_stacks += team_stack_var
            
            # Require at least 2 mini stacks
            if mini_stacks > 0:
                stack_constraints.append(mini_stacks >= 2)
        
        return stack_constraints
    
    def calculate_stack_bonus(self, lineup_df):
        """Calculate bonus points for successful stacks"""
        bonus = 0
        
        # Team stack bonuses
        team_counts = lineup_df[lineup_df['Position'] != 'P']['Team'].value_counts()
        for team, count in team_counts.items():
            if count >= 4:
                bonus += count * 2  # 2 points per player in 4+ stack
            elif count >= 3:
                bonus += count * 1  # 1 point per player in 3-stack
        
        # Game stack bonuses
        game_counts = lineup_df['Game'].value_counts()
        for game, count in game_counts.items():
            if count >= 6:
                bonus += count * 1.5  # Game stack bonus
            elif count >= 5:
                bonus += count * 1
        
        # Batting order correlation bonus
        for team in lineup_df['Team'].unique():
            team_players = lineup_df[lineup_df['Team'] == team]
            if 'Batting Order' in team_players.columns and len(team_players) >= 3:
                orders = team_players['Batting Order'].dropna().sort_values()
                if len(orders) >= 3:
                    # Consecutive batting order bonus
                    for i in range(len(orders) - 2):
                        if orders.iloc[i+2] - orders.iloc[i] <= 3:  # 3 consecutive spots
                            bonus += 3
        
        return bonus
    
    def get_teams_for_game(self, game_id, player_pool):
        """Get teams playing in a specific game"""
        game_players = player_pool[player_pool['Game'].str.contains(str(game_id), na=False)]
        return game_players['Team'].unique().tolist()
    
    def get_opposing_team(self, pitcher):
        """Get the team opposing this pitcher"""
        return pitcher.get('Opponent', 'UNK')

if __name__ == "__main__":
    # Example usage
    engine = DynamicStackingEngine()
    
    # Would load real data in practice
    player_pool = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    weather_data = pd.read_csv("../data/weather_today.csv")
    
    # Mock vegas totals
    vegas_totals = pd.DataFrame({
        'game_id': ['Game1', 'Game2'], 
        'total': [9.5, 8.5],
        'home_team': ['LAD', 'NYY'],
        'away_team': ['SF', 'BOS']
    })
    
    stacks = engine.identify_optimal_stacks(player_pool, weather_data, vegas_totals)
    print("📊 Stack recommendations:", stacks)
