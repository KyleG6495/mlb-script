#!/usr/bin/env python3
"""
DFS Game State Baseball Simulator
==================================

Advanced baseball game simulation that models realistic game flow, 
player interactions, and scoring patterns for DFS projections.

This simulator provides:
- Play-by-play game simulation
- Natural player correlations
- Realistic FPPG distributions
- Context-aware scoring opportunities
"""

import pandas as pd
import numpy as np
import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GameState:
    """Represents current state of a baseball game"""
    inning: int = 1
    half: str = 'top'  # 'top' or 'bottom'
    outs: int = 0
    runners: List[Optional[str]] = field(default_factory=lambda: [None, None, None])  # 1B, 2B, 3B
    score: List[int] = field(default_factory=lambda: [0, 0])  # [away, home]
    current_batter_idx: Dict[str, int] = field(default_factory=lambda: {'away': 0, 'home': 0})
    
    def is_game_over(self) -> bool:
        """Check if game is complete"""
        if self.inning >= 9:
            if self.half == 'bottom' and self.score[1] > self.score[0]:
                return True  # Walk-off
            if self.half == 'top' and self.inning > 9:
                return True  # Extra innings completed
        return False
    
    def get_batting_team(self) -> str:
        """Get current batting team"""
        return 'away' if self.half == 'top' else 'home'
    
    def advance_inning(self):
        """Move to next half inning"""
        if self.half == 'top':
            self.half = 'bottom'
        else:
            self.half = 'top'
            self.inning += 1
        self.outs = 0
        self.runners = [None, None, None]

@dataclass
class PlayerStats:
    """Track individual player statistics during simulation"""
    player_id: str
    name: str
    position: str
    team: str
    
    # Counting stats
    plate_appearances: int = 0
    at_bats: int = 0
    hits: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    runs: int = 0
    rbi: int = 0
    walks: int = 0
    strikeouts: int = 0
    stolen_bases: int = 0
    hit_by_pitch: int = 0
    
    def calculate_fppg(self) -> float:
        """Calculate FanDuel points based on accumulated stats"""
        points = (
            (self.hits - self.doubles - self.triples - self.home_runs) * 3 +  # Singles = 3 pts
            self.doubles * 6 +        # Double = 6 pts (3 + 3 bonus)
            self.triples * 9 +        # Triple = 9 pts (3 + 6 bonus)
            self.home_runs * 12 +     # HR = 12 pts (3 + 9 bonus)
            self.runs * 3.2 +         # Run = 3.2 pts
            self.rbi * 3.5 +          # RBI = 3.5 pts
            self.walks * 2 +          # Walk = 2 pts
            self.stolen_bases * 6 +   # SB = 6 pts
            self.hit_by_pitch * 2     # HBP = 2 pts
        )
        return round(points, 2)

class BaseballSimulator:
    """Main simulation engine for baseball games"""
    
    def __init__(self):
        self.setup_outcome_probabilities()
        
    def setup_outcome_probabilities(self):
        """Initialize realistic baseball outcome probabilities"""
        # League average probabilities (can be customized per player/matchup)
        self.base_probabilities = {
            'strikeout': 0.235,
            'walk': 0.086,
            'hbp': 0.009,
            'single': 0.135,  # Reduced from 0.155
            'double': 0.035,  # Reduced from 0.042
            'triple': 0.003,  # Reduced from 0.005
            'home_run': 0.025, # Reduced from 0.028
            'groundout': 0.285, # Increased to compensate
            'flyout': 0.187   # Adjusted
        }
        
        # Stolen base attempt probabilities
        self.steal_probabilities = {
            'attempt_rate': 0.015,  # Reduced from 0.035 - too many attempts
            'success_rate': 0.75
        }
    
    def get_player_probabilities(self, player_data: dict, pitcher_data: dict, 
                               game_situation: dict) -> dict:
        """
        Adjust base probabilities based on player skills and situation
        
        Args:
            player_data: Hitter's stats and projections
            pitcher_data: Pitcher's stats and projections  
            game_situation: Game context (inning, score, etc.)
        """
        # Start with base probabilities
        probs = self.base_probabilities.copy()
        
        # Adjust based on player's historical rates
        if 'strikeout_rate' in player_data:
            probs['strikeout'] = player_data['strikeout_rate']
        if 'walk_rate' in player_data:
            probs['walk'] = player_data['walk_rate']
        if 'home_run_rate' in player_data:
            probs['home_run'] = player_data['home_run_rate']
        
        # Adjust based on pitcher quality
        if 'pitcher_k_rate' in pitcher_data:
            probs['strikeout'] *= (pitcher_data['pitcher_k_rate'] / 0.235)
        if 'pitcher_bb_rate' in pitcher_data:
            probs['walk'] *= (pitcher_data['pitcher_bb_rate'] / 0.086)
        
        # Game situation adjustments
        if game_situation.get('late_inning_pressure', False):
            probs['strikeout'] *= 1.1  # More pressure = more strikeouts
        
        # Normalize probabilities to sum to 1.0
        total = sum(probs.values())
        probs = {k: v/total for k, v in probs.items()}
        
        return probs
    
    def simulate_plate_appearance(self, batter_data: dict, pitcher_data: dict, 
                                game_state: GameState) -> str:
        """
        Simulate a single plate appearance
        
        Returns: outcome string ('single', 'strikeout', etc.)
        """
        # Get contextual probabilities
        situation = {
            'late_inning_pressure': game_state.inning >= 7,
            'runners_on_base': any(game_state.runners),
            'score_differential': abs(game_state.score[0] - game_state.score[1])
        }
        
        probs = self.get_player_probabilities(batter_data, pitcher_data, situation)
        
        # Random selection based on probabilities
        outcomes = list(probs.keys())
        probabilities = list(probs.values())
        
        return np.random.choice(outcomes, p=probabilities)
    
    def process_outcome(self, outcome: str, batter_stats: PlayerStats, 
                       game_state: GameState) -> List[PlayerStats]:
        """
        Process the outcome of a plate appearance and update game state
        
        Returns: List of players who scored (for RBI/Run credit)
        """
        scored_players = []
        
        # Update batter's plate appearances
        batter_stats.plate_appearances += 1
        
        if outcome in ['single', 'double', 'triple', 'home_run']:
            # Hit outcomes
            batter_stats.at_bats += 1
            batter_stats.hits += 1
            
            if outcome == 'single':
                scored_players = self.advance_runners(game_state, 1)
                game_state.runners[0] = batter_stats.player_id
                
            elif outcome == 'double':
                batter_stats.doubles += 1
                scored_players = self.advance_runners(game_state, 2)
                game_state.runners[1] = batter_stats.player_id
                
            elif outcome == 'triple':
                batter_stats.triples += 1
                scored_players = self.advance_runners(game_state, 3)
                game_state.runners[2] = batter_stats.player_id
                
            elif outcome == 'home_run':
                batter_stats.home_runs += 1
                # All runners score + batter
                for runner in game_state.runners:
                    if runner:
                        scored_players.append(runner)
                scored_players.append(batter_stats.player_id)
                game_state.runners = [None, None, None]
        
        elif outcome == 'walk':
            batter_stats.walks += 1
            scored_players = self.force_advance_runners(game_state)
            game_state.runners[0] = batter_stats.player_id
            
        elif outcome == 'hbp':
            batter_stats.hit_by_pitch += 1
            scored_players = self.force_advance_runners(game_state)
            game_state.runners[0] = batter_stats.player_id
            
        elif outcome == 'strikeout':
            batter_stats.at_bats += 1
            batter_stats.strikeouts += 1
            game_state.outs += 1
            
        elif outcome in ['groundout', 'flyout']:
            batter_stats.at_bats += 1
            game_state.outs += 1
            
            # Chance for RBI on sacrifice fly/groundout with runner on 3rd
            if (outcome == 'flyout' and game_state.runners[2] and 
                game_state.outs < 3):
                scored_players.append(game_state.runners[2])
                game_state.runners[2] = None
        
        return scored_players
    
    def advance_runners(self, game_state: GameState, bases: int) -> List[str]:
        """Advance all runners by specified number of bases"""
        scored_players = []
        
        # Move runners from back to front to avoid overwriting
        new_runners = [None, None, None]
        
        for i in range(2, -1, -1):  # Start from 3rd base (index 2)
            if game_state.runners[i]:
                new_position = i + bases
                if new_position >= 3:
                    # Runner scores
                    scored_players.append(game_state.runners[i])
                else:
                    new_runners[new_position] = game_state.runners[i]
        
        game_state.runners = new_runners
        return scored_players
    
    def force_advance_runners(self, game_state: GameState) -> List[str]:
        """Force advance runners (walk/HBP scenario)"""
        scored_players = []
        
        # Only advance if forced
        if game_state.runners[2] and game_state.runners[1] and game_state.runners[0]:
            # Bases loaded - runner on 3rd scores
            scored_players.append(game_state.runners[2])
            game_state.runners[2] = game_state.runners[1]
            game_state.runners[1] = game_state.runners[0]
            
        elif game_state.runners[1] and game_state.runners[0]:
            # Runners on 1st and 2nd
            game_state.runners[2] = game_state.runners[1]
            game_state.runners[1] = game_state.runners[0]
            
        elif game_state.runners[0]:
            # Runner on 1st only
            game_state.runners[1] = game_state.runners[0]
        
        return scored_players
    
    def attempt_stolen_base(self, game_state: GameState, 
                          runner_stats: PlayerStats) -> bool:
        """Attempt stolen base and return success"""
        if random.random() < self.steal_probabilities['success_rate']:
            runner_stats.stolen_bases += 1
            return True
        else:
            # Caught stealing - runner is out
            game_state.outs += 1
            return False
    
    def simulate_full_game(self, away_lineup: List[dict], home_lineup: List[dict],
                          away_pitcher: dict, home_pitcher: dict) -> Dict[str, PlayerStats]:
        """
        Simulate a complete baseball game
        
        Args:
            away_lineup: List of away team hitter data
            home_lineup: List of home team hitter data  
            away_pitcher: Away team pitcher data
            home_pitcher: Home team pitcher data
            
        Returns:
            Dictionary mapping player_id to PlayerStats
        """
        game_state = GameState()
        
        # Initialize player stats
        all_players = {}
        
        for i, player in enumerate(away_lineup):
            stats = PlayerStats(
                player_id=player['player_id'],
                name=player['name'],
                position=player['position'],
                team='away'
            )
            all_players[player['player_id']] = stats
        
        for i, player in enumerate(home_lineup):
            stats = PlayerStats(
                player_id=player['player_id'],
                name=player['name'], 
                position=player['position'],
                team='home'
            )
            all_players[player['player_id']] = stats
        
        # Main game loop
        while not game_state.is_game_over():
            batting_team = game_state.get_batting_team()
            lineup = away_lineup if batting_team == 'away' else home_lineup
            pitcher = home_pitcher if batting_team == 'away' else away_pitcher
            
            # Get current batter
            batter_idx = game_state.current_batter_idx[batting_team]
            current_batter = lineup[batter_idx % len(lineup)]
            batter_stats = all_players[current_batter['player_id']]
            
            # Simulate plate appearance
            outcome = self.simulate_plate_appearance(
                current_batter, pitcher, game_state
            )
            
            # Process outcome
            scored_players = self.process_outcome(outcome, batter_stats, game_state)
            
            # Update runs and RBIs
            batting_team_idx = 0 if batting_team == 'away' else 1
            for player_id in scored_players:
                all_players[player_id].runs += 1
                game_state.score[batting_team_idx] += 1
                
            # Credit RBIs (don't credit RBI for scoring on your own HR)
            if scored_players and outcome != 'home_run':
                batter_stats.rbi += len(scored_players)
            elif outcome == 'home_run':
                # For HR, credit RBI for all runners that were on base (not including batter)
                runners_rbi = len([p for p in scored_players if p != batter_stats.player_id])
                batter_stats.rbi += runners_rbi + 1  # +1 for the HR itself
            
            # Check for stolen base attempts
            self.check_stolen_base_attempts(game_state, all_players)
            
            # Advance batter in lineup
            game_state.current_batter_idx[batting_team] = (batter_idx + 1) % len(lineup)
            
            # Check for end of inning
            if game_state.outs >= 3:
                game_state.advance_inning()
        
        return all_players
    
    def check_stolen_base_attempts(self, game_state: GameState, 
                                 all_players: Dict[str, PlayerStats]):
        """Check if any runners attempt stolen bases"""
        for i, runner_id in enumerate(game_state.runners):
            if runner_id and i < 2:  # Can't steal home in this simple model
                if random.random() < self.steal_probabilities['attempt_rate']:
                    runner_stats = all_players[runner_id]
                    if self.attempt_stolen_base(game_state, runner_stats):
                        # Successful steal - advance runner
                        game_state.runners[i] = None
                        game_state.runners[i + 1] = runner_id
                    else:
                        # Caught stealing - remove runner
                        game_state.runners[i] = None

class DFSSimulationEngine:
    """High-level DFS simulation engine"""
    
    def __init__(self):
        self.simulator = BaseballSimulator()
    
    def load_slate_data(self, slate_file: str) -> Dict:
        """Load today's DFS slate data"""
        # This would load your actual slate data
        # For now, returning mock structure
        return {
            'games': [],
            'players': {}
        }
    
    def simulate_slate(self, slate_data: Dict, n_simulations: int = 1000) -> pd.DataFrame:
        """
        Run multiple simulations of entire slate
        
        Returns:
            DataFrame with player projections including floor/ceiling
        """
        logger.info(f"Running {n_simulations} slate simulations...")
        
        all_results = []
        
        for sim_num in range(n_simulations):
            if sim_num % 100 == 0:
                logger.info(f"Completed {sim_num}/{n_simulations} simulations")
            
            sim_results = {}
            
            # Simulate each game in the slate
            for game in slate_data['games']:
                game_results = self.simulator.simulate_full_game(
                    game['away_lineup'],
                    game['home_lineup'], 
                    game['away_pitcher'],
                    game['home_pitcher']
                )
                
                # Extract FPPG for each player
                for player_id, stats in game_results.items():
                    sim_results[player_id] = stats.calculate_fppg()
            
            all_results.append(sim_results)
        
        # Analyze simulation results
        return self.analyze_simulation_results(all_results)
    
    def analyze_simulation_results(self, all_results: List[Dict]) -> pd.DataFrame:
        """Convert simulation results to useful projections"""
        
        # Get all unique players
        all_players = set()
        for sim in all_results:
            all_players.update(sim.keys())
        
        projections = []
        
        for player_id in all_players:
            # Extract all FPPG values for this player
            player_fppg = [sim.get(player_id, 0) for sim in all_results]
            
            projection = {
                'player_id': player_id,
                'mean_fppg': np.mean(player_fppg),
                'median_fppg': np.median(player_fppg),
                'floor_fppg': np.percentile(player_fppg, 10),
                'ceiling_fppg': np.percentile(player_fppg, 90),
                'std_fppg': np.std(player_fppg),
                'bust_rate': np.mean(np.array(player_fppg) < 2.0),
                'boom_rate': np.mean(np.array(player_fppg) > 15.0),
                'consistency': 1 / (1 + np.std(player_fppg))  # Higher = more consistent
            }
            
            projections.append(projection)
        
        df = pd.DataFrame(projections)
        
        # Add value metrics
        # (This would incorporate salary data when available)
        
        logger.info(f"Generated projections for {len(df)} players")
        return df
    
    def simulate_player_variance(self, player_data: Dict, n_simulations: int = 500) -> Dict:
        """Simulate individual player variance for enhanced projections"""
        
        # Extract player stats
        hits = player_data.get('hits', 100)
        at_bats = hits / 0.25 if hits > 0 else 400  # Assume .250 BA
        home_runs = player_data.get('home_runs', 15)
        doubles = player_data.get('doubles', 20)
        walks = player_data.get('walks', 40)
        
        # Calculate rates
        hit_rate = min(hits / at_bats, 0.4) if at_bats > 0 else 0.25
        hr_rate = min(home_runs / at_bats, 0.15) if at_bats > 0 else 0.04
        walk_rate = min(walks / at_bats, 0.2) if at_bats > 0 else 0.1
        
        # Run simulations
        fppg_results = []
        for _ in range(n_simulations):
            # Simulate plate appearances (typically 3-5 per game)
            plate_appearances = np.random.poisson(4)
            plate_appearances = max(1, min(plate_appearances, 6))  # Cap between 1-6
            
            game_fppg = 0
            for _ in range(plate_appearances):
                outcome = self._simulate_plate_appearance(hit_rate, hr_rate, walk_rate)
                game_fppg += self._calculate_fppg_for_outcome(outcome)
            
            fppg_results.append(game_fppg)
        
        # Calculate statistics
        fppg_array = np.array(fppg_results)
        
        return {
            'mean_fppg': np.mean(fppg_array),
            'median_fppg': np.median(fppg_array),
            'std_fppg': np.std(fppg_array),
            'floor_fppg': np.percentile(fppg_array, 10),
            'ceiling_fppg': np.percentile(fppg_array, 90),
            'bust_rate': np.mean(fppg_array < 2.0),
            'boom_rate': np.mean(fppg_array > 15.0),
            'consistency': 1 / (1 + np.std(fppg_array))  # Higher is more consistent
        }
    
    def _simulate_plate_appearance(self, hit_rate: float, hr_rate: float, walk_rate: float) -> str:
        """Simulate a single plate appearance outcome"""
        
        rand = np.random.random()
        
        if rand < walk_rate:
            return 'walk'
        elif rand < walk_rate + hr_rate:
            return 'home_run'
        elif rand < walk_rate + hit_rate:
            # Hit but not HR - could be single, double, triple
            hit_type_rand = np.random.random()
            if hit_type_rand < 0.7:
                return 'single'
            elif hit_type_rand < 0.9:
                return 'double'
            else:
                return 'triple'
        else:
            return 'out'
    
    def _calculate_fppg_for_outcome(self, outcome: str) -> float:
        """Calculate FPPG points for a specific outcome"""
        
        # FanDuel scoring
        scoring = {
            'single': 3.0,
            'double': 6.0,
            'triple': 9.0,
            'home_run': 12.0,
            'walk': 3.0,
            'run_scored': 3.2,
            'rbi': 3.5,
            'stolen_base': 6.0,
            'out': 0.0
        }
        
        base_points = scoring.get(outcome, 0.0)
        
        # Add potential bonus points
        if outcome in ['single', 'double', 'triple', 'home_run']:
            # Chance for RBI
            if np.random.random() < 0.3:  # 30% chance of RBI
                base_points += scoring['rbi']
            
            # Chance to score
            if outcome == 'home_run':
                base_points += scoring['run_scored']  # HR always scores
            elif outcome in ['triple', 'double'] and np.random.random() < 0.6:
                base_points += scoring['run_scored']
            elif outcome == 'single' and np.random.random() < 0.2:
                base_points += scoring['run_scored']
        
        # Stolen base chance for runners
        if outcome in ['single', 'double', 'walk'] and np.random.random() < 0.1:
            base_points += scoring['stolen_base']
        
        return base_points

def main():
    """Example usage of the DFS Game Simulator"""
    
    # Initialize simulator
    engine = DFSSimulationEngine()
    
    # Create more realistic mock slate data
    slate_data = {
        'games': [
            {
                'away_lineup': [
                    {'player_id': f'away_{i}', 'name': f'Away Player {i}', 'position': 'OF', 
                     'strikeout_rate': np.random.uniform(0.15, 0.35), 
                     'walk_rate': np.random.uniform(0.05, 0.15), 
                     'home_run_rate': np.random.uniform(0.01, 0.05)}
                    for i in range(1, 10)  # 9 players
                ],
                'home_lineup': [
                    {'player_id': f'home_{i}', 'name': f'Home Player {i}', 'position': 'OF',
                     'strikeout_rate': np.random.uniform(0.15, 0.35),
                     'walk_rate': np.random.uniform(0.05, 0.15), 
                     'home_run_rate': np.random.uniform(0.01, 0.05)}
                    for i in range(1, 10)  # 9 players
                ],
                'away_pitcher': {'pitcher_k_rate': 0.28, 'pitcher_bb_rate': 0.09},
                'home_pitcher': {'pitcher_k_rate': 0.24, 'pitcher_bb_rate': 0.08}
            }
        ]
    }
    
    # Run simulations with fewer iterations for testing
    projections = engine.simulate_slate(slate_data, n_simulations=100)
    
    print("\nDFS Projections:")
    print(projections.to_string())
    
    # Show some sample statistics
    if not projections.empty:
        print(f"\nSummary Statistics:")
        print(f"Average FPPG: {projections['mean_fppg'].mean():.2f}")
        print(f"Highest projection: {projections['mean_fppg'].max():.2f}")
        print(f"Lowest projection: {projections['mean_fppg'].min():.2f}")
        print(f"Players with >10 FPPG: {len(projections[projections['mean_fppg'] > 10])}")
        print(f"Players with >15 FPPG: {len(projections[projections['mean_fppg'] > 15])}")

if __name__ == "__main__":
    main()
