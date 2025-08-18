#!/usr/bin/env python3
"""
Enhanced DFS Lineup Optimizer
============================

Advanced lineup optimization using Monte Carlo simulation results.
Supports multiple contest types and correlation modeling.
"""

import pandas as pd
import numpy as np
from pulp import *
import itertools
from typing import Dict, List, Tuple
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedLineupOptimizer:
    """Advanced DFS lineup optimizer with simulation integration"""
    
    def __init__(self, projections_file: str = "../data/dfs_projections_for_optimizer.csv"):
        self.projections_file = projections_file
        self.salary_cap = 35000
        self.lineup_size = 9
        self.position_requirements = {
            'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 4
        }
        
    def load_projections(self) -> pd.DataFrame:
        """Load enhanced projections from simulation"""
        
        try:
            df = pd.read_csv(self.projections_file)
            logger.info(f"Loaded projections for {len(df)} players")
            
            # Ensure required columns exist
            required_cols = ['player_id', 'name', 'position', 'salary', 'mean_fppg']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                logger.error(f"Missing required columns: {missing_cols}")
                return pd.DataFrame()
            
            # Clean and prepare data
            df = self.prepare_data(df)
            return df
            
        except Exception as e:
            logger.error(f"Error loading projections: {e}")
            return pd.DataFrame()
    
    def prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare projection data"""
        
        # Remove players with missing critical data
        df = df.dropna(subset=['salary', 'mean_fppg'])
        
        # Standardize position names
        df['primary_position'] = df['position'].apply(self.get_primary_position)
        
        # Remove players without valid positions
        valid_positions = list(self.position_requirements.keys())
        df = df[df['primary_position'].isin(valid_positions)]
        
        # Set default values for optional columns
        df['floor_fppg'] = df.get('floor_fppg', df['mean_fppg'] * 0.6)
        df['ceiling_fppg'] = df.get('ceiling_fppg', df['mean_fppg'] * 1.5)
        df['value_mean'] = df.get('value_mean', df['mean_fppg'] / (df['salary'] / 1000))
        
        # Add utility columns
        df['salary_per_k'] = df['salary'] / 1000
        df['points_per_dollar'] = df['mean_fppg'] / df['salary_per_k']
        
        logger.info(f"Prepared data for {len(df)} players")
        return df
    
    def get_primary_position(self, position_str: str) -> str:
        """Extract primary position from position string"""
        
        if pd.isna(position_str):
            return None
            
        # Handle multi-position eligibility (e.g., "1B/OF")
        positions = str(position_str).split('/')
        
        # Priority order for position assignment
        position_priority = ['C', '1B', '2B', '3B', 'SS', 'OF']
        
        for pos in position_priority:
            if pos in positions:
                return pos
        
        # Default to first position listed
        return positions[0] if positions else None
    
    def optimize_lineup(self, df: pd.DataFrame, contest_type: str = 'cash',
                       objective_weights: Dict = None) -> Dict:
        """
        Optimize lineup for specific contest type
        
        Args:
            df: Player projections dataframe
            contest_type: 'cash', 'tournament', or 'custom'
            objective_weights: Custom weights for multi-objective optimization
        """
        
        if objective_weights is None:
            objective_weights = self.get_default_weights(contest_type)
        
        # Create optimization problem
        prob = LpProblem("Enhanced_DFS_Lineup", LpMaximize)
        
        # Decision variables
        player_vars = {}
        for idx, player in df.iterrows():
            player_vars[idx] = LpVariable(f"player_{idx}", cat='Binary')
        
        # Objective function - multi-component
        objective = 0
        for idx, player in df.iterrows():
            player_value = (
                objective_weights['mean'] * player['mean_fppg'] +
                objective_weights['floor'] * player['floor_fppg'] +
                objective_weights['ceiling'] * player['ceiling_fppg'] +
                objective_weights['value'] * player['value_mean']
            )
            objective += player_value * player_vars[idx]
        
        prob += objective
        
        # Constraints
        self.add_basic_constraints(prob, df, player_vars)
        self.add_position_constraints(prob, df, player_vars)
        
        if contest_type == 'tournament':
            self.add_tournament_constraints(prob, df, player_vars)
        
        # Solve
        solver = PULP_CBC_CMD(msg=False)
        prob.solve(solver)
        
        if prob.status != LpStatusOptimal:
            logger.error(f"Optimization failed with status: {LpStatus[prob.status]}")
            return None
        
        # Extract solution
        lineup = self.extract_lineup(df, player_vars)
        return lineup
    
    def get_default_weights(self, contest_type: str) -> Dict:
        """Get default objective weights for contest type"""
        
        if contest_type == 'cash':
            return {
                'mean': 0.4,
                'floor': 0.4,
                'ceiling': 0.1,
                'value': 0.1
            }
        elif contest_type == 'tournament':
            return {
                'mean': 0.3,
                'floor': 0.1,
                'ceiling': 0.5,
                'value': 0.1
            }
        else:  # balanced
            return {
                'mean': 0.5,
                'floor': 0.2,
                'ceiling': 0.2,
                'value': 0.1
            }
    
    def add_basic_constraints(self, prob: LpProblem, df: pd.DataFrame, 
                            player_vars: Dict):
        """Add basic lineup constraints"""
        
        # Exactly 9 players
        prob += lpSum(player_vars[idx] for idx in df.index) == self.lineup_size
        
        # Salary cap
        prob += lpSum(df.loc[idx, 'salary'] * player_vars[idx] 
                     for idx in df.index) <= self.salary_cap
    
    def add_position_constraints(self, prob: LpProblem, df: pd.DataFrame,
                               player_vars: Dict):
        """Add position requirement constraints"""
        
        for position, required_count in self.position_requirements.items():
            position_players = df[df['primary_position'] == position].index
            
            # Debug: Print available players for each position
            logger.info(f"Position {position}: need {required_count}, have {len(position_players)} players")
            
            if len(position_players) < required_count:
                logger.error(f"Not enough {position} players: need {required_count}, have {len(position_players)}")
                # Relax constraint if not enough players
                if len(position_players) > 0:
                    prob += lpSum(player_vars[idx] for idx in position_players) <= len(position_players)
            else:
                prob += lpSum(player_vars[idx] for idx in position_players) == required_count
    
    def add_tournament_constraints(self, prob: LpProblem, df: pd.DataFrame,
                                 player_vars: Dict):
        """Add tournament-specific constraints"""
        
        # Minimum salary utilization (use most of budget for upside)
        min_salary = self.salary_cap * 0.95
        prob += lpSum(df.loc[idx, 'salary'] * player_vars[idx] 
                     for idx in df.index) >= min_salary
        
        # Limit super-safe plays (encourage some risk)
        if 'bust_rate' in df.columns:
            safe_players = df[df['bust_rate'] < 0.05].index
            prob += lpSum(player_vars[idx] for idx in safe_players) <= 3
    
    def extract_lineup(self, df: pd.DataFrame, player_vars: Dict) -> Dict:
        """Extract optimal lineup from solution"""
        
        selected_players = []
        for idx in df.index:
            if player_vars[idx].value() == 1:
                selected_players.append(idx)
        
        lineup_df = df.loc[selected_players].copy()
        
        lineup_summary = {
            'players': lineup_df,
            'total_salary': lineup_df['salary'].sum(),
            'projected_points': lineup_df['mean_fppg'].sum(),
            'projected_floor': lineup_df['floor_fppg'].sum(),
            'projected_ceiling': lineup_df['ceiling_fppg'].sum(),
            'salary_remaining': self.salary_cap - lineup_df['salary'].sum()
        }
        
        return lineup_summary
    
    def generate_multiple_lineups(self, df: pd.DataFrame, contest_type: str = 'tournament',
                                num_lineups: int = 5, max_overlap: int = 6) -> List[Dict]:
        """
        Generate multiple lineups with limited overlap
        """
        
        lineups = []
        used_players = set()
        
        for i in range(num_lineups):
            logger.info(f"Generating lineup {i+1}/{num_lineups}")
            
            # Create modified dataframe that penalizes overused players
            df_modified = df.copy()
            
            for player_idx in used_players:
                if player_idx in df_modified.index:
                    # Reduce attractiveness of overused players
                    df_modified.loc[player_idx, 'mean_fppg'] *= 0.8
                    df_modified.loc[player_idx, 'value_mean'] *= 0.8
            
            # Optimize lineup
            lineup = self.optimize_lineup(df_modified, contest_type)
            
            if lineup:
                lineups.append(lineup)
                
                # Track used players
                for _, player in lineup['players'].iterrows():
                    used_players.add(player.name)
                
                # Add uniqueness constraint for next iteration
                if len(lineups) > 1:
                    overlap = self.calculate_overlap(lineups[-1], lineups[-2])
                    logger.info(f"Overlap with previous lineup: {overlap} players")
            else:
                logger.warning(f"Failed to generate lineup {i+1}")
        
        return lineups
    
    def calculate_overlap(self, lineup1: Dict, lineup2: Dict) -> int:
        """Calculate number of overlapping players between lineups"""
        
        players1 = set(lineup1['players']['player_id'])
        players2 = set(lineup2['players']['player_id'])
        
        return len(players1.intersection(players2))
    
    def analyze_lineup_correlations(self, lineup: Dict) -> Dict:
        """Analyze correlations within a lineup"""
        
        players_df = lineup['players']
        
        # Team stacking analysis
        team_counts = players_df['team'].value_counts()
        max_team_stack = team_counts.max() if len(team_counts) > 0 else 0
        
        # Game stacking analysis (if game info available)
        game_exposure = {}
        if 'game_id' in players_df.columns:
            game_counts = players_df['game_id'].value_counts()
            game_exposure = game_counts.to_dict()
        
        correlation_analysis = {
            'max_team_stack': max_team_stack,
            'team_distribution': team_counts.to_dict(),
            'game_exposure': game_exposure,
            'position_diversity': len(players_df['primary_position'].unique())
        }
        
        return correlation_analysis
    
    def save_lineups(self, lineups: List[Dict], contest_type: str):
        """Save generated lineups to CSV files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed lineup analysis
        for i, lineup in enumerate(lineups):
            filename = f"../data/lineup_{contest_type}_{i+1}_{timestamp}.csv"
            lineup['players'].to_csv(filename, index=False)
            
            logger.info(f"Saved lineup {i+1} to {filename}")
            
            # Print lineup summary
            self.print_lineup_summary(lineup, i+1)
        
        # Save lineup summary
        summary_data = []
        for i, lineup in enumerate(lineups):
            summary = {
                'lineup_num': i+1,
                'total_salary': lineup['total_salary'],
                'projected_points': lineup['projected_points'],
                'projected_floor': lineup['projected_floor'],
                'projected_ceiling': lineup['projected_ceiling'],
                'correlation_analysis': self.analyze_lineup_correlations(lineup)
            }
            summary_data.append(summary)
        
        summary_df = pd.DataFrame(summary_data)
        summary_file = f"../data/lineup_summary_{contest_type}_{timestamp}.csv"
        summary_df.to_csv(summary_file, index=False)
        logger.info(f"Saved lineup summary to {summary_file}")
    
    def print_lineup_summary(self, lineup: Dict, lineup_num: int):
        """Print detailed lineup summary"""
        
        print(f"\n{'='*60}")
        print(f"LINEUP: LINEUP #{lineup_num} SUMMARY")
        print(f"{'='*60}")
        
        players_df = lineup['players']
        
        print(f"MONEY: Total Salary: ${lineup['total_salary']:,} / ${self.salary_cap:,}")
        print(f"DATA: Projected Points: {lineup['projected_points']:.1f}")
        print(f"  Floor: {lineup['projected_floor']:.1f}")
        print(f"START: Ceiling: {lineup['projected_ceiling']:.1f}")
        print(f" Remaining: ${lineup['salary_remaining']:,}")
        
        print(f"\nOWNERSHIP: LINEUP:")
        display_cols = ['name', 'primary_position', 'team', 'salary', 'mean_fppg']
        if 'value_mean' in players_df.columns:
            display_cols.append('value_mean')
        
        print(players_df[display_cols].to_string(index=False))
        
        # Correlation analysis
        corr_analysis = self.analyze_lineup_correlations(lineup)
        print(f"\n CORRELATION ANALYSIS:")
        print(f"   Max team stack: {corr_analysis['max_team_stack']} players")
        print(f"   Position diversity: {corr_analysis['position_diversity']}/6 positions")

def main():
    """Main execution function"""
    
    # Initialize optimizer
    optimizer = EnhancedLineupOptimizer()
    
    # Load projections
    df = optimizer.load_projections()
    
    if df.empty:
        logger.error("Failed to load projections")
        return
    
    print("\nTARGET: GENERATING ENHANCED DFS LINEUPS")
    print("="*50)
    
    # Generate cash game lineups
    print("\nMONEY: CASH GAME LINEUPS:")
    cash_lineups = optimizer.generate_multiple_lineups(
        df, contest_type='cash', num_lineups=3
    )
    optimizer.save_lineups(cash_lineups, 'cash')
    
    # Generate tournament lineups  
    print("\nLINEUP: TOURNAMENT LINEUPS:")
    tournament_lineups = optimizer.generate_multiple_lineups(
        df, contest_type='tournament', num_lineups=5
    )
    optimizer.save_lineups(tournament_lineups, 'tournament')
    
    logger.info("SUCCESS: Enhanced lineup optimization completed!")

if __name__ == "__main__":
    main()
