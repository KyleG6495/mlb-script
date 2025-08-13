#!/usr/bin/env python3
"""
TOURNAMENT VOLUME LINEUP GENERATOR
Creates 20+ diverse lineups for maximum tournament coverage
"""

import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime
from itertools import combinations
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TournamentVolumeGenerator:
    def __init__(self):
        self.optimized_players = None
        self.salary_cap = 35000
        self.lineup_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        
    def load_optimized_data(self):
        """Load the optimized projections data"""
        try:
            # Try multiple possible paths for confirmed projections
            possible_paths = [
                '../data/confirmed_optimized_projections.csv',  # From Scripts directory
                '../../data/confirmed_optimized_projections.csv',  # From DAILY_RUNNERS directory
                'data/confirmed_optimized_projections.csv',  # From MLB directory
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    self.optimized_players = pd.read_csv(path)
                    logger.info(f"📥 Loaded {len(self.optimized_players)} optimized confirmed starters from {path}")
                    return True
            
            # If no file found, log error
            logger.error("❌ Could not find confirmed_optimized_projections.csv in any expected location")
            return False
            
        except Exception as e:
            logger.error(f"❌ Could not load optimized data: {e}")
            return False
    
    def generate_tournament_volume(self, num_lineups=20):
        """Generate diverse tournament lineups for high-volume play"""
        logger.info(f"🏆 GENERATING {num_lineups} TOURNAMENT LINEUPS")
        logger.info("🎯 Maximum diversity for tournament volume play")
        logger.info("=" * 60)
        
        if not self.load_optimized_data():
            return None
        
        all_lineups = []
        strategy_mix = [
            'ceiling', 'leverage', 'balanced', 'contrarian', 'stack_heavy',
            'value', 'upside', 'anti_chalk', 'correlation', 'stars_and_scrubs'
        ]
        
        # Generate diverse lineups
        for i in range(num_lineups):
            strategy = strategy_mix[i % len(strategy_mix)]
            
            logger.info(f"🔄 Generating lineup {i+1}/{num_lineups} - {strategy}")
            
            lineup = self._generate_diverse_lineup(strategy, i)
            
            if lineup:
                lineup['strategy'] = strategy
                lineup['lineup_id'] = i + 1
                all_lineups.append(lineup)
                
                logger.info(f"✅ Lineup {i+1}: {lineup['projected_score']:.1f} FPPG (${lineup['total_salary']:,})")
            else:
                logger.warning(f"⚠️ Failed to generate lineup {i+1}")
        
        # Save all lineups
        self._save_tournament_volume(all_lineups)
        
        # Analysis
        self._analyze_tournament_portfolio(all_lineups)
        
        return all_lineups
    
    def _generate_diverse_lineup(self, strategy, lineup_num):
        """Generate a single diverse lineup based on strategy"""
        
        # Strategy-specific parameters
        strategies = {
            'ceiling': {'score_col': 'sim_ceiling', 'randomness': 0.3},
            'leverage': {'score_col': 'leverage', 'randomness': 0.4},
            'balanced': {'score_col': 'sim_mean', 'randomness': 0.2},
            'contrarian': {'score_col': 'leverage', 'randomness': 0.6},
            'stack_heavy': {'score_col': 'tournament_score', 'randomness': 0.3, 'force_stack': True},
            'value': {'score_col': 'value', 'randomness': 0.3},
            'upside': {'score_col': 'sim_upside', 'randomness': 0.4},
            'anti_chalk': {'score_col': 'leverage', 'randomness': 0.7},
            'correlation': {'score_col': 'tournament_score', 'randomness': 0.2, 'force_correlation': True},
            'stars_and_scrubs': {'score_col': 'sim_ceiling', 'randomness': 0.1, 'salary_distribution': 'extreme'}
        }
        
        params = strategies.get(strategy, strategies['balanced'])
        score_col = params['score_col']
        randomness = params['randomness']
        
        # Position pools
        position_pools = {}
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS']:
            position_pools[pos] = self.optimized_players[
                self.optimized_players['Position'] == pos
            ].sort_values(score_col, ascending=False).copy()
        
        position_pools['OF'] = self.optimized_players[
            self.optimized_players['Position'] == 'OF'
        ].sort_values(score_col, ascending=False).copy()
        
        # Try to build lineup
        max_attempts = 5000
        for attempt in range(max_attempts):
            lineup_players = []
            total_salary = 0
            valid_lineup = True
            
            # Add lineup-specific randomness seed
            random.seed(lineup_num * 1000 + attempt)
            np.random.seed(lineup_num * 1000 + attempt)
            
            for pos in self.lineup_positions:
                available_players = position_pools[pos][
                    ~position_pools[pos]['Nickname'].isin([p['player'] for p in lineup_players])
                ].copy()
                
                if len(available_players) == 0:
                    valid_lineup = False
                    break
                
                # Calculate remaining budget
                remaining_positions = self.lineup_positions[len(lineup_players)+1:]
                min_remaining_salary = self._estimate_min_remaining_salary(remaining_positions)
                max_affordable_salary = self.salary_cap - total_salary - min_remaining_salary
                
                affordable_players = available_players[
                    available_players['Salary'] <= max_affordable_salary
                ]
                
                if len(affordable_players) == 0:
                    valid_lineup = False
                    break
                
                # Strategy-specific selection
                selected_player = self._select_diverse_player(
                    affordable_players, score_col, strategy, randomness, lineup_num
                )
                
                lineup_players.append({
                    'position': pos,
                    'player': selected_player['Nickname'],
                    'player_id': selected_player['Id'],
                    'salary': selected_player['Salary'],
                    'projection': selected_player[score_col],
                    'ownership': selected_player.get('projected_ownership', 0.15),
                    'team': selected_player['Team']
                })
                
                total_salary += selected_player['Salary']
            
            if valid_lineup and total_salary <= self.salary_cap:
                # Calculate final lineup score
                lineup_score = sum([p['projection'] for p in lineup_players])
                
                # Add strategy bonuses
                if params.get('force_stack'):
                    lineup_score += self._calculate_stacking_bonus(lineup_players)
                
                return {
                    'players': lineup_players,
                    'total_salary': total_salary,
                    'projected_score': lineup_score,
                    'salary_remaining': self.salary_cap - total_salary
                }
        
        return None
    
    def _select_diverse_player(self, players, score_col, strategy, randomness, lineup_num):
        """Select player with strategy-specific logic and randomness"""
        
        if len(players) == 1:
            return players.iloc[0]
        
        # Determine selection pool size based on strategy
        if strategy in ['anti_chalk', 'contrarian']:
            pool_size = min(len(players), 8)  # Larger pool for more randomness
        elif strategy in ['stars_and_scrubs']:
            pool_size = min(len(players), 3)  # Smaller pool for more stars
        else:
            pool_size = min(len(players), 5)  # Standard pool
        
        top_candidates = players.head(pool_size)
        
        # Add randomness based on strategy
        if randomness > 0.5:  # High randomness strategies
            weights = np.ones(len(top_candidates))  # Equal weights
        else:  # Lower randomness strategies
            weights = np.exp(top_candidates[score_col] - top_candidates[score_col].max())
        
        # Normalize weights
        weights = weights / weights.sum()
        
        # Add lineup-specific bias to create different results
        bias_factor = (lineup_num % len(top_candidates)) / len(top_candidates)
        weights = weights * (1 + bias_factor * randomness)
        weights = weights / weights.sum()
        
        selected_idx = np.random.choice(top_candidates.index, p=weights)
        return players.loc[selected_idx]
    
    def _calculate_stacking_bonus(self, lineup_players):
        """Calculate bonus for team stacking"""
        teams = {}
        for player in lineup_players:
            if player['position'] != 'P':
                team = player['team']
                teams[team] = teams.get(team, 0) + 1
        
        bonus = 0
        for team, count in teams.items():
            if count >= 3:
                bonus += count * 2  # Stack bonus
        
        return bonus
    
    def _estimate_min_remaining_salary(self, remaining_positions):
        """Estimate minimum salary needed for remaining positions"""
        min_salary = 0
        for pos in remaining_positions:
            if pos == 'P':
                min_salary += 4500
            elif pos == 'C':
                min_salary += 2000
            else:
                min_salary += 2200
        return min_salary
    
    def _save_tournament_volume(self, lineups):
        """Save all lineups in FanDuel format"""
        fd_lineups = []
        
        for lineup in lineups:
            fd_lineup = {
                'P': '', 'C': '', '1B': '', '2B': '', '3B': '', 'SS': '', 
                'OF': '', 'OF2': '', 'OF3': '', 'UTIL': '',
                'P Id': '', 'C Id': '', '1B Id': '', '2B Id': '', '3B Id': '', 'SS Id': '', 
                'OF Id': '', 'OF2 Id': '', 'OF3 Id': '', 'UTIL Id': ''
            }
            
            of_count = 0
            
            for player in lineup['players']:
                if player['position'] == 'OF':
                    of_count += 1
                    if of_count == 1:
                        fd_lineup['OF'] = player['player']
                        fd_lineup['OF Id'] = player['player_id']
                    elif of_count == 2:
                        fd_lineup['OF2'] = player['player']
                        fd_lineup['OF2 Id'] = player['player_id']
                    elif of_count == 3:
                        fd_lineup['OF3'] = player['player']
                        fd_lineup['OF3 Id'] = player['player_id']
                else:
                    fd_lineup[player['position']] = player['player']
                    fd_lineup[f"{player['position']} Id"] = player['player_id']
            
            # Add metadata
            fd_lineup['Projected_FPPG'] = round(lineup['projected_score'], 1)
            fd_lineup['Total_Salary'] = lineup['total_salary']
            fd_lineup['Strategy'] = lineup['strategy']
            fd_lineup['Lineup_ID'] = lineup['lineup_id']
            
            fd_lineups.append(fd_lineup)
        
        # Save to CSV with flexible path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Try multiple possible output paths
        possible_output_paths = [
            f'../fd_current_slate/TOURNAMENT_VOLUME_{timestamp}.csv',  # From Scripts
            f'../../fd_current_slate/TOURNAMENT_VOLUME_{timestamp}.csv',  # From DAILY_RUNNERS  
            f'fd_current_slate/TOURNAMENT_VOLUME_{timestamp}.csv',  # From MLB root
        ]
        
        output_file = None
        for path in possible_output_paths:
            output_dir = os.path.dirname(path)
            if os.path.exists(output_dir):
                output_file = path
                break
        
        if output_file is None:
            # Fallback to current directory
            output_file = f'TOURNAMENT_VOLUME_{timestamp}.csv'
            logger.warning(f"⚠️ Using fallback path: {output_file}")
        
        df = pd.DataFrame(fd_lineups)
        df.to_csv(output_file, index=False)
        
        logger.info(f"💾 Saved {len(lineups)} tournament lineups to: {output_file}")
    
    def _analyze_tournament_portfolio(self, lineups):
        """Analyze the diversity and coverage of the lineup portfolio"""
        logger.info("=" * 60)
        logger.info("📊 TOURNAMENT PORTFOLIO ANALYSIS")
        logger.info("=" * 60)
        
        # Projection analysis
        projections = [l['projected_score'] for l in lineups]
        logger.info(f"📈 Projection Range: {min(projections):.1f} - {max(projections):.1f} FPPG")
        logger.info(f"📊 Average Projection: {np.mean(projections):.1f} FPPG")
        logger.info(f"📊 Projection Std Dev: {np.std(projections):.1f} FPPG")
        
        # Salary analysis
        salaries = [l['total_salary'] for l in lineups]
        logger.info(f"💰 Salary Range: ${min(salaries):,} - ${max(salaries):,}")
        logger.info(f"💰 Average Salary: ${np.mean(salaries):,.0f}")
        
        # Player diversity
        all_players = []
        for lineup in lineups:
            all_players.extend([p['player'] for p in lineup['players']])
        
        unique_players = len(set(all_players))
        total_spots = len(lineups) * 9
        diversity_pct = unique_players / total_spots * 100
        
        logger.info(f"👥 Player Diversity: {unique_players} unique players across {len(lineups)} lineups")
        logger.info(f"🎯 Diversity Rate: {diversity_pct:.1f}% (higher = more diverse)")
        
        # Strategy breakdown
        strategies = [l['strategy'] for l in lineups]
        strategy_counts = {}
        for strategy in strategies:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        logger.info("🎭 STRATEGY BREAKDOWN:")
        for strategy, count in strategy_counts.items():
            logger.info(f"   {strategy}: {count} lineups")
        
        logger.info("=" * 60)

def main():
    """Main tournament volume generation function"""
    generator = TournamentVolumeGenerator()
    
    # Generate 20 diverse tournament lineups
    lineups = generator.generate_tournament_volume(20)
    
    if lineups:
        logger.info(f"🏆 Successfully generated {len(lineups)} diverse tournament lineups!")
        logger.info("🎯 Ready for high-volume tournament play!")
    else:
        logger.error("❌ Failed to generate tournament volume")

if __name__ == "__main__":
    main()
