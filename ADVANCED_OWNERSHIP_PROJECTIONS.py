#!/usr/bin/env python3
"""
ADVANCED OWNERSHIP PROJECTIONS FOR DFS MLB
Build sophisticated ownership models based on real DFS patterns
"""

import pandas as pd
import numpy as np
import logging
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedOwnershipProjector:
    """Advanced ownership projection system for DFS MLB"""
    
    def __init__(self):
        self.ownership_factors = {
            # Base factors that drive ownership
            'salary_weight': 0.25,      # Higher salary = higher ownership
            'projection_weight': 0.30,  # Higher projection = higher ownership  
            'value_weight': 0.20,       # Higher value = higher ownership
            'game_stack_weight': 0.15,  # Game environment factors
            'position_weight': 0.10     # Position-specific ownership patterns
        }
        
        # Position ownership tendencies
        self.position_ownership_mults = {
            'P': 1.4,      # Pitchers have highest ownership concentration
            'C': 0.7,      # Catchers lowest owned
            'OF': 1.1,     # Outfield slightly higher
            '1B': 1.0,     # First base baseline
            '2B': 0.9,     # Middle infield lower
            '3B': 1.0,     # Third base baseline  
            'SS': 0.9      # Shortstop lower
        }
        
        # Salary tier ownership patterns
        self.salary_ownership_curves = {
            'P': {
                'min_salary': 6000, 'max_salary': 12000,
                'min_ownership': 0.02, 'max_ownership': 0.45
            },
            'C': {
                'min_salary': 4500, 'max_salary': 9000,
                'min_ownership': 0.01, 'max_ownership': 0.25
            },
            'hitter': {
                'min_salary': 4500, 'max_salary': 11000,
                'min_ownership': 0.02, 'max_ownership': 0.35
            }
        }
        
    def calculate_base_ownership_from_salary(self, salary, position):
        """Calculate base ownership from salary using realistic curves"""
        
        # Determine salary curve to use
        if position == 'P':
            curve = self.salary_ownership_curves['P']
        elif position == 'C':
            curve = self.salary_ownership_curves['C']
        else:
            curve = self.salary_ownership_curves['hitter']
        
        # Normalize salary within position
        salary_pct = (salary - curve['min_salary']) / (curve['max_salary'] - curve['min_salary'])
        salary_pct = max(0, min(1, salary_pct))  # Clamp to [0,1]
        
        # Use logarithmic curve for ownership (high salaries get exponentially more ownership)
        ownership_range = curve['max_ownership'] - curve['min_ownership']
        
        # Logarithmic scaling - higher salaries get disproportionately more ownership
        log_factor = np.log(1 + salary_pct * 9) / np.log(10)  # Scale 0-1 using log(1) to log(10)
        base_ownership = curve['min_ownership'] + (ownership_range * log_factor)
        
        return base_ownership
    
    def calculate_projection_ownership_boost(self, projection, position):
        """Calculate ownership boost from high projections"""
        
        # Position-specific projection thresholds
        projection_thresholds = {
            'P': {'low': 25, 'high': 45},
            'C': {'low': 8, 'high': 18},
            'hitter': {'low': 10, 'high': 20}
        }
        
        if position == 'P':
            thresh = projection_thresholds['P']
        elif position == 'C':
            thresh = projection_thresholds['C']
        else:
            thresh = projection_thresholds['hitter']
        
        # Calculate projection percentile
        proj_pct = (projection - thresh['low']) / (thresh['high'] - thresh['low'])
        proj_pct = max(0, min(1, proj_pct))
        
        # High projections get exponential ownership boost
        ownership_boost = 1 + (proj_pct ** 1.5) * 0.8  # Up to 80% boost for elite projections
        
        return ownership_boost
    
    def calculate_value_ownership_factor(self, projection, salary):
        """Calculate ownership factor based on value (projection per $1000)"""
        
        value = projection / (salary / 1000)
        
        # Value thresholds
        if value >= 4.0:
            return 1.4      # Elite value gets big ownership boost
        elif value >= 3.5:
            return 1.25     # Great value
        elif value >= 3.0:
            return 1.1      # Good value
        elif value >= 2.5:
            return 1.0      # Average value
        elif value >= 2.0:
            return 0.85     # Below average value
        else:
            return 0.7      # Poor value gets ownership penalty
    
    def calculate_game_environment_factor(self, team, opponent, vegas_total=None, implied_runs=None):
        """Calculate ownership factor based on game environment"""
        
        base_factor = 1.0
        
        # Vegas total factor (higher totals = more ownership)
        if vegas_total is not None:
            if vegas_total >= 9.5:
                base_factor *= 1.3      # High-scoring game
            elif vegas_total >= 8.5:
                base_factor *= 1.15     # Above average scoring
            elif vegas_total <= 7.5:
                base_factor *= 0.85     # Low-scoring game
        
        # Implied runs factor (higher implied runs = more ownership)
        if implied_runs is not None:
            if implied_runs >= 5.5:
                base_factor *= 1.25     # High implied runs
            elif implied_runs >= 4.5:
                base_factor *= 1.1      # Above average
            elif implied_runs <= 3.5:
                base_factor *= 0.8      # Low implied runs
        
        return base_factor
    
    def apply_stacking_ownership_boost(self, ownership_dict, stacking_teams):
        """Apply ownership boost for players on popular stacking teams"""
        
        boosted_ownership = ownership_dict.copy()
        
        for player_id, player_data in ownership_dict.items():
            if player_data['team'] in stacking_teams:
                # Players on popular stacking teams get ownership boost
                boost = 1.2 if player_data['position'] != 'P' else 1.0  # Only hitters get stack boost
                boosted_ownership[player_id]['ownership'] *= boost
        
        return boosted_ownership
    
    def add_ownership_variance(self, base_ownership, variance_factor=0.15):
        """Add realistic variance to ownership projections"""
        
        # Higher ownership players have higher variance
        variance = variance_factor * (1 + base_ownership)
        
        # Generate variance using normal distribution
        variance_multiplier = np.random.normal(1.0, variance)
        variance_multiplier = max(0.3, min(2.0, variance_multiplier))  # Clamp variance
        
        return base_ownership * variance_multiplier
    
    def project_player_ownership(self, player_data, game_environment=None, stacking_teams=None):
        """Project ownership for a single player"""
        
        salary = player_data['Salary']
        projection = player_data.get('FPPG', player_data.get('enhanced_fppg', 10))
        position = player_data['Position']
        team = player_data.get('Team', '')
        
        # 1. Base ownership from salary
        base_ownership = self.calculate_base_ownership_from_salary(salary, position)
        
        # 2. Projection boost
        proj_boost = self.calculate_projection_ownership_boost(projection, position)
        
        # 3. Value factor
        value_factor = self.calculate_value_ownership_factor(projection, salary)
        
        # 4. Position multiplier
        pos_mult = self.position_ownership_mults.get(position, 1.0)
        
        # 5. Game environment
        game_factor = 1.0
        if game_environment:
            game_factor = self.calculate_game_environment_factor(
                team, 
                game_environment.get('opponent', ''),
                game_environment.get('vegas_total'),
                game_environment.get('implied_runs')
            )
        
        # Combine all factors
        projected_ownership = (
            base_ownership * 
            proj_boost * 
            value_factor * 
            pos_mult * 
            game_factor
        )
        
        # Apply stacking boost if applicable
        if stacking_teams and team in stacking_teams and position != 'P':
            projected_ownership *= 1.2
        
        # Add variance
        projected_ownership = self.add_ownership_variance(projected_ownership)
        
        # Clamp to realistic bounds
        projected_ownership = max(0.005, min(0.50, projected_ownership))  # 0.5% to 50%
        
        return projected_ownership
    
    def project_slate_ownership(self, players_df, game_environment_df=None, identify_stacking_teams=True):
        """Project ownership for entire slate"""
        
        logger.info("TARGET: PROJECTING SLATE OWNERSHIP")
        logger.info("=" * 50)
        
        projected_ownership = {}
        
        # Identify popular stacking teams if requested
        stacking_teams = []
        if identify_stacking_teams:
            # Find teams with high projection density
            team_scores = players_df.groupby('Team').agg({
                'FPPG': 'sum',
                'Salary': 'sum'
            }).reset_index()
            
            team_scores['team_value'] = team_scores['FPPG'] / (team_scores['Salary'] / 1000)
            top_stack_teams = team_scores.nlargest(6, 'team_value')['Team'].tolist()
            stacking_teams = top_stack_teams
            
            logger.info(f" Top stacking teams: {stacking_teams}")
        
        # Project ownership for each player
        for idx, player in players_df.iterrows():
            
            # Get game environment if available
            game_env = None
            if game_environment_df is not None:
                game_env = game_environment_df.get(player['Team'], {})
            
            # Project ownership
            ownership = self.project_player_ownership(
                player, 
                game_environment=game_env,
                stacking_teams=stacking_teams
            )
            
            projected_ownership[idx] = {
                'player_name': f"{player['First Name']} {player['Last Name']}" if 'First Name' in player else player.get('Player', ''),
                'position': player['Position'],
                'team': player['Team'],
                'salary': player['Salary'],
                'projection': player.get('FPPG', player.get('enhanced_fppg', 10)),
                'ownership': ownership
            }
        
        # Convert to DataFrame for analysis
        ownership_df = pd.DataFrame.from_dict(projected_ownership, orient='index')
        
        # Add ownership tiers
        ownership_df['ownership_tier'] = pd.cut(
            ownership_df['ownership'], 
            bins=[0, 0.05, 0.10, 0.20, 0.35, 1.0],
            labels=['Contrarian', 'Low', 'Medium', 'High', 'Chalk']
        )
        
        # Calculate leverage scores (projection / ownership)
        ownership_df['leverage_score'] = ownership_df['projection'] / (ownership_df['ownership'] * 100 + 1)
        
        logger.info(f"SUCCESS: Projected ownership for {len(ownership_df)} players")
        logger.info(f"DATA: Ownership range: {ownership_df['ownership'].min():.1%} to {ownership_df['ownership'].max():.1%}")
        logger.info(f"PROGRESS: Ownership tiers: {ownership_df['ownership_tier'].value_counts().to_dict()}")
        
        return ownership_df
    
    def analyze_ownership_opportunities(self, ownership_df):
        """Analyze ownership for tournament opportunities"""
        
        logger.info("\nTARGET: OWNERSHIP OPPORTUNITY ANALYSIS")
        logger.info("=" * 50)
        
        # High leverage plays (good projection, low ownership)
        high_leverage = ownership_df[
            (ownership_df['leverage_score'] >= ownership_df['leverage_score'].quantile(0.80)) &
            (ownership_df['projection'] >= 10)
        ].sort_values('leverage_score', ascending=False)
        
        logger.info(f"START: TOP LEVERAGE PLAYS ({len(high_leverage)}):")
        for idx, player in high_leverage.head(10).iterrows():
            logger.info(f"  {player['player_name']} ({player['position']}) - "
                       f"${player['salary']} | {player['projection']:.1f} proj | "
                       f"{player['ownership']:.1%} own | {player['leverage_score']:.2f} leverage")
        
        # Contrarian plays
        contrarian = ownership_df[
            (ownership_df['ownership_tier'] == 'Contrarian') &
            (ownership_df['projection'] >= 8)
        ].sort_values('projection', ascending=False)
        
        logger.info(f"\n CONTRARIAN OPPORTUNITIES ({len(contrarian)}):")
        for idx, player in contrarian.head(8).iterrows():
            logger.info(f"  {player['player_name']} ({player['position']}) - "
                       f"${player['salary']} | {player['projection']:.1f} proj | "
                       f"{player['ownership']:.1%} own")
        
        # Chalk plays to consider
        chalk = ownership_df[
            ownership_df['ownership_tier'] == 'Chalk'
        ].sort_values('projection', ascending=False)
        
        logger.info(f"\n CHALK PLAYS ({len(chalk)}):")
        for idx, player in chalk.head(8).iterrows():
            logger.info(f"  {player['player_name']} ({player['position']}) - "
                       f"${player['salary']} | {player['projection']:.1f} proj | "
                       f"{player['ownership']:.1%} own")
        
        return {
            'high_leverage': high_leverage,
            'contrarian': contrarian,
            'chalk': chalk
        }

def main():
    """Test the advanced ownership projector"""
    
    try:
        # Load current projections using dynamic date
        current_date = datetime.now().strftime("%Y%m%d")
        logger.info("SUCCESS: Loading enhanced projections for ownership analysis...")
        
        # Try to find today's enhanced projections file
        import glob
        enhanced_files = glob.glob(f"../data/enhanced_projections_{current_date}_*.csv")
        if enhanced_files:
            projections_file = enhanced_files[-1]  # Use the latest file from today
            logger.info(f"DATA: Using projections file: {projections_file}")
        else:
            # Fallback to fd_slate_today.csv if no enhanced projections
            projections_file = "../fd_current_slate/fd_slate_today.csv"
            logger.info(f"DATA: Using fallback slate file: {projections_file}")
        
        projections = pd.read_csv(projections_file)
        logger.info(f"SUCCESS: Loaded {len(projections)} player projections")
        
        # CRITICAL: Filter for healthy players and probable pitchers only
        logger.info("FILTER: Applying injury and probable pitcher filters...")
        original_count = len(projections)
        
        # Filter out injured players (IL, O, DTD)
        if 'Injury Indicator' in projections.columns:
            projections = projections[
                (projections['Injury Indicator'].isna()) | 
                (projections['Injury Indicator'] == '') |
                (projections['Injury Indicator'] == ' ')
            ]
            logger.info(f" Filtered out {original_count - len(projections)} injured players")
        
        # For pitchers: Keep only probable pitchers (marked "Yes")
        if 'Probable Pitcher' in projections.columns:
            pitcher_mask = projections['Position'] == 'P'
            prob_pitchers = projections[pitcher_mask & (projections['Probable Pitcher'] == 'Yes')]
            non_pitchers = projections[projections['Position'] != 'P']
            projections = pd.concat([prob_pitchers, non_pitchers], ignore_index=True)
            logger.info(f"BASEBALL: Kept {len(prob_pitchers)} probable pitchers only")
        
        # For hitters: Keep only starting lineup players (Batting Order > 0)
        if 'Batting Order' in projections.columns:
            hitter_mask = projections['Position'] != 'P'
            starting_hitters = projections[hitter_mask & (projections['Batting Order'] > 0)]
            pitchers = projections[projections['Position'] == 'P']
            projections = pd.concat([pitchers, starting_hitters], ignore_index=True)
            logger.info(f" Kept {len(starting_hitters)} starting hitters only")
        
        logger.info(f"SUCCESS: Final filtered players: {len(projections)} (removed {original_count - len(projections)} unplayable)")
        logger.info(f"SUCCESS: Loaded {len(projections)} player projections")
        
        # Initialize projector
        projector = AdvancedOwnershipProjector()
        
        # Project ownership
        ownership_df = projector.project_slate_ownership(projections)
        
        # Analyze opportunities
        opportunities = projector.analyze_ownership_opportunities(ownership_df)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/advanced_ownership_projections_{timestamp}.csv"
        ownership_df.to_csv(output_file, index=False)
        
        logger.info(f" Saved ownership projections to {output_file}")
        
        return ownership_df, opportunities
        
    except Exception as e:
        logger.error(f"ERROR: Error in ownership projection: {str(e)}")
        raise

if __name__ == "__main__":
    ownership_results = main()
