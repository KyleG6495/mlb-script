#!/usr/bin/env python3
"""
ELITE_DFS_OPTIMIZER - Advanced ownership modeling + player correlation matrix
Adds the missing tournament edge: ownership projections and correlation analysis
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EliteDFSOptimizer:
    def __init__(self):
        self.ownership_model = None
        self.correlation_matrix = None
        
    def enhance_with_elite_features(self, df):
        """Add elite tournament features to existing data"""
        
        logger.info("START: ELITE DFS OPTIMIZER")
        logger.info("=" * 50)
        logger.info("Adding ownership modeling + correlation analysis...")
        
        df_elite = df.copy()
        
        # 1. Add sophisticated ownership projections
        df_elite = self.add_ownership_projections(df_elite)
        
        # 2. Add ceiling/floor variance modeling
        df_elite = self.add_variance_projections(df_elite)
        
        # 3. Add player correlation scores
        df_elite = self.add_correlation_scores(df_elite)
        
        # 4. Add leverage scores (value vs ownership)
        df_elite = self.add_leverage_scores(df_elite)
        
        logger.info(f"SUCCESS: Elite features added to {len(df_elite)} players")
        
        return df_elite
    
    def add_ownership_projections(self, df):
        """Advanced ownership modeling based on multiple factors"""
        
        logger.info("DATA: BUILDING ADVANCED OWNERSHIP MODEL")
        
        df['ownership_proj'] = 0.0
        
        for idx, player in df.iterrows():
            ownership = 5.0  # Base ownership percentage
            
            # SALARY-BASED OWNERSHIP (Most Important Factor)
            salary = player['Salary']
            if salary >= 11000:  # Premium aces
                ownership += 18
            elif salary >= 9000:  # Solid starters
                ownership += 12
            elif salary >= 7000:  # Mid-tier
                ownership += 6
            elif salary >= 5000:  # Value plays
                ownership += 2
            elif salary <= 3000:  # Min salary
                ownership -= 4
            
            # PROJECTION-BASED OWNERSHIP
            projection = player.get('FPPG', 0)
            if projection >= 15:  # Elite projections
                ownership += 10
            elif projection >= 12:  # Strong projections
                ownership += 6
            elif projection >= 9:  # Decent projections
                ownership += 2
            elif projection < 6:  # Poor projections
                ownership -= 5
            
            # POSITION-BASED OWNERSHIP
            position = player['Position']
            if position == 'P':
                # Probable pitcher status is huge for ownership
                if player.get('Probable Pitcher') == 'Yes':
                    ownership += 12
                else:
                    ownership -= 15  # Non-probable pitchers rarely owned
            else:
                # Batting order significantly affects ownership
                batting_order = player.get('Batting Order', 9)
                if batting_order == 1:  # Leadoff hitters popular
                    ownership += 6
                elif batting_order <= 3:  # Top of order
                    ownership += 4
                elif batting_order <= 5:  # Heart of order
                    ownership += 2
                elif batting_order >= 8:  # Bottom of order
                    ownership -= 3
                elif batting_order == 0:  # Bench players
                    ownership -= 20
            
            # TEAM POPULARITY (Some teams always higher owned)
            team = player['Team']
            popular_teams = ['LAD', 'NYY', 'HOU', 'ATL', 'NYM', 'BOS']
            unpopular_teams = ['MIA', 'OAK', 'COL', 'KC', 'DET']
            
            if team in popular_teams:
                ownership += 4
            elif team in unpopular_teams:
                ownership -= 2
            
            # INJURY STATUS (Huge ownership impact)
            injury_status = player.get('Injury Indicator', '')
            if injury_status in ['IL', 'DTD', 'O']:
                ownership -= 20  # Injured players avoid like plague
            
            # GAME ENVIRONMENT FACTORS
            # High total games get more ownership
            # Pitcher matchups matter
            # Weather conditions (if available)
            
            # ADD RANDOMNESS (Market isn't perfectly efficient)
            ownership += np.random.normal(0, 2.5)
            
            # Keep in realistic bounds
            ownership = max(0.1, min(45.0, ownership))
            
            df.at[idx, 'ownership_proj'] = ownership
        
        # Log ownership distribution
        avg_own = df['ownership_proj'].mean()
        std_own = df['ownership_proj'].std()
        logger.info(f"Ownership model: {avg_own:.1f}% avg, {std_own:.1f}% std dev")
        
        return df
    
    def add_variance_projections(self, df):
        """Add ceiling and floor projections for tournament optimization"""
        
        logger.info("PROGRESS: BUILDING CEILING/FLOOR MODEL")
        
        for idx, player in df.iterrows():
            base_proj = player.get('FPPG', 0)
            position = player['Position']
            salary = player['Salary']
            
            if position == 'P':
                # PITCHER VARIANCE MODEL
                # High ceiling: Complete game, low ERA
                # Low floor: Early exit, blown up
                
                if salary >= 10000:  # Ace pitchers
                    ceiling_mult = 2.0  # Can get 40-50+ points
                    floor_mult = 0.3   # Still risky if matched up poorly
                    variance = 0.7
                else:  # Value pitchers
                    ceiling_mult = 2.5  # Higher upside if everything clicks
                    floor_mult = 0.1   # Higher bust risk
                    variance = 0.9
            
            else:
                # HITTER VARIANCE MODEL
                # High ceiling: Multi-homer, grand slam games
                # Low floor: 0-4 with strikeouts
                
                batting_order = player.get('Batting Order', 9)
                
                if batting_order <= 3:  # Top of order
                    ceiling_mult = 2.2  # Runs + RBI opportunities
                    floor_mult = 0.1   # Can always get 0
                    variance = 0.5
                elif batting_order <= 6:  # Heart of order
                    ceiling_mult = 2.5  # Most RBI opportunities
                    floor_mult = 0.0   # Can get 0 if team struggles
                    variance = 0.6
                else:  # Bottom of order
                    ceiling_mult = 2.0  # Limited opportunities
                    floor_mult = 0.0
                    variance = 0.7
                
                # Salary adjustments
                if salary <= 3000:  # Min salary players
                    ceiling_mult += 0.3  # Higher variance
                    variance += 0.2
            
            # Calculate ceiling and floor
            ceiling = base_proj * ceiling_mult
            floor = max(0, base_proj * floor_mult)
            
            # Add some randomness (ensure positive std)
            ceiling += np.random.normal(0, max(0.5, abs(base_proj * 0.1)))
            floor = max(0, floor + np.random.normal(0, max(0.3, abs(base_proj * 0.05))))
            
            df.at[idx, 'ceiling_proj'] = ceiling
            df.at[idx, 'floor_proj'] = floor
            df.at[idx, 'variance_score'] = ceiling - floor
        
        avg_ceiling = df['ceiling_proj'].mean()
        logger.info(f"Ceiling model: {avg_ceiling:.1f} avg ceiling projection")
        
        return df
    
    def add_correlation_scores(self, df):
        """Build player correlation matrix for stacking optimization"""
        
        logger.info(" BUILDING CORRELATION MATRIX")
        
        df['correlation_score'] = 0.0
        df['stack_multiplier'] = 1.0
        
        # Analyze each team for internal correlations
        for team in df['Team'].unique():
            team_players = df[df['Team'] == team]
            team_hitters = team_players[team_players['Position'] != 'P']
            
            if len(team_hitters) < 3:  # Need enough players for correlation
                continue
            
            # Calculate team offensive strength
            team_avg_proj = team_hitters['FPPG'].mean() if len(team_hitters) > 0 else 0
            team_ceiling = team_hitters['ceiling_proj'].mean() if len(team_hitters) > 0 else 0
            
            for idx, player in team_players.iterrows():
                correlation_score = 0.0
                stack_multiplier = 1.0
                
                if player['Position'] != 'P':  # HITTER CORRELATIONS
                    batting_order = player.get('Batting Order', 9)
                    
                    # SEQUENTIAL BATTING ORDER CORRELATION
                    # Players who bat close together are correlated
                    if batting_order <= 2:  # Leadoff types
                        correlation_score += 0.12  # Sets table for others
                        stack_multiplier += 0.08
                    elif batting_order in [3, 4, 5]:  # RBI positions
                        correlation_score += 0.20  # Benefits from runners on base
                        stack_multiplier += 0.12
                    elif batting_order >= 6:  # Bottom order
                        correlation_score += 0.08  # Less correlation
                        stack_multiplier += 0.05
                    
                    # TEAM OFFENSIVE ENVIRONMENT
                    if team_avg_proj >= 10:  # Strong offensive team
                        stack_multiplier += 0.15  # Rising tide lifts all boats
                    elif team_avg_proj >= 8:  # Decent offense
                        stack_multiplier += 0.08
                    
                    # POSITION-SPECIFIC CORRELATIONS
                    if batting_order == 1:  # Leadoff hitter
                        correlation_score += 0.10  # Scores if team does well
                    elif batting_order in [3, 4]:  # Cleanup hitters
                        correlation_score += 0.15  # Most correlated with team success
                
                else:  # PITCHER CORRELATIONS
                    # Pitchers have slight negative correlation with opposing hitters
                    # But we don't usually stack opposing pitcher anyway
                    stack_multiplier = 0.98
                
                df.at[idx, 'correlation_score'] = correlation_score
                df.at[idx, 'stack_multiplier'] = stack_multiplier
        
        avg_corr = df['correlation_score'].mean()
        avg_mult = df['stack_multiplier'].mean()
        logger.info(f"Correlation model: {avg_corr:.3f} avg correlation, {avg_mult:.3f} avg multiplier")
        
        return df
    
    def add_leverage_scores(self, df):
        """Calculate leverage scores (value vs ownership for tournaments)"""
        
        logger.info("TARGET: CALCULATING LEVERAGE SCORES")
        
        for idx, player in df.iterrows():
            ceiling = player.get('ceiling_proj', player.get('FPPG', 0))
            ownership = player['ownership_proj']
            salary = player['Salary']
            
            # LEVERAGE = (CEILING / OWNERSHIP) * SALARY_EFFICIENCY
            points_per_dollar = (ceiling / salary) * 1000
            
            if ownership > 0:
                leverage_base = ceiling / ownership
            else:
                leverage_base = ceiling * 10  # Very low owned
            
            # Final leverage score
            leverage = leverage_base * points_per_dollar
            
            # TOURNAMENT LEVERAGE BOOSTS
            # Low ownership + high ceiling = tournament gold
            if ownership <= 5 and ceiling >= 20:
                leverage *= 1.5  # Major boost for contrarian bombs
            elif ownership <= 10 and ceiling >= 15:
                leverage *= 1.25  # Good contrarian plays
            
            # LEVERAGE PENALTIES
            # High ownership + medium ceiling = tournament trap
            if ownership >= 25 and ceiling < 18:
                leverage *= 0.7  # Penalize chalk without upside
            
            df.at[idx, 'leverage_score'] = leverage
            df.at[idx, 'points_per_dollar'] = points_per_dollar
        
        # Normalize leverage to 0-100 scale for easier interpretation
        max_leverage = df['leverage_score'].max()
        if max_leverage > 0:
            df['leverage_score'] = (df['leverage_score'] / max_leverage) * 100
        
        avg_leverage = df['leverage_score'].mean()
        logger.info(f"Leverage model: {avg_leverage:.1f} avg leverage score")
        
        return df
    
    def identify_elite_stacks(self, df):
        """Identify best stacking opportunities using all elite metrics"""
        
        logger.info("LINEUP: IDENTIFYING ELITE STACKING OPPORTUNITIES")
        
        stack_opportunities = []
        
        for team in df['Team'].unique():
            team_players = df[df['Team'] == team]
            team_hitters = team_players[team_players['Position'] != 'P']
            
            if len(team_hitters) < 4:  # Need stackable depth
                continue
            
            # CALCULATE COMPREHENSIVE STACK METRICS
            avg_projection = team_hitters['FPPG'].mean()
            avg_ceiling = team_hitters['ceiling_proj'].mean()
            avg_ownership = team_hitters['ownership_proj'].mean()
            avg_leverage = team_hitters['leverage_score'].mean()
            total_correlation = team_hitters['correlation_score'].sum()
            avg_stack_mult = team_hitters['stack_multiplier'].mean()
            value_players = len(team_hitters[team_hitters['Salary'] <= 3500])
            
            # ELITE STACK SCORE CALCULATION
            # Weights based on tournament importance
            stack_score = (
                (avg_ceiling * 0.25) +          # Ceiling potential (25%)
                (avg_leverage * 0.20) +         # Leverage vs field (20%)
                ((15 - avg_ownership) * 0.15) + # Contrarian value (15%)
                (total_correlation * 0.15) +    # Internal correlation (15%)
                (avg_stack_mult * 15) +         # Stack multiplier (15%)
                (value_players * 2)             # Value player count (10%)
            )
            
            stack_opportunities.append({
                'team': team,
                'stack_score': stack_score,
                'avg_projection': avg_projection,
                'avg_ceiling': avg_ceiling,
                'avg_ownership': avg_ownership,
                'avg_leverage': avg_leverage,
                'correlation_total': total_correlation,
                'value_players': value_players,
                'player_count': len(team_hitters)
            })
        
        # Sort by elite stack score
        stack_df = pd.DataFrame(stack_opportunities).sort_values('stack_score', ascending=False)
        
        logger.info(" ELITE STACK RANKINGS:")
        for i, (idx, stack) in enumerate(stack_df.head(6).iterrows()):
            logger.info(f"  {i+1}. {stack['team']}: {stack['stack_score']:.1f} score "
                       f"(Ceiling: {stack['avg_ceiling']:.1f}, Own: {stack['avg_ownership']:.1f}%, "
                       f"Leverage: {stack['avg_leverage']:.1f}, Players: {stack['player_count']})")
        
        return stack_df

def test_elite_optimizer():
    """Test the elite optimizer with August 13th data"""
    
    try:
        # Load test data
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        logger.info(f"SUCCESS: Loaded test data: {len(df)} players")
        
        # Initialize optimizer
        optimizer = EliteDFSOptimizer()
        
        # Add elite features
        df_elite = optimizer.enhance_with_elite_features(df)
        
        # Analyze stacking opportunities
        stack_analysis = optimizer.identify_elite_stacks(df_elite)
        
        # Show sample elite players
        logger.info(f"\nTARGET: ELITE LEVERAGE TARGETS:")
        top_leverage = df_elite.nlargest(10, 'leverage_score')
        for idx, player in top_leverage.iterrows():
            logger.info(f"  {player['Nickname']} {player['Last Name']} ({player['Team']}) - "
                       f"Leverage: {player['leverage_score']:.1f}, "
                       f"Own: {player['ownership_proj']:.1f}%, "
                       f"Ceiling: {player['ceiling_proj']:.1f}")
        
        logger.info(f"\n LOW OWNERSHIP BOMBS:")
        low_owned = df_elite[df_elite['ownership_proj'] <= 5].nlargest(5, 'ceiling_proj')
        for idx, player in low_owned.iterrows():
            logger.info(f"  {player['Nickname']} {player['Last Name']} ({player['Team']}) - "
                       f"Own: {player['ownership_proj']:.1f}%, "
                       f"Ceiling: {player['ceiling_proj']:.1f}, "
                       f"Salary: ${player['Salary']}")
        
        logger.info(f"\nSUCCESS: ELITE OPTIMIZER TEST COMPLETE")
        logger.info("Ready to integrate into your tournament pipeline!")
        
        return df_elite, stack_analysis
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_elite_optimizer()
