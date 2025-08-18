#!/usr/bin/env python3
"""
ADVANCED LINEUP CONSTRUCTOR FOR CONFIRMED STARTERS
Uses optimized projections, correlations, ownership for elite lineup construction
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from itertools import combinations
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedLineupConstructor:
    def __init__(self):
        self.optimized_players = None
        self.correlations = None
        self.salary_cap = 35000
        self.lineup_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        
    def load_optimized_data(self):
        """Load the optimized projections data"""
        try:
            self.optimized_players = pd.read_csv('../data/confirmed_optimized_projections.csv')
            logger.info(f" Loaded {len(self.optimized_players)} optimized confirmed starters")
            return True
        except Exception as e:
            logger.error(f"ERROR: Could not load optimized data: {e}")
            return False
    
    def construct_tournament_lineup(self, strategy='balanced'):
        """Construct optimal tournament lineup using advanced metrics"""
        logger.info(f"LINEUP: CONSTRUCTING TOURNAMENT LINEUP - {strategy.upper()} STRATEGY")
        logger.info("=" * 60)
        
        if not self.load_optimized_data():
            return None
        
        # Select scoring metric based on strategy
        if strategy == 'ceiling':
            score_col = 'sim_ceiling'
            logger.info("START: Using CEILING strategy (max upside)")
        elif strategy == 'leverage':
            score_col = 'leverage' 
            logger.info(" Using LEVERAGE strategy (low ownership + upside)")
        elif strategy == 'tournament':
            score_col = 'tournament_score'
            logger.info("TARGET: Using TOURNAMENT strategy (balanced upside)")
        else:
            score_col = 'sim_mean'
            logger.info("DATA: Using BALANCED strategy (mean projections)")
        
        lineup = self._optimize_lineup(score_col, strategy)
        
        if lineup:
            self._display_lineup_analysis(lineup, strategy)
            return lineup
        else:
            logger.error("ERROR: Could not construct valid lineup")
            return None
    
    def construct_cash_lineup(self):
        """Construct optimal cash game lineup (high floor)"""
        logger.info("MONEY: CONSTRUCTING CASH GAME LINEUP")
        logger.info("=" * 60)
        
        if not self.load_optimized_data():
            return None
        
        lineup = self._optimize_lineup('cash_score', 'cash')
        
        if lineup:
            self._display_lineup_analysis(lineup, 'cash')
            return lineup
        else:
            logger.error("ERROR: Could not construct valid cash lineup")
            return None
    
    def _optimize_lineup(self, score_column, strategy):
        """Core lineup optimization algorithm"""
        
        best_lineup = None
        best_score = 0
        iterations = 0
        max_iterations = 50000
        
        # Position pools
        position_pools = {}
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS']:
            position_pools[pos] = self.optimized_players[
                self.optimized_players['Position'] == pos
            ].sort_values(score_column, ascending=False)
        
        # OF pool (includes OF players)
        position_pools['OF'] = self.optimized_players[
            self.optimized_players['Position'] == 'OF'
        ].sort_values(score_column, ascending=False)
        
        logger.info(f"SWAP: Starting optimization with {max_iterations:,} iterations...")
        
        while iterations < max_iterations:
            lineup_players = []
            total_salary = 0
            
            # Build lineup position by position
            valid_lineup = True
            
            for pos in self.lineup_positions:
                available_players = position_pools[pos][
                    ~position_pools[pos]['Nickname'].isin([p['player'] for p in lineup_players])
                ]
                
                if len(available_players) == 0:
                    valid_lineup = False
                    break
                
                # Smart selection based on remaining salary and positions
                remaining_positions = self.lineup_positions[len(lineup_players)+1:]
                min_remaining_salary = self._estimate_min_remaining_salary(remaining_positions)
                
                max_affordable_salary = self.salary_cap - total_salary - min_remaining_salary
                
                affordable_players = available_players[
                    available_players['Salary'] <= max_affordable_salary
                ]
                
                if len(affordable_players) == 0:
                    valid_lineup = False
                    break
                
                # Selection strategy
                if strategy == 'cash':
                    # For cash: prioritize consistency and floor
                    selected_player = self._select_cash_player(affordable_players, score_column)
                else:
                    # For tournaments: mix of projections and contrarian value
                    selected_player = self._select_tournament_player(affordable_players, score_column, strategy)
                
                lineup_players.append({
                    'position': pos,
                    'player': selected_player['Nickname'],
                    'salary': selected_player['Salary'],
                    'projection': selected_player[score_column],
                    'ownership': selected_player.get('projected_ownership', 0.15)
                })
                
                total_salary += selected_player['Salary']
            
            if not valid_lineup or total_salary > self.salary_cap:
                iterations += 1
                continue
            
            # Calculate lineup score
            lineup_score = sum([p['projection'] for p in lineup_players])
            
            # Add correlation bonuses for tournament play
            if strategy != 'cash':
                correlation_bonus = self._calculate_correlation_bonus(lineup_players)
                lineup_score += correlation_bonus
            
            # Check if this is the best lineup
            if lineup_score > best_score:
                best_score = lineup_score
                best_lineup = {
                    'players': lineup_players,
                    'total_salary': total_salary,
                    'projected_score': lineup_score,
                    'salary_remaining': self.salary_cap - total_salary
                }
                
                logger.info(f"TIP: New best {strategy} lineup: {lineup_score:.2f} points (${total_salary:,})")
            
            iterations += 1
            
            # Progress updates
            if iterations % 10000 == 0:
                logger.info(f" Iteration {iterations:,}/50,000 - Best: {best_score:.2f}")
        
        return best_lineup
    
    def _select_cash_player(self, players, score_col):
        """Select player for cash games (prioritize floor and consistency)"""
        # Weight by floor and consistency more heavily
        top_candidates = players.head(min(5, len(players)))
        
        # Prefer higher floors and consistency
        if len(top_candidates) > 1:
            # Add some randomness but favor better floors
            weights = top_candidates['sim_floor'] * top_candidates['consistency']
            weights = weights / weights.sum()
            selected_idx = np.random.choice(top_candidates.index, p=weights)
            return players.loc[selected_idx]
        else:
            return top_candidates.iloc[0]
    
    def _select_tournament_player(self, players, score_col, strategy):
        """Select player for tournaments (balance projection and ownership)"""
        top_candidates = players.head(min(8, len(players)))
        
        if strategy == 'leverage':
            # Strongly favor low ownership
            contrarian_candidates = top_candidates[
                top_candidates['ownership_tier'].isin(['Contrarian', 'Deep Contrarian'])
            ]
            if len(contrarian_candidates) > 0:
                top_candidates = contrarian_candidates.head(3)
        
        # Some randomness for lineup diversity
        if len(top_candidates) > 1:
            # Weight by score but add randomness
            weights = np.exp(top_candidates[score_col] - top_candidates[score_col].max())
            weights = weights / weights.sum()
            selected_idx = np.random.choice(top_candidates.index, p=weights)
            return players.loc[selected_idx]
        else:
            return top_candidates.iloc[0]
    
    def _estimate_min_remaining_salary(self, remaining_positions):
        """Estimate minimum salary needed for remaining positions"""
        min_salary = 0
        
        for pos in remaining_positions:
            if pos in ['P']:
                min_salary += 4500  # Minimum pitcher
            elif pos in ['C']:
                min_salary += 2000  # Minimum catcher
            else:
                min_salary += 2200  # Minimum hitter
        
        return min_salary
    
    def _calculate_correlation_bonus(self, lineup_players):
        """Calculate correlation bonus for stacking"""
        bonus = 0
        
        # Team stacking bonus
        teams = {}
        for player in lineup_players:
            if player['position'] != 'P':  # Don't count pitchers in stacks
                player_data = self.optimized_players[
                    self.optimized_players['Nickname'] == player['player']
                ]
                if len(player_data) > 0:
                    team = player_data.iloc[0]['Team']
                    teams[team] = teams.get(team, 0) + 1
        
        # Bonus for team stacks
        for team, count in teams.items():
            if count >= 3:
                bonus += count * 0.5  # Stacking bonus
        
        return bonus
    
    def _display_lineup_analysis(self, lineup, strategy):
        """Display detailed lineup analysis"""
        logger.info("=" * 70)
        logger.info(f"LINEUP: {strategy.upper()} LINEUP ANALYSIS")
        logger.info("=" * 70)
        
        # Basic lineup info
        logger.info(f"MONEY: Total Salary: ${lineup['total_salary']:,} / ${self.salary_cap:,}")
        logger.info(f" Remaining: ${lineup['salary_remaining']:,}")
        logger.info(f"DATA: Projected Score: {lineup['projected_score']:.2f} FPPG")
        logger.info("")
        
        # Player breakdown
        logger.info("OWNERSHIP: LINEUP BREAKDOWN:")
        total_ownership = 0
        
        for player in lineup['players']:
            player_data = self.optimized_players[
                self.optimized_players['Nickname'] == player['player']
            ].iloc[0]
            
            ownership_pct = player['ownership'] * 100
            total_ownership += ownership_pct
            
            logger.info(f"   {player['position']:>2} | {player['player']:<20} | "
                       f"${player['salary']:>5,} | {player['projection']:>5.1f} | "
                       f"{ownership_pct:>4.1f}% | {player_data.get('ownership_tier', 'Unknown')}")
        
        logger.info("")
        logger.info(f"PROGRESS: Average Ownership: {total_ownership/9:.1f}%")
        
        # Team breakdown
        teams = {}
        for player in lineup['players']:
            if player['position'] != 'P':
                player_data = self.optimized_players[
                    self.optimized_players['Nickname'] == player['player']
                ]
                if len(player_data) > 0:
                    team = player_data.iloc[0]['Team']
                    teams[team] = teams.get(team, 0) + 1
        
        logger.info(" TEAM BREAKDOWN:")
        for team, count in teams.items():
            logger.info(f"   {team}: {count} players")
        
        logger.info("=" * 70)
    
    def generate_multiple_lineups(self, num_lineups=5, strategies=['balanced', 'ceiling', 'leverage']):
        """Generate multiple diverse lineups"""
        logger.info(f"TARGET: GENERATING {num_lineups} DIVERSE LINEUPS")
        logger.info("=" * 60)
        
        all_lineups = []
        
        for i in range(num_lineups):
            strategy = strategies[i % len(strategies)]
            
            logger.info(f"\nSWAP: Generating lineup {i+1}/{num_lineups} - {strategy}")
            lineup = self.construct_tournament_lineup(strategy)
            
            if lineup:
                lineup['strategy'] = strategy
                lineup['lineup_id'] = i + 1
                all_lineups.append(lineup)
        
        # Save all lineups
        self._save_lineups_to_csv(all_lineups)
        
        return all_lineups
    
    def _save_lineups_to_csv(self, lineups):
        """Save lineups in FanDuel format"""
        fd_lineups = []
        
        for lineup in lineups:
            fd_lineup = {
                'P': '', 'C': '', '1B': '', '2B': '', '3B': '', 'SS': '', 
                'OF': '', 'OF2': '', 'OF3': '', 'UTIL': ''
            }
            
            of_count = 0
            util_filled = False
            
            for player in lineup['players']:
                if player['position'] == 'OF':
                    of_count += 1
                    if of_count == 1:
                        fd_lineup['OF'] = player['player']
                    elif of_count == 2:
                        fd_lineup['OF2'] = player['player']
                    elif of_count == 3:
                        fd_lineup['OF3'] = player['player']
                elif not util_filled and player['position'] in ['1B', '2B', '3B', 'SS', 'OF']:
                    # Use as UTIL if we haven't filled it yet
                    if fd_lineup[player['position']] == '':
                        fd_lineup[player['position']] = player['player']
                    else:
                        fd_lineup['UTIL'] = player['player']
                        util_filled = True
                else:
                    fd_lineup[player['position']] = player['player']
            
            # Add metadata
            fd_lineup['Projected_FPPG'] = round(lineup['projected_score'], 1)
            fd_lineup['Total_Salary'] = lineup['total_salary']
            fd_lineup['Strategy'] = lineup['strategy']
            
            fd_lineups.append(fd_lineup)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'../fd_current_slate/OPTIMIZED_LINEUPS_{timestamp}.csv'
        
        df = pd.DataFrame(fd_lineups)
        df.to_csv(output_file, index=False)
        
        logger.info(f" Saved {len(lineups)} lineups to: {output_file}")

def main():
    """Main lineup construction function"""
    constructor = AdvancedLineupConstructor()
    
    # Generate multiple tournament lineups
    lineups = constructor.generate_multiple_lineups(5)
    
    if lineups:
        logger.info(f"LINEUP: Successfully generated {len(lineups)} optimized lineups!")
    else:
        logger.error("ERROR: Failed to generate lineups")

if __name__ == "__main__":
    main()
