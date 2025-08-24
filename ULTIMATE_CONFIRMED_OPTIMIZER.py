#!/usr/bin/env python3
"""
ULTIMATE CONFIRMED STARTERS OPTIMIZER
Complete optimization pipeline before lineup generation
Uses simulations, ownership, correlations, weather - EVERYTHING!
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import random
from itertools import combinations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConfirmedStartersOptimizer:
    def __init__(self):
        self.confirmed_players = None
        self.weather_data = None
        self.park_factors = None
        self.ownership_projections = None
        self.simulation_results = None
        self.correlations = None
        
    def load_all_data(self):
        """Load all confirmed starters data and enhancements"""
        logger.info(" LOADING ALL CONFIRMED STARTERS DATA")
        logger.info("=" * 60)
        
        # Load confirmed starters
        try:
            self.confirmed_players = pd.read_csv('../fd_current_slate/fd_slate_confirmed_starters_only.csv')
            logger.info(f"SUCCESS: Loaded {len(self.confirmed_players)} confirmed starters")
        except:
            logger.error("ERROR: Could not load confirmed starters!")
            return False
            
        # Load weather data
        try:
            self.weather_data = pd.read_csv('data/weather_today.csv')
            logger.info(f" Loaded weather data for {len(self.weather_data)} games")
        except:
            logger.warning("WARNING: No weather data - will use defaults")
            
        # Load park factors
        try:
            park_data = pd.read_csv('../../data/park_factors.csv')
            logger.info(f" Loaded park factors for {len(park_data)} teams")
        except:
            logger.warning("WARNING: No park factors - will use defaults")
            
        return True
    
    def run_game_simulations(self, num_simulations=2000):
        """Run Monte Carlo simulations for all confirmed players"""
        logger.info(f" RUNNING {num_simulations} GAME SIMULATIONS")
        logger.info("=" * 60)
        
        simulation_results = []
        
        for _, player in self.confirmed_players.iterrows():
            player_sims = self._simulate_player_performance(player, num_simulations)
            simulation_results.append({
                'player_name': player['Nickname'],
                'position': player['Position'],
                'team': player['Team'],
                'salary': player['Salary'],
                'base_projection': player['Salary'] / 300,  # Base estimate
                'sim_mean': np.mean(player_sims),
                'sim_median': np.median(player_sims),
                'sim_std': np.std(player_sims),
                'sim_ceiling': np.percentile(player_sims, 90),
                'sim_floor': np.percentile(player_sims, 10),
                'sim_upside': np.percentile(player_sims, 90) - np.median(player_sims),
                'consistency': 1 / (1 + np.std(player_sims))  # Higher = more consistent
            })
            
        self.simulation_results = pd.DataFrame(simulation_results)
        logger.info(f"SUCCESS: Simulated {len(self.simulation_results)} confirmed players")
        logger.info(f"DATA: Projection range: {self.simulation_results['sim_mean'].min():.1f} - {self.simulation_results['sim_mean'].max():.1f} FPPG")
        
        return self.simulation_results
    
    def _simulate_player_performance(self, player, num_sims):
        """Simulate individual player performance with realistic variance"""
        
        # Base projection from salary
        base_proj = player['Salary'] / 300
        
        # Position-specific adjustments
        if player['Position'] == 'P':
            # Pitchers: higher base, more variance
            base_proj = player['Salary'] / 250
            variance_factor = 0.4  # High variance
        else:
            # Hitters: different variance by position
            variance_factor = 0.3
        
        # Game situation factors
        game = player['Game']
        if '@' in game:
            away_team, home_team = game.split('@')
            is_home = (player['Team'] == home_team)
        else:
            is_home = True
            
        # Home field advantage
        if is_home:
            base_proj *= 1.05
        
        # Weather impact (if available)
        if self.weather_data is not None and len(self.weather_data) > 0:
            temp = self.weather_data.iloc[0].get('temperature', 70)
            wind = self.weather_data.iloc[0].get('wind_speed', 5)
            
            # Temperature impact (hitters like heat)
            if player['Position'] != 'P':
                if temp > 75:
                    base_proj *= 1.08  # Hot weather helps hitters
                elif temp < 60:
                    base_proj *= 0.95  # Cold weather hurts hitters
                    
            # Wind impact
            if wind > 10:
                base_proj *= 0.97  # High wind generally hurts offense
        
        # Generate simulations with realistic distribution
        simulations = []
        for _ in range(num_sims):
            # Use gamma distribution for realistic fantasy scoring
            random_factor = np.random.gamma(2, variance_factor)
            simulated_score = base_proj * random_factor
            
            # Add some completely random variance (injuries, ejections, etc.)
            if np.random.random() < 0.05:  # 5% chance of disaster
                simulated_score *= 0.1
            elif np.random.random() < 0.15:  # 15% chance of explosion
                simulated_score *= 2.5
                
            simulations.append(max(0, simulated_score))  # Can't go negative
            
        return simulations
    
    def calculate_ownership_projections(self):
        """Calculate advanced ownership projections for confirmed starters"""
        logger.info("OWNERSHIP: CALCULATING OWNERSHIP PROJECTIONS")
        logger.info("=" * 60)
        
        ownership_data = []
        
        for _, player in self.confirmed_players.iterrows():
            # Multi-factor ownership model
            base_ownership = 0.05
            
            # Salary factor (cheaper = higher owned)
            salary_factor = 1 - (player['Salary'] / self.confirmed_players['Salary'].max()) * 0.3
            
            # Projection factor (from simulations if available)
            if self.simulation_results is not None:
                sim_player = self.simulation_results[self.simulation_results['player_name'] == player['Nickname']]
                if len(sim_player) > 0:
                    proj_factor = (sim_player.iloc[0]['sim_mean'] / self.simulation_results['sim_mean'].max()) * 0.4
                else:
                    proj_factor = 0.2
            else:
                proj_factor = 0.2
            
            # Position factor
            position_ownership = {
                'P': 0.15, 'C': 0.08, '1B': 0.12, '2B': 0.10, 
                '3B': 0.10, 'SS': 0.12, 'OF': 0.15
            }
            pos_factor = position_ownership.get(player['Position'], 0.12)
            
            # Game stack factor (only 2 games = higher ownership)
            game_factor = 0.15
            
            # Star bonus (top salaries)
            star_threshold = self.confirmed_players['Salary'].quantile(0.8)
            star_bonus = 0.05 if player['Salary'] >= star_threshold else 0
            
            # Calculate final ownership
            ownership = base_ownership + salary_factor + proj_factor + pos_factor + game_factor + star_bonus
            ownership = np.clip(ownership, 0.02, 0.95)
            
            ownership_data.append({
                'player_name': player['Nickname'],
                'position': player['Position'],
                'salary': player['Salary'],
                'projected_ownership': ownership,
                'ownership_tier': self._get_ownership_tier(ownership)
            })
        
        self.ownership_projections = pd.DataFrame(ownership_data)
        
        # Log ownership distribution
        tier_counts = self.ownership_projections['ownership_tier'].value_counts()
        logger.info(" OWNERSHIP DISTRIBUTION:")
        for tier, count in tier_counts.items():
            avg_own = self.ownership_projections[self.ownership_projections['ownership_tier'] == tier]['projected_ownership'].mean()
            logger.info(f"   {tier}: {count} players (avg {avg_own:.1%})")
        
        return self.ownership_projections
    
    def _get_ownership_tier(self, ownership):
        """Categorize ownership into tiers"""
        if ownership >= 0.40:
            return 'Super Chalk'
        elif ownership >= 0.25:
            return 'Chalk'
        elif ownership >= 0.15:
            return 'Medium'
        elif ownership >= 0.08:
            return 'Contrarian'
        else:
            return 'Deep Contrarian'
    
    def calculate_correlations(self):
        """Calculate player correlations for stacking"""
        logger.info("DATA: CALCULATING PLAYER CORRELATIONS")
        logger.info("=" * 60)
        
        correlations = {}
        
        # Team correlations (same team players)
        for team in self.confirmed_players['Team'].unique():
            team_players = self.confirmed_players[self.confirmed_players['Team'] == team]['Nickname'].tolist()
            correlations[f"{team}_stack"] = {
                'players': team_players,
                'correlation': 0.85,  # High correlation for same team
                'type': 'team_stack'
            }
        
        # Game correlations (opposing pitchers vs hitters)
        for game in self.confirmed_players['Game'].unique():
            game_players = self.confirmed_players[self.confirmed_players['Game'] == game]['Nickname'].tolist()
            correlations[f"{game}_game"] = {
                'players': game_players,
                'correlation': 0.65,  # Medium correlation for same game
                'type': 'game_correlation'
            }
        
        # Pitcher vs opposing hitters (negative correlation)
        pitchers = self.confirmed_players[self.confirmed_players['Position'] == 'P']
        for _, pitcher in pitchers.iterrows():
            game = pitcher['Game']
            pitcher_team = pitcher['Team']
            
            # Find opposing hitters
            if '@' in game:
                away_team, home_team = game.split('@')
                opposing_team = home_team if pitcher_team == away_team else away_team
            else:
                continue
                
            opposing_hitters = self.confirmed_players[
                (self.confirmed_players['Team'] == opposing_team) & 
                (self.confirmed_players['Position'] != 'P')
            ]['Nickname'].tolist()
            
            if opposing_hitters:
                correlations[f"{pitcher['Nickname']}_vs_opp"] = {
                    'pitcher': pitcher['Nickname'],
                    'opposing_hitters': opposing_hitters,
                    'correlation': -0.3,  # Negative correlation
                    'type': 'pitcher_vs_hitters'
                }
        
        self.correlations = correlations
        logger.info(f"PROGRESS: Calculated {len(correlations)} correlation relationships")
        
        return correlations
    
    def create_optimized_projections(self):
        """Combine all factors into final optimized projections"""
        logger.info(" CREATING OPTIMIZED PROJECTIONS")
        logger.info("=" * 60)
        
        optimized_players = self.confirmed_players.copy()
        
        # Add simulation data
        if self.simulation_results is not None:
            optimized_players = optimized_players.merge(
                self.simulation_results[['player_name', 'sim_mean', 'sim_ceiling', 'sim_floor', 'sim_upside', 'consistency']],
                left_on='Nickname', right_on='player_name', how='left'
            )
        
        # Add ownership data
        if self.ownership_projections is not None:
            optimized_players = optimized_players.merge(
                self.ownership_projections[['player_name', 'projected_ownership', 'ownership_tier']],
                left_on='Nickname', right_on='player_name', how='left', suffixes=('', '_own')
            )
        
        # Calculate value metrics
        optimized_players['value'] = optimized_players['sim_mean'] / (optimized_players['Salary'] / 1000)
        optimized_players['ceiling_value'] = optimized_players['sim_ceiling'] / (optimized_players['Salary'] / 1000)
        optimized_players['leverage'] = optimized_players['sim_upside'] / optimized_players['projected_ownership']
        
        # Tournament scoring (accounts for leverage and upside)
        optimized_players['tournament_score'] = (
            optimized_players['sim_mean'] * 0.4 +
            optimized_players['sim_upside'] * 0.4 + 
            optimized_players['leverage'] * 0.2
        )
        
        # Cash game scoring (accounts for floor and consistency)
        optimized_players['cash_score'] = (
            optimized_players['sim_mean'] * 0.5 +
            optimized_players['sim_floor'] * 0.3 +
            optimized_players['consistency'] * 0.2
        )
        
        # Save optimized projections
        output_file = '../data/confirmed_optimized_projections.csv'
        optimized_players.to_csv(output_file, index=False)
        
        logger.info(f" Saved optimized projections: {output_file}")
        logger.info(f"DATA: {len(optimized_players)} players with complete optimization data")
        
        return optimized_players
    
    def generate_strategy_recommendations(self):
        """Generate strategic recommendations based on optimization"""
        logger.info("TARGET: GENERATING STRATEGY RECOMMENDATIONS")
        logger.info("=" * 60)
        
        if self.ownership_projections is None:
            return {}
        
        recommendations = {
            'chalk_plays': [],
            'contrarian_plays': [], 
            'value_plays': [],
            'leverage_plays': [],
            'stack_recommendations': []
        }
        
        # Chalk plays (high ownership, good projections)
        chalk = self.ownership_projections[
            self.ownership_projections['ownership_tier'].isin(['Chalk', 'Super Chalk'])
        ].head(5)
        recommendations['chalk_plays'] = chalk.to_dict('records')
        
        # Contrarian plays (low ownership, decent projections)
        contrarian = self.ownership_projections[
            self.ownership_projections['ownership_tier'].isin(['Contrarian', 'Deep Contrarian'])
        ].head(5)
        recommendations['contrarian_plays'] = contrarian.to_dict('records')
        
        # Stack recommendations
        if self.correlations:
            for stack_name, stack_data in self.correlations.items():
                if stack_data['type'] == 'team_stack' and len(stack_data['players']) >= 3:
                    recommendations['stack_recommendations'].append({
                        'stack': stack_name,
                        'players': stack_data['players'][:4],  # Top 4 players
                        'correlation': stack_data['correlation']
                    })
        
        return recommendations
    
    def run_complete_optimization(self):
        """Run the complete optimization pipeline"""
        logger.info("START: ULTIMATE CONFIRMED STARTERS OPTIMIZATION")
        logger.info("TARGET: Complete pipeline: Simulations + Ownership + Correlations")
        logger.info("=" * 70)
        
        # Step 1: Load all data
        if not self.load_all_data():
            logger.error("ERROR: Failed to load confirmed starters data")
            return None
        
        # Step 2: Run simulations
        self.run_game_simulations(2000)
        
        # Step 3: Calculate ownership
        self.calculate_ownership_projections()
        
        # Step 4: Calculate correlations
        self.calculate_correlations()
        
        # Step 5: Create optimized projections
        optimized_players = self.create_optimized_projections()
        
        # Step 6: Generate recommendations
        recommendations = self.generate_strategy_recommendations()
        
        # Summary
        logger.info("=" * 70)
        logger.info("COMPLETE: COMPLETE OPTIMIZATION FINISHED!")
        logger.info(f"SUCCESS: {len(optimized_players)} confirmed players optimized")
        logger.info(f" 2000 simulations per player completed")
        logger.info(f"OWNERSHIP: Advanced ownership projections calculated")
        logger.info(f"DATA: {len(self.correlations)} correlation patterns identified")
        logger.info(f"TARGET: Ready for advanced lineup construction")
        
        return {
            'optimized_players': optimized_players,
            'recommendations': recommendations,
            'correlations': self.correlations
        }

def main():
    """Main optimization function"""
    optimizer = ConfirmedStartersOptimizer()
    results = optimizer.run_complete_optimization()
    
    if results:
        logger.info("LINEUP: OPTIMIZATION COMPLETE - READY FOR LINEUP GENERATION!")
    else:
        logger.error("ERROR: Optimization failed!")

if __name__ == "__main__":
    main()
