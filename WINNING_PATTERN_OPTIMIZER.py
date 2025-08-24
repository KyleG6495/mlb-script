#!/usr/bin/env python3
"""
WINNING_PATTERN_OPTIMIZER - Advanced DFS optimization incorporating August 13th winners
Combines proven filtering + game stacking + contrarian strategy + salary optimization
"""

import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import logging
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WinningPatternOptimizer:
    def __init__(self):
        self.salary_cap = 35000
        self.lineup_positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
    def load_data(self):
        """Load enhanced projections and slate data"""
        try:
            # Load enhanced projections
            import glob
            projection_files = glob.glob("../data/enhanced_projections_*.csv")
            if projection_files:
                latest_file = max(projection_files)
                self.df = pd.read_csv(latest_file)
                logger.info(f"SUCCESS: Loaded enhanced projections: {latest_file.split('/')[-1]}")
            else:
                # Fallback to slate
                self.df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
                logger.info("SUCCESS: Loaded slate data (no enhanced projections found)")
                
            return True
        except Exception as e:
            logger.error(f"ERROR: Error loading data: {e}")
            return False
    
    def apply_proven_filtering(self):
        """Apply the proven filtering that we perfected"""
        logger.info("TARGET: APPLYING PROVEN FILTERING SYSTEM")
        original_size = len(self.df)
        
        # Filter injured players
        injury_indicators = ['IL', 'DTD', 'O']
        if 'Injury Indicator' in self.df.columns:
            self.df = self.df[~self.df['Injury Indicator'].isin(injury_indicators)]
            logger.info(f"ERROR: Removed injured players: {original_size - len(self.df)}")
        
        # Filter non-probable pitchers
        if 'Probable Pitcher' in self.df.columns:
            pitchers = self.df[self.df['Position'] == 'P']
            non_probable = len(pitchers[pitchers['Probable Pitcher'] != 'Yes'])
            self.df = self.df[
                (self.df['Position'] != 'P') | 
                (self.df['Probable Pitcher'] == 'Yes')
            ]
            logger.info(f"ERROR: Removed non-probable pitchers: {non_probable}")
        
        # Filter bench players
        if 'Batting Order' in self.df.columns:
            bench_players = len(self.df[
                (self.df['Position'] != 'P') & 
                (self.df['Batting Order'] <= 0)
            ])
            self.df = self.df[
                (self.df['Position'] == 'P') | 
                (self.df['Batting Order'] > 0)
            ]
            logger.info(f"ERROR: Removed bench players: {bench_players}")
        
        filtered_size = len(self.df)
        logger.info(f"TARGET: Final filtered slate: {filtered_size} players ({((original_size - filtered_size) / original_size * 100):.1f}% removed)")
    
    def add_winning_patterns(self):
        """Add adjustments based on August 13th winning patterns"""
        logger.info("LINEUP: APPLYING AUGUST 13TH WINNING PATTERNS")
        
        # Create tournament projection column
        self.df['tournament_proj'] = self.df['FPPG'].copy()
        
        # 1. Game stacking boost (identify high-scoring games)
        games = self.df['Game'].value_counts()
        for game in games.index[:3]:  # Top 3 games by player count
            game_players = self.df[self.df['Game'] == game]
            avg_proj = game_players['FPPG'].mean()
            
            if avg_proj > self.df['FPPG'].mean():  # Above average game
                mask = self.df['Game'] == game
                self.df.loc[mask, 'tournament_proj'] *= 1.15  # 15% boost
                logger.info(f" Boosted {game} players (avg {avg_proj:.1f} FPPG)")
        
        # 2. Contrarian value boost (low salary, decent projection)
        contrarian_mask = (self.df['Salary'] <= 3000) & (self.df['FPPG'] >= 10)
        self.df.loc[contrarian_mask, 'tournament_proj'] *= 1.25  # 25% boost
        contrarian_count = contrarian_mask.sum()
        logger.info(f" Boosted {contrarian_count} contrarian gems ($3K, 10 FPPG)")
        
        # 3. Mid-tier pitcher boost (salary savings strategy)
        mid_pitcher_mask = (
            (self.df['Position'] == 'P') & 
            (self.df['Salary'] >= 7000) & 
            (self.df['Salary'] <= 10000)
        )
        self.df.loc[mid_pitcher_mask, 'tournament_proj'] *= 1.1  # 10% boost
        mid_pitcher_count = mid_pitcher_mask.sum()
        logger.info(f"BASEBALL: Boosted {mid_pitcher_count} mid-tier pitchers ($7K-$10K)")
        
        # 4. Team stacking correlation
        for team in self.df['Team'].unique():
            team_players = self.df[self.df['Team'] == team]
            if len(team_players) >= 4:  # Stackable teams
                team_avg = team_players['FPPG'].mean()
                if team_avg > self.df['FPPG'].median():
                    mask = self.df['Team'] == team
                    self.df.loc[mask, 'tournament_proj'] *= 1.08  # 8% correlation boost
    
    def optimize_lineup(self, strategy="tournament_balanced"):
        """Optimize a single lineup with winning patterns"""
        max_attempts = 6000
        best_score = 0
        best_lineup = None
        
        # Create position pools
        position_pools = {
            'P': self.df[self.df['Position'] == 'P'].copy(),
            'C/1B': self.df[self.df['Roster Position'].str.contains('C', na=False)].copy(),
            '2B': self.df[self.df['Position'] == '2B'].copy(),
            '3B': self.df[self.df['Position'] == '3B'].copy(), 
            'SS': self.df[self.df['Position'] == 'SS'].copy(),
            'OF': self.df[self.df['Roster Position'].str.contains('OF', na=False)].copy(),
            'UTIL': self.df[self.df['Position'] != 'P'].copy()
        }
        
        for attempt in range(max_attempts):
            lineup = {}
            total_salary = 0
            total_score = 0
            used_players = set()
            
            # Strategy-specific selection
            if strategy == "game_stack":
                # Try to get 3-4 players from same game
                top_games = self.df.groupby('Game')['tournament_proj'].mean().nlargest(2).index
                target_game = random.choice(top_games)
                target_count = random.randint(3, 4)
            else:
                target_game = None
                target_count = 0
            
            game_players_selected = 0
            
            # Fill positions
            valid_lineup = True
            for pos in self.lineup_positions:
                if pos in ['OF']:
                    continue  # Handle OF separately
                    
                pool = position_pools[pos.split('/')[0] if '/' in pos else pos]
                available = pool[~pool.index.isin(used_players)]
                
                if len(available) == 0:
                    valid_lineup = False
                    break
                
                # Game stacking logic
                if (target_game and game_players_selected < target_count and 
                    pos != 'P' and len(available[available['Game'] == target_game]) > 0):
                    game_available = available[available['Game'] == target_game]
                    if len(game_available) > 0:
                        weights = game_available['tournament_proj'] / game_available['tournament_proj'].sum()
                        selected = game_available.sample(1, weights=weights).iloc[0]
                        game_players_selected += 1
                    else:
                        weights = available['tournament_proj'] / available['tournament_proj'].sum()
                        selected = available.sample(1, weights=weights).iloc[0]
                else:
                    # Regular selection
                    weights = available['tournament_proj'] / available['tournament_proj'].sum()
                    selected = available.sample(1, weights=weights).iloc[0]
                
                lineup[pos] = {
                    'name': f"{selected['Nickname']} {selected['Last Name']}",
                    'salary': selected['Salary'],
                    'projection': selected['tournament_proj'],
                    'team': selected['Team'],
                    'id': selected.name
                }
                
                total_salary += selected['Salary']
                total_score += selected['tournament_proj']
                used_players.add(selected.name)
            
            # Handle OF positions (need 3)
            if valid_lineup:
                of_pool = position_pools['OF'][~position_pools['OF'].index.isin(used_players)]
                if len(of_pool) >= 3:
                    # Select 3 OF
                    for i in range(3):
                        if len(of_pool) == 0:
                            valid_lineup = False
                            break
                            
                        weights = of_pool['tournament_proj'] / of_pool['tournament_proj'].sum()
                        selected = of_pool.sample(1, weights=weights).iloc[0]
                        
                        lineup[f'OF{i+1}'] = {
                            'name': f"{selected['Nickname']} {selected['Last Name']}",
                            'salary': selected['Salary'],
                            'projection': selected['tournament_proj'],
                            'team': selected['Team'],
                            'id': selected.name
                        }
                        
                        total_salary += selected['Salary']
                        total_score += selected['tournament_proj']
                        used_players.add(selected.name)
                        of_pool = of_pool[of_pool.index != selected.name]
            
            # Check constraints
            if not valid_lineup or total_salary > self.salary_cap:
                continue
                
            # Team stacking bonus
            teams = [p['team'] for p in lineup.values()]
            team_counts = pd.Series(teams).value_counts()
            max_stack = team_counts.max()
            if max_stack >= 3:
                total_score *= (1 + (max_stack - 2) * 0.05)  # Bonus for stacking
            
            if total_score > best_score:
                best_score = total_score
                best_lineup = lineup.copy()
                best_lineup['total_salary'] = total_salary
                best_lineup['projected_score'] = total_score
            
            if attempt % 1000 == 0 and attempt > 0:
                logger.info(f"    {attempt} attempts, best: {best_score:.1f}")
        
        return best_lineup, best_score
    
    def create_multiple_lineups(self):
        """Create multiple lineups with different strategies"""
        strategies = [
            ("tournament_balanced", "Balanced tournament approach"),
            ("game_stack", "Game stacking for correlation"),
            ("contrarian_heavy", "Heavy contrarian value"),
            ("salary_savings", "Mid-tier pitcher + elite hitters"),
            ("max_upside", "Maximum ceiling plays")
        ]
        
        lineups = []
        
        for strategy, description in strategies:
            logger.info(f"TARGET: Creating {strategy} lineup...")
            
            # Adjust projections for strategy
            if strategy == "contrarian_heavy":
                mask = self.df['Salary'] <= 3500
                self.df.loc[mask, 'tournament_proj'] *= 1.2
            elif strategy == "salary_savings":
                mask = (self.df['Position'] == 'P') & (self.df['Salary'] <= 9000)
                self.df.loc[mask, 'tournament_proj'] *= 1.25
            
            lineup, score = self.optimize_lineup(strategy)
            
            if lineup:
                lineup['strategy'] = strategy
                lineup['description'] = description
                lineups.append(lineup)
                logger.info(f"SUCCESS: {strategy}: {score:.1f} pts, ${lineup['total_salary']:,}")
        
        return lineups
    
    def save_lineups(self, lineups):
        """Save lineups in FanDuel format"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # FanDuel submission format
        submission_rows = []
        
        for lineup in lineups:
            row = {}
            
            # Map positions
            row['P'] = lineup['P']['name']
            row['C/1B'] = lineup['C/1B']['name'] 
            row['2B'] = lineup['2B']['name']
            row['3B'] = lineup['3B']['name']
            row['SS'] = lineup['SS']['name']
            row['OF'] = lineup['OF1']['name']
            row['OF '] = lineup['OF2']['name']  # Second OF
            row['OF  '] = lineup['OF3']['name']  # Third OF
            row['UTIL'] = lineup['UTIL']['name']
            
            submission_rows.append(row)
        
        submission_df = pd.DataFrame(submission_rows)
        submission_file = f"../data/WINNING_PATTERN_SUBMISSION_{timestamp}.csv"
        submission_df.to_csv(submission_file, index=False)
        
        # Detailed analysis
        analysis_file = f"../data/WINNING_PATTERN_ANALYSIS_{timestamp}.txt"
        with open(analysis_file, 'w') as f:
            f.write("LINEUP: WINNING PATTERN LINEUP ANALYSIS\n")
            f.write("=" * 60 + "\n\n")
            
            for i, lineup in enumerate(lineups):
                f.write(f"LINEUP {i+1}: {lineup['strategy'].upper()}\n")
                f.write(f"Description: {lineup['description']}\n")
                f.write(f"Projected Score: {lineup['projected_score']:.1f} points\n")
                f.write(f"Total Salary: ${lineup['total_salary']:,}\n")
                f.write(f"Remaining: ${35000 - lineup['total_salary']:,}\n\n")
                
                for pos in self.lineup_positions:
                    if pos.startswith('OF'):
                        pos_key = f'OF{pos[-1]}' if pos != 'OF' else 'OF1'
                    else:
                        pos_key = pos
                    
                    if pos_key in lineup:
                        player = lineup[pos_key]
                        f.write(f"  {pos}: {player['name']} (${player['salary']}) - {player['projection']:.1f} pts\n")
                
                f.write("\n" + "-" * 50 + "\n\n")
        
        logger.info(f" Submission file: {submission_file}")
        logger.info(f"DATA: Analysis file: {analysis_file}")
        
        return submission_file

def main():
    """Main execution"""
    logger.info("START: WINNING PATTERN OPTIMIZER - AUGUST 13TH LEARNINGS")
    logger.info("=" * 70)
    logger.info("Incorporating proven strategies from tournament winners:")
    logger.info("  SUCCESS: Game stacking from blowout games")
    logger.info("  SUCCESS: Contrarian value plays (<$3K gems)")
    logger.info("  SUCCESS: Mid-tier pitcher salary savings")
    logger.info("  SUCCESS: Team correlation modeling")
    logger.info("  SUCCESS: Proven filtering (no bench/injured players)")
    logger.info("=" * 70)
    
    optimizer = WinningPatternOptimizer()
    
    # Load data
    if not optimizer.load_data():
        return
    
    # Apply filtering
    optimizer.apply_proven_filtering()
    
    # Add winning patterns
    optimizer.add_winning_patterns()
    
    # Create lineups
    lineups = optimizer.create_multiple_lineups()
    
    if lineups:
        submission_file = optimizer.save_lineups(lineups)
        
        logger.info("LINEUP: WINNING PATTERN OPTIMIZATION COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"DATA: Created {len(lineups)} elite lineups")
        logger.info(f"TARGET: Target: 250+ points using proven patterns")
        logger.info(f" Ready for tournament dominance!")
    else:
        logger.error("ERROR: No lineups created")

if __name__ == "__main__":
    main()
