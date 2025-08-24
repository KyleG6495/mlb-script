#!/usr/bin/env python3
"""
DFS Simulation Integration
=========================

Integrates the Game State Baseball Simulator with your existing DFS pipeline.
This script loads your actual player data, runs simulations, and outputs
enhanced projections for lineup optimization.
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import logging
from typing import Dict, List

# Add the scripts directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dfs_game_simulator import DFSSimulationEngine, BaseballSimulator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DFSDataIntegrator:
    """Integrates simulation with existing DFS data pipeline"""
    
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self.simulation_engine = DFSSimulationEngine()
        
    def load_todays_slate(self) -> Dict:
        """Load today's FanDuel slate and transform for simulation"""
        
        try:
            # Load FanDuel slate
            slate_file = os.path.join(self.data_dir, "fd_slate_today.csv")
            if not os.path.exists(slate_file):
                logger.error(f"Slate file not found: {slate_file}")
                return None
                
            fd_slate = pd.read_csv(slate_file)
            logger.info(f"Loaded {len(fd_slate)} players from FanDuel slate")
            
            # Load hitter features
            hitter_features_file = os.path.join(self.data_dir, "projected_fd_hitter_scores.csv")
            if os.path.exists(hitter_features_file):
                hitter_features = pd.read_csv(hitter_features_file)
                logger.info(f"Loaded hitter features for {len(hitter_features)} players")
            else:
                logger.warning("Hitter features file not found, using slate data only")
                hitter_features = pd.DataFrame()
            
            # Load pitcher data
            pitcher_file = os.path.join(self.data_dir, "probable_pitchers_today.csv")
            if os.path.exists(pitcher_file):
                pitchers = pd.read_csv(pitcher_file)
                logger.info(f"Loaded {len(pitchers)} probable pitchers")
            else:
                logger.warning("Pitcher file not found, using default pitcher stats")
                pitchers = pd.DataFrame()
            
            # Transform data for simulation
            slate_data = self.transform_slate_data(fd_slate, hitter_features, pitchers)
            return slate_data
            
        except Exception as e:
            logger.error(f"Error loading slate data: {e}")
            return None
    
    def transform_slate_data(self, fd_slate: pd.DataFrame, 
                           hitter_features: pd.DataFrame, 
                           pitchers: pd.DataFrame) -> Dict:
        """Transform loaded data into simulation format"""
        
        slate_data = {
            'games': [],
            'players': {}
        }
        
        # Group players by game (assumes fd_slate has 'Game' column)
        if 'Game' not in fd_slate.columns:
            # Create mock games from team matchups
            unique_teams = fd_slate['Team'].unique()
            games = self.create_games_from_teams(unique_teams)
        else:
            games = fd_slate['Game'].unique()
        
        for game in games:
            game_data = self.process_game_data(game, fd_slate, hitter_features, pitchers)
            if game_data:
                slate_data['games'].append(game_data)
        
        # Store player reference data
        for _, player in fd_slate.iterrows():
            slate_data['players'][str(player['Id'])] = {
                'name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Position'],
                'team': player['Team'],
                'salary': player['Salary'],
                'fppg': player.get('FPPG', 0)
            }
        
        return slate_data
    
    def process_game_data(self, game: str, fd_slate: pd.DataFrame,
                         hitter_features: pd.DataFrame, 
                         pitchers: pd.DataFrame) -> Dict:
        """Process data for a single game"""
        
        # Extract teams from game (format: "TEAM1@TEAM2")
        if '@' in str(game):
            away_team, home_team = str(game).split('@')
        else:
            # Fallback: use first two unique teams
            teams = fd_slate['Team'].unique()[:2]
            away_team, home_team = teams[0], teams[1] if len(teams) > 1 else teams[0]
        
        # Get players for each team
        away_players = fd_slate[fd_slate['Team'] == away_team]
        home_players = fd_slate[fd_slate['Team'] == home_team]
        
        if len(away_players) == 0 or len(home_players) == 0:
            logger.warning(f"Insufficient players for game {game}")
            return None
        
        # Build lineups
        away_lineup = self.build_lineup(away_players, hitter_features)
        home_lineup = self.build_lineup(home_players, hitter_features)
        
        # Get pitcher data
        away_pitcher = self.get_pitcher_data(home_team, pitchers)  # Away team faces home pitcher
        home_pitcher = self.get_pitcher_data(away_team, pitchers)  # Home team faces away pitcher
        
        return {
            'game_id': game,
            'away_team': away_team,
            'home_team': home_team,
            'away_lineup': away_lineup,
            'home_lineup': home_lineup,
            'away_pitcher': away_pitcher,
            'home_pitcher': home_pitcher
        }
    
    def build_lineup(self, team_players: pd.DataFrame, 
                    hitter_features: pd.DataFrame) -> List[Dict]:
        """Build batting lineup for a team"""
        
        lineup = []
        
        for _, player in team_players.iterrows():
            player_data = {
                'player_id': str(player['Id']),
                'name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Position'],
                'team': player['Team'],
                'salary': player['Salary']
            }
            
            # Add advanced stats if available
            if not hitter_features.empty:
                # Try to match player by name or ID
                player_features = self.match_player_features(player, hitter_features)
                if player_features is not None:
                    player_data.update(player_features)
            
            # Set default rates if not found
            player_data.setdefault('strikeout_rate', 0.23)
            player_data.setdefault('walk_rate', 0.085)
            player_data.setdefault('home_run_rate', 0.025)
            player_data.setdefault('hit_rate', 0.250)
            
            lineup.append(player_data)
        
        return lineup
    
    def match_player_features(self, player: pd.Series, 
                            hitter_features: pd.DataFrame) -> Dict:
        """Match player with feature data"""
        
        player_name = f"{player['First Name']} {player['Last Name']}".lower()
        
        # Try exact name match first
        name_matches = hitter_features[
            hitter_features['name'].str.lower() == player_name
        ]
        
        if not name_matches.empty:
            features = name_matches.iloc[0]
            return {
                'strikeout_rate': features.get('strikeout_rate', 0.23),
                'walk_rate': features.get('walk_rate', 0.085),
                'home_run_rate': features.get('home_run_rate', 0.025),
                'hit_rate': features.get('hit_rate', 0.250),
                'projected_fppg': features.get('projected_fppg', 0)
            }
        
        return None
    
    def get_pitcher_data(self, team: str, pitchers: pd.DataFrame) -> Dict:
        """Get pitcher data for team"""
        
        default_pitcher = {
            'team': team,
            'pitcher_k_rate': 0.24,
            'pitcher_bb_rate': 0.085,
            'pitcher_hr_rate': 0.12,
            'era': 4.20
        }
        
        if pitchers.empty:
            return default_pitcher
        
        # Find pitcher for this team
        team_pitcher = pitchers[pitchers['Team'] == team]
        
        if not team_pitcher.empty:
            pitcher = team_pitcher.iloc[0]
            return {
                'team': team,
                'name': pitcher.get('Name', 'Unknown'),
                'pitcher_k_rate': pitcher.get('K_rate', 0.24),
                'pitcher_bb_rate': pitcher.get('BB_rate', 0.085),
                'pitcher_hr_rate': pitcher.get('HR_rate', 0.12),
                'era': pitcher.get('ERA', 4.20)
            }
        
        return default_pitcher
    
    def create_games_from_teams(self, teams: np.ndarray) -> List[str]:
        """Create mock games from available teams"""
        games = []
        for i in range(0, len(teams) - 1, 2):
            if i + 1 < len(teams):
                games.append(f"{teams[i]}@{teams[i+1]}")
        return games
    
    def run_enhanced_projections(self, n_simulations: int = 1000) -> pd.DataFrame:
        """Run full simulation pipeline and generate enhanced projections"""
        
        logger.info("Starting enhanced DFS projection pipeline...")
        
        # Load today's slate
        slate_data = self.load_todays_slate()
        if not slate_data:
            logger.error("Failed to load slate data")
            return pd.DataFrame()
        
        # Run simulations
        logger.info(f"Running {n_simulations} game simulations...")
        projections = self.simulation_engine.simulate_slate(slate_data, n_simulations)
        
        # Enhance projections with salary data
        enhanced_projections = self.enhance_projections(projections, slate_data)
        
        # Save results
        self.save_projections(enhanced_projections)
        
        return enhanced_projections
    
    def enhance_projections(self, projections: pd.DataFrame, 
                          slate_data: Dict) -> pd.DataFrame:
        """Add salary and value calculations to projections"""
        
        # Add player metadata
        player_info = []
        for _, proj in projections.iterrows():
            player_id = proj['player_id']
            if player_id in slate_data['players']:
                info = slate_data['players'][player_id].copy()
                info.update(proj.to_dict())
                player_info.append(info)
            else:
                # Player not found, use projection data only
                player_info.append(proj.to_dict())
        
        enhanced_df = pd.DataFrame(player_info)
        
        # Calculate value metrics
        if 'salary' in enhanced_df.columns:
            enhanced_df['value_mean'] = enhanced_df['mean_fppg'] / (enhanced_df['salary'] / 1000)
            enhanced_df['value_ceiling'] = enhanced_df['ceiling_fppg'] / (enhanced_df['salary'] / 1000)
            enhanced_df['value_floor'] = enhanced_df['floor_fppg'] / (enhanced_df['salary'] / 1000)
        
        # Add tournament vs cash game recommendations
        enhanced_df['tournament_score'] = (
            0.4 * enhanced_df['ceiling_fppg'] + 
            0.3 * enhanced_df['mean_fppg'] + 
            0.3 * enhanced_df['boom_rate']
        )
        
        enhanced_df['cash_score'] = (
            0.5 * enhanced_df['floor_fppg'] + 
            0.3 * enhanced_df['consistency'] + 
            0.2 * enhanced_df['mean_fppg']
        )
        
        # Sort by value
        if 'value_mean' in enhanced_df.columns:
            enhanced_df = enhanced_df.sort_values('value_mean', ascending=False)
        
        return enhanced_df
    
    def save_projections(self, projections: pd.DataFrame):
        """Save enhanced projections to files"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full projections
        output_file = os.path.join(self.data_dir, f"enhanced_dfs_projections_{timestamp}.csv")
        projections.to_csv(output_file, index=False)
        logger.info(f"Saved enhanced projections to {output_file}")
        
        # Save simplified version for lineup optimizer (in format expected by SimplifiedDFSOptimizer)
        simple_projections = projections.copy()
        
        # Format columns for SimplifiedDFSOptimizer compatibility
        if 'name' in simple_projections.columns:
            name_parts = simple_projections['name'].str.split(' ', n=1, expand=True)
            simple_projections['First Name'] = name_parts[0] if len(name_parts.columns) > 0 else 'Player'
            simple_projections['Last Name'] = name_parts[1] if len(name_parts.columns) > 1 else 'Unknown'
        else:
            simple_projections['First Name'] = 'Player'
            simple_projections['Last Name'] = 'Unknown'
        
        # Rename columns to match optimizer expectations
        column_mapping = {
            'position': 'Position',
            'team': 'Team', 
            'salary': 'Salary',
            'mean_fppg': 'FPPG'
        }
        simple_projections = simple_projections.rename(columns=column_mapping)
        
        # Select only the columns needed by SimplifiedDFSOptimizer
        optimizer_cols = ['First Name', 'Last Name', 'Position', 'Team', 'Salary', 'FPPG']
        for col in optimizer_cols:
            if col not in simple_projections.columns:
                if col == 'Position':
                    simple_projections[col] = 'OF'
                elif col == 'Team':
                    simple_projections[col] = 'UNK'
                elif col == 'Salary':
                    simple_projections[col] = 3000
                elif col == 'FPPG':
                    simple_projections[col] = 8.0
                else:
                    simple_projections[col] = 'Unknown'
        
        simple_projections = simple_projections[optimizer_cols]
        
        simple_file = os.path.join(self.data_dir, "dfs_projections_for_optimizer.csv")
        simple_projections.to_csv(simple_file, index=False)
        logger.info(f"Saved optimizer-ready projections to {simple_file}")
        logger.info(f"Formatted {len(simple_projections)} players for SimplifiedDFSOptimizer")
        
        # Print top recommendations
        self.print_recommendations(projections)
    
    def print_recommendations(self, projections: pd.DataFrame):
        """Print top DFS recommendations"""
        
        print("\n" + "="*60)
        print("📊 ENHANCED DFS PROJECTIONS SUMMARY")
        print("="*60)
        
        if 'value_mean' in projections.columns:
            print("\n🏆 TOP VALUE PLAYS:")
            top_value = projections.head(10)[['name', 'position', 'salary', 'mean_fppg', 'value_mean']]
            print(top_value.to_string(index=False))
        
        print("\n🚀 TOURNAMENT UPSIDE PLAYS:")
        top_upside = projections.nlargest(10, 'ceiling_fppg')[['name', 'position', 'ceiling_fppg', 'boom_rate']]
        print(top_upside.to_string(index=False))
        
        print("\n🛡️ SAFE CASH GAME PLAYS:")
        top_safe = projections.nlargest(10, 'floor_fppg')[['name', 'position', 'floor_fppg', 'bust_rate']]
        print(top_safe.to_string(index=False))

def main():
    """Main execution function"""
    
    # Initialize integrator
    integrator = DFSDataIntegrator()
    
    # Run enhanced projections
    projections = integrator.run_enhanced_projections(n_simulations=500)
    
    if not projections.empty:
        logger.info("✅ Enhanced DFS projections completed successfully!")
    else:
        logger.error("❌ Failed to generate projections")

if __name__ == "__main__":
    main()
