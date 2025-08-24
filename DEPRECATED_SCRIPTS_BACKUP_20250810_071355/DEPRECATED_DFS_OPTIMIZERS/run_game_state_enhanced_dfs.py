#!/usr/bin/env python3
"""
GAME STATE ENHANCED DFS SYSTEM
==============================
Uses your existing SimplifiedDFSOptimizer with Game State Baseball Simulator
for enhanced projections on real FanDuel data.
"""

import pandas as pd
import numpy as np
import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Dict
from dfs_game_simulator import DFSSimulationEngine
from optimize_simplified_dfs_lineups import SimplifiedDFSOptimizer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GameStateEnhancedDFS:
    """Enhanced DFS system using Game State Baseball Simulator with existing optimizer"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.simulator = DFSSimulationEngine()
        self.optimizer = SimplifiedDFSOptimizer()
        
    def enhance_real_projections(self, fd_hitter_path: str = None, fd_pitcher_path: str = None, n_simulations: int = 2000):
        """Enhance real FanDuel projections using Game State simulation with weather & park factors"""
        
        logger.info(f"🚀 Enhancing real FanDuel projections with {n_simulations} simulations")
        
        # Default file paths
        if fd_hitter_path is None:
            fd_hitter_path = self.data_dir / "fd_hitter_features_final.csv"
        if fd_pitcher_path is None:
            fd_pitcher_path = self.data_dir / "fd_pitcher_features_final.csv"
        
        # Load weather and park factors
        weather_park_path = self.data_dir / "merged_weather_park.csv"
        weather_data = {}
        try:
            weather_df = pd.read_csv(weather_park_path)
            logger.info(f"🌤️ Loaded weather & park factors for {len(weather_df)} games")
            # Create team-based lookup for quick access
            for _, row in weather_df.iterrows():
                team = row.get('home_team', '')
                weather_data[team] = {
                    'temperature': row.get('temperature', 75),
                    'wind_speed': row.get('wind_speed', 5),
                    'humidity': row.get('humidity', 50),
                    'park_factor': row.get('park_factor', 100),
                    'hr_factor': row.get('HR', 100),
                    'so_factor': row.get('SO', 100)
                }
        except FileNotFoundError:
            logger.warning("⚠️ Weather/park data not found - using neutral conditions")
            weather_data = {}
        
        # Load hitters
        try:
            hitter_data = pd.read_csv(fd_hitter_path)
            logger.info(f"Loaded {len(hitter_data)} hitters from {os.path.basename(fd_hitter_path)}")
        except FileNotFoundError:
            logger.error(f"Hitter file not found: {fd_hitter_path}")
            return None
        
        # Load pitchers
        try:
            pitcher_data = pd.read_csv(fd_pitcher_path)
            logger.info(f"Loaded {len(pitcher_data)} pitchers from {os.path.basename(fd_pitcher_path)}")
        except FileNotFoundError:
            logger.error(f"Pitcher file not found: {fd_pitcher_path}")
            return None
        
        # Process hitters
        enhanced_hitters = self._enhance_hitters(hitter_data, n_simulations, weather_data)
        
        # Process pitchers  
        enhanced_pitchers = self._enhance_pitchers(pitcher_data, n_simulations, weather_data)
        
        # Combine hitters and pitchers
        enhanced_projections = enhanced_hitters + enhanced_pitchers
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save enhanced projections
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / f"game_state_enhanced_projections_{timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        logger.info(f"💾 Saved enhanced projections to {output_file}")
        logger.info(f"📊 Enhanced {len(enhanced_hitters)} hitters + {len(enhanced_pitchers)} pitchers = {len(enhanced_df)} total players")
        logger.info(f"🎯 Avg hitter FPPG: {enhanced_df[enhanced_df['Position'] != 'P']['FPPG'].mean():.2f}")
        logger.info(f"⚾ Avg pitcher FPPG: {enhanced_df[enhanced_df['Position'] == 'P']['FPPG'].mean():.2f}")
        
        return enhanced_df
    
    def _enhance_hitters(self, hitter_data: pd.DataFrame, n_simulations: int, weather_data: dict) -> list:
        """Enhance hitter projections with Game State simulation"""
        
        enhanced_hitters = []
        
        for idx, player in hitter_data.iterrows():
            # Create player data for simulation
            player_data = {
                'id': f"{player['Team']}_{idx}",
                'name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Position'],
                'team': player['Team'],
                'salary': player['Salary'],
                'hits': player.get('hits', 100),
                'home_runs': player.get('homeRuns', 15),
                'doubles': player.get('doubles', 20),
                'triples': player.get('triples', 2),
                'rbi': player.get('runsBattedIn', 60),
                'runs': player.get('runsScored', 65),
                'walks': player.get('baseOnBalls', 40),
                'strikeouts': player.get('strikeOuts', 120),
                'stolen_bases': player.get('stolenBases', 8)
            }
            
            # Run mini simulation for variance
            player_projections = self.simulator.simulate_player_variance(
                player_data, n_simulations=500
            )
            
            # Enhance base projection with simulation data
            base_fppg = player.get('FPPG', 8.0)
            sim_fppg = player_projections['mean_fppg']
            
            # Apply weather and park factors
            team = player.get('Team', '')
            weather_factor = 1.0
            if team in weather_data:
                w_data = weather_data[team]
                # Temperature factor (hot weather = more offense)
                temp_factor = 1.0 + (w_data['temperature'] - 75) * 0.002
                # Wind factor (wind out = more HRs)
                wind_factor = 1.0 + max(0, w_data['wind_speed'] - 10) * 0.01
                # Park factor
                park_factor = w_data['park_factor'] / 100.0
                weather_factor = temp_factor * wind_factor * park_factor
                
            # Blend base projection with simulation (70% base, 30% simulation) + weather
            enhanced_fppg = (base_fppg * 0.7 + sim_fppg * 0.3) * weather_factor
            
            enhanced_hitters.append({
                'First Name': player['First Name'],
                'Last Name': player['Last Name'],
                'Position': player['Position'],
                'Team': player['Team'],
                'Salary': player['Salary'],
                'FPPG': enhanced_fppg,
                'base_fppg': base_fppg,
                'sim_fppg': sim_fppg,
                'ceiling_fppg': player_projections['ceiling_fppg'],
                'floor_fppg': player_projections['floor_fppg'],
                'variance': player_projections['std_fppg'],
                'boom_rate': player_projections['boom_rate'],
                'bust_rate': player_projections['bust_rate'],
                'player_type': 'hitter'
            })
        
        return enhanced_hitters
    
    def _enhance_pitchers(self, pitcher_data: pd.DataFrame, n_simulations: int, weather_data: dict) -> list:
        """Enhance pitcher projections with Game State simulation"""
        
        enhanced_pitchers = []
        
        for idx, player in pitcher_data.iterrows():
            # Handle team column (pitcher data uses Team_x)
            team = player.get('Team_x', player.get('Team', 'UNK'))
            
            # Create pitcher data for simulation
            pitcher_stats = {
                'id': f"{team}_{idx}",
                'name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Position'],
                'team': team,
                'salary': player['Salary'],
                'strikeouts': player.get('strikeOuts', 5.5),  # Per start average
                'walks': player.get('baseOnBalls', 2.5),
                'hits_allowed': player.get('hits', 5.0),
                'innings_pitched': player.get('outs', 18) / 3.0,  # Convert outs to innings
                'earned_runs': player.get('earnedRuns', 3.0)
            }
            
            # Simulate pitcher variance
            pitcher_projections = self._simulate_pitcher_variance(pitcher_stats, n_simulations=500)
            
            # Enhance base projection 
            base_fppg = player.get('FPPG', 35.0)
            sim_fppg = pitcher_projections['mean_fppg']
            
            # Apply weather and park factors for pitchers
            weather_factor = 1.0
            if team in weather_data:
                w_data = weather_data[team]
                # Temperature factor (hot weather = more offense = lower pitcher scores)
                temp_factor = 1.0 - (w_data['temperature'] - 75) * 0.001
                # Wind factor (wind out = more HRs = lower pitcher scores)
                wind_factor = 1.0 - max(0, w_data['wind_speed'] - 10) * 0.005
                # Park factor (pitcher-friendly parks = higher scores)
                park_factor = (200 - w_data['park_factor']) / 100.0
                weather_factor = temp_factor * wind_factor * park_factor
            
            # Blend projections (80% base, 20% simulation for pitchers - they're more predictable) + weather
            enhanced_fppg = (base_fppg * 0.8 + sim_fppg * 0.2) * weather_factor
            
            enhanced_pitchers.append({
                'First Name': player['First Name'],
                'Last Name': player['Last Name'],
                'Position': player['Position'], 
                'Team': team,  # Use the resolved team
                'Salary': player['Salary'],
                'FPPG': enhanced_fppg,
                'base_fppg': base_fppg,
                'sim_fppg': sim_fppg,
                'ceiling_fppg': pitcher_projections['ceiling_fppg'],
                'floor_fppg': pitcher_projections['floor_fppg'],
                'variance': pitcher_projections['std_fppg'],
                'boom_rate': pitcher_projections['boom_rate'],
                'bust_rate': pitcher_projections['bust_rate'],
                'player_type': 'pitcher'
            })
        
        return enhanced_pitchers
    
    def _simulate_pitcher_variance(self, pitcher_stats: Dict, n_simulations: int = 500) -> Dict:
        """Simulate pitcher variance for enhanced projections"""
        
        # Extract pitcher stats
        k_rate = min(pitcher_stats.get('strikeouts', 5.5) / 27.0, 0.4)  # K per 9 innings
        bb_rate = min(pitcher_stats.get('walks', 2.5) / 27.0, 0.15)     # BB per 9 innings
        hits_per_9 = min(pitcher_stats.get('hits_allowed', 5.0) / 6.0, 2.0)  # Hits per 6 IP
        innings_avg = pitcher_stats.get('innings_pitched', 6.0)
        
        # Run simulations
        fppg_results = []
        for _ in range(n_simulations):
            # Simulate innings pitched (typically 5-7 innings)
            innings = max(3.0, min(9.0, np.random.normal(innings_avg, 1.5)))
            
            # Simulate pitcher outcomes
            outs_pitched = innings * 3
            strikeouts = np.random.poisson(k_rate * outs_pitched)
            walks = np.random.poisson(bb_rate * outs_pitched) 
            hits_allowed = np.random.poisson(hits_per_9 * innings / 6.0)
            
            # Calculate FanDuel pitcher scoring
            pitcher_fppg = self._calculate_pitcher_fppg(
                innings, strikeouts, walks, hits_allowed
            )
            
            fppg_results.append(pitcher_fppg)
        
        # Calculate statistics
        fppg_array = np.array(fppg_results)
        
        return {
            'mean_fppg': np.mean(fppg_array),
            'median_fppg': np.median(fppg_array),
            'std_fppg': np.std(fppg_array),
            'floor_fppg': np.percentile(fppg_array, 10),
            'ceiling_fppg': np.percentile(fppg_array, 90),
            'bust_rate': np.mean(fppg_array < 20.0),  # Under 20 is bust for pitcher
            'boom_rate': np.mean(fppg_array > 50.0),  # Over 50 is boom for pitcher
            'consistency': 1 / (1 + np.std(fppg_array))
        }
    
    def _calculate_pitcher_fppg(self, innings: float, strikeouts: int, walks: int, hits_allowed: int) -> float:
        """Calculate FanDuel pitcher scoring"""
        
        # FanDuel pitcher scoring
        points = 0.0
        
        # Innings pitched: 3 pts per IP
        points += innings * 3.0
        
        # Strikeouts: 3 pts each
        points += strikeouts * 3.0
        
        # Walks: -3 pts each
        points -= walks * 3.0
        
        # Hits allowed: -3 pts each  
        points -= hits_allowed * 3.0
        
        # Earned runs: -9 pts each (estimate based on hits/walks)
        estimated_er = max(0, (hits_allowed + walks - 3) * 0.3)  # Rough ER estimate
        points -= estimated_er * 9.0
        
        # Win bonus: 12 pts (30% chance)
        if np.random.random() < 0.3:
            points += 12.0
        
        # Quality start bonus: 4 pts (if 6+ IP, ≤3 ER)
        if innings >= 6.0 and estimated_er <= 3.0:
            points += 4.0
        
        return max(0.0, points)  # Can't go negative
    
    def run_complete_pipeline(self, fd_hitter_path: str = None, fd_pitcher_path: str = None, n_lineups: int = 15):
        """Run complete enhanced DFS pipeline"""
        
        logger.info("🚀 GAME STATE ENHANCED DFS PIPELINE")
        logger.info("=" * 50)
        
        # Use default FanDuel files if not specified
        if fd_hitter_path is None:
            fd_hitter_path = self.data_dir / "fd_hitter_features_final.csv"
        if fd_pitcher_path is None:
            fd_pitcher_path = self.data_dir / "fd_pitcher_features_final.csv"
        
        # Step 1: Enhance projections for both hitters and pitchers
        enhanced_df = self.enhance_real_projections(
            fd_hitter_path, fd_pitcher_path, n_simulations=2000
        )
        if enhanced_df is None:
            logger.error("Failed to enhance projections")
            return False
        
        # Step 2: Generate optimized lineups
        logger.info(f"🎯 Generating {n_lineups} optimized lineups...")
        lineups = self.optimizer.generate_multiple_lineups(enhanced_df, n_lineups=n_lineups)
        
        if lineups:
            logger.info(f"✅ Generated {len(lineups)} lineups successfully!")
            
            # Analyze results
            self.optimizer.analyze_lineup_distribution(lineups)
            
            # Save lineups in standard format
            self.save_enhanced_lineups(lineups)
            
            return True
        else:
            logger.error("Failed to generate lineups")
            return False
    
    def save_enhanced_lineups(self, lineups):
        """Save lineups in enhanced format"""
        
        all_lineups = []
        for i, lineup_result in enumerate(lineups):
            for j, player in enumerate(lineup_result['lineup']):
                all_lineups.append({
                    'lineup_id': i + 1,
                    'contest_type': lineup_result.get('objective', 'balanced'),
                    'strategy_description': self.get_strategy_description(lineup_result.get('objective', 'balanced')),
                    'slot': j + 1,
                    'name': player['name'],
                    'position': player['position'],
                    'team': player['team'],
                    'salary': player['salary'],
                    'projected_fppg': player['projected_fppg'],
                    'ceiling': player['ceiling'],
                    'floor': player['floor'],
                    'tier': player.get('tier', ''),
                    'salary_efficiency': player.get('salary_efficiency', 0),
                    'lineup_total_salary': lineup_result['total_salary'],
                    'lineup_total_projection': lineup_result['total_fppg'],
                    'lineup_total_ceiling': sum(p['ceiling'] for p in lineup_result['lineup']),
                    'lineup_total_floor': sum(p['floor'] for p in lineup_result['lineup'])
                })
        
        # Save to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / f"game_state_enhanced_lineups_{timestamp}.csv"
        
        df_lineups = pd.DataFrame(all_lineups)
        df_lineups.to_csv(output_file, index=False)
        
        logger.info(f"💾 Saved enhanced lineups to {output_file}")
        
        # Print top lineups
        print(f"\n🏆 TOP 5 ENHANCED LINEUPS:")
        print("=" * 60)
        
        top_lineups = sorted(lineups, key=lambda x: x['total_fppg'], reverse=True)[:5]
        for i, lineup in enumerate(top_lineups, 1):
            print(f"#{i} ({lineup['objective']}): {lineup['total_fppg']:.1f} FPPG, ${lineup['total_salary']:,}")
            for player in lineup['lineup']:
                print(f"  {player['name']:<20} {player['position']:>3} {player['team']:>4} "
                      f"${player['salary']:,} ({player['projected_fppg']:.1f} FPPG)")
            print()
    
    def get_strategy_description(self, objective):
        """Get strategy description for objective"""
        descriptions = {
            'floor': 'High-floor lineups for cash games',
            'balanced': 'Balanced upside for small tournaments', 
            'ceiling': 'High-ceiling lineups for large tournaments'
        }
        return descriptions.get(objective, 'Game State Enhanced lineup')

def main():
    """Main execution function"""
    
    # Initialize enhanced DFS system
    enhanced_dfs = GameStateEnhancedDFS()
    
    # Run complete pipeline
    success = enhanced_dfs.run_complete_pipeline(n_lineups=20)
    
    if success:
        logger.info("✅ Game State Enhanced DFS pipeline completed successfully!")
    else:
        logger.error("❌ Pipeline failed")

if __name__ == "__main__":
    main()
