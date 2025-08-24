#!/usr/bin/env python3
"""
CONTRARIAN LINEUP OPTIMIZER
============================
Generate lineups using contrarian stack insights to target 230+ scores
"""

import pandas as pd
import numpy as np
import logging
import itertools
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContrarianLineupOptimizer:
    def __init__(self):
        self.players_data = None
        self.ownership_data = None
        self.contrarian_lineups = []
        self.salary_cap = 50000
        
    def load_data(self):
        """Load all necessary data"""
        try:
            # Load enhanced projections
            proj_file = "../data/enhanced_projections_20250815_133709.csv"
            if os.path.exists(proj_file):
                self.players_data = pd.read_csv(proj_file)
                logger.info(f"SUCCESS: Loaded {len(self.players_data)} players")
            
            # Load ownership data
            own_file = "../data/advanced_ownership_projections_20250815_175656.csv"
            if os.path.exists(own_file):
                self.ownership_data = pd.read_csv(own_file)
                
                # Merge ownership into players data
                for idx, player in self.players_data.iterrows():
                    player_name = player.get('Nickname', '')
                    ownership_match = self.ownership_data[
                        self.ownership_data['player_name'].str.contains(player_name.split()[-1], case=False, na=False)
                    ]
                    
                    if not ownership_match.empty:
                        ownership = ownership_match['ownership'].iloc[0]
                        self.players_data.at[idx, 'ownership'] = ownership * 100 if ownership < 1 else ownership
                    else:
                        self.players_data.at[idx, 'ownership'] = 5.0  # Default
                
                logger.info(f"SUCCESS: Merged ownership data")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def identify_contrarian_game_stacks(self):
        """Find contrarian opportunities based on LAA@OAK winning model"""
        contrarian_opportunities = []
        
        # Group players by game
        games = self.players_data['Game'].unique()
        
        for game in games:
            if '@' not in game:
                continue
                
            away_team, home_team = game.split('@')
            game_players = self.players_data[self.players_data['Game'] == game]
            
            # Skip pitchers for stacking
            hitters = game_players[game_players['Position'] != 'P']
            
            if len(hitters) < 6:  # Need enough hitters
                continue
            
            # Calculate team stats
            away_players = hitters[hitters['Team'] == away_team]
            home_players = hitters[hitters['Team'] == home_team]
            
            if len(away_players) < 3 or len(home_players) < 3:
                continue
            
            away_avg_ownership = away_players['ownership'].mean()
            home_avg_ownership = home_players['ownership'].mean()
            away_avg_projection = away_players['enhanced_fppg'].mean()
            home_avg_projection = home_players['enhanced_fppg'].mean()
            
            # Find ownership imbalances (contrarian opportunities)
            ownership_diff = abs(away_avg_ownership - home_avg_ownership)
            
            if ownership_diff > 3.0:  # Significant ownership gap
                # Identify the contrarian team (lower owned)
                if away_avg_ownership < home_avg_ownership:
                    contrarian_team = away_team
                    contrarian_players = away_players
                    contrarian_ownership = away_avg_ownership
                    popular_ownership = home_avg_ownership
                else:
                    contrarian_team = home_team
                    contrarian_players = home_players
                    contrarian_ownership = home_avg_ownership
                    popular_ownership = away_avg_ownership
                
                # Calculate leverage score
                leverage = (popular_ownership - contrarian_ownership) * contrarian_players['enhanced_fppg'].mean()
                
                contrarian_opportunities.append({
                    'game': game,
                    'team': contrarian_team,
                    'players': contrarian_players,
                    'avg_ownership': contrarian_ownership,
                    'ownership_edge': popular_ownership - contrarian_ownership,
                    'leverage_score': leverage,
                    'avg_projection': contrarian_players['enhanced_fppg'].mean()
                })
        
        # Sort by leverage score
        contrarian_opportunities.sort(key=lambda x: x['leverage_score'], reverse=True)
        
        logger.info(f"🎯 FOUND {len(contrarian_opportunities)} CONTRARIAN GAME OPPORTUNITIES:")
        for i, opp in enumerate(contrarian_opportunities[:5], 1):
            logger.info(f"{i}. {opp['game']} | {opp['team']} Stack | {opp['avg_ownership']:.1f}% own | Edge: {opp['ownership_edge']:.1f}% | Leverage: {opp['leverage_score']:.1f}")
        
        return contrarian_opportunities
    
    def build_contrarian_stacks(self, opportunities):
        """Build 3-4 player stacks from contrarian opportunities"""
        contrarian_stacks = []
        
        for opp in opportunities[:5]:  # Top 5 opportunities
            players = opp['players'].copy()
            
            # Sort by value (projection / salary) and ownership combination
            players['value_score'] = (players['enhanced_fppg'] / players['Salary'] * 1000) * (10 - players['ownership'])
            players = players.sort_values('value_score', ascending=False)
            
            # Build different stack sizes (3 and 4 players)
            for stack_size in [3, 4]:
                if len(players) >= stack_size:
                    # Try different combinations
                    for combo in itertools.combinations(players.head(6).iterrows(), stack_size):
                        stack_players = [player[1] for player in combo]
                        
                        total_salary = sum(p['Salary'] for p in stack_players)
                        total_projection = sum(p['enhanced_fppg'] for p in stack_players)
                        avg_ownership = np.mean([p['ownership'] for p in stack_players])
                        
                        # Check if it's a viable stack
                        if total_salary < 20000 and avg_ownership < 8.0:  # Reasonable constraints
                            contrarian_stacks.append({
                                'game': opp['game'],
                                'team': opp['team'],
                                'players': stack_players,
                                'size': stack_size,
                                'total_salary': total_salary,
                                'total_projection': total_projection,
                                'avg_ownership': avg_ownership,
                                'leverage_score': opp['ownership_edge'] * total_projection,
                                'value_score': total_projection / total_salary * 1000
                            })
        
        # Sort by leverage score and return top stacks
        contrarian_stacks.sort(key=lambda x: x['leverage_score'], reverse=True)
        return contrarian_stacks[:10]
    
    def build_complete_lineups(self, contrarian_stacks):
        """Build complete 9-player lineups around contrarian stacks"""
        complete_lineups = []
        
        # Get elite pitchers for lineup building
        pitchers = self.players_data[self.players_data['Position'] == 'P'].copy()
        elite_pitchers = pitchers.nlargest(10, 'enhanced_fppg')
        
        for stack in contrarian_stacks[:5]:  # Top 5 contrarian stacks
            # Try to build lineups around each stack
            stack_players = stack['players']
            remaining_salary = self.salary_cap - stack['total_salary']
            
            # Fill remaining positions
            used_positions = [p['Position'] for p in stack_players]
            needed_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            
            # Remove positions already filled by stack
            for pos in used_positions:
                if pos in needed_positions:
                    needed_positions.remove(pos)
            
            # Try different pitcher options
            for pitcher in elite_pitchers.head(3).iterrows():
                pitcher_data = pitcher[1]
                pitcher_salary = pitcher_data['Salary']
                
                if pitcher_salary > remaining_salary:
                    continue
                
                lineup_players = stack_players + [pitcher_data]
                lineup_salary = stack['total_salary'] + pitcher_salary
                lineup_projection = stack['total_projection'] + pitcher_data['enhanced_fppg']
                
                # Fill remaining positions with value plays
                remaining_positions = [pos for pos in needed_positions if pos != 'P']
                remaining_budget = remaining_salary - pitcher_salary
                
                if self.fill_remaining_positions(lineup_players, remaining_positions, remaining_budget):
                    # Calculate final lineup stats
                    total_salary = sum(p['Salary'] for p in lineup_players)
                    total_projection = sum(p['enhanced_fppg'] for p in lineup_players)
                    avg_ownership = np.mean([p.get('ownership', 5.0) for p in lineup_players])
                    
                    if total_salary <= self.salary_cap:
                        complete_lineups.append({
                            'players': lineup_players,
                            'total_salary': total_salary,
                            'total_projection': total_projection,
                            'avg_ownership': avg_ownership,
                            'contrarian_stack': f"{stack['team']} ({stack['size']} players)",
                            'leverage_score': stack['leverage_score'],
                            'lineup_id': f"CONTRARIAN_{len(complete_lineups)+1}"
                        })
        
        return complete_lineups
    
    def fill_remaining_positions(self, current_players, needed_positions, budget):
        """Fill remaining positions with best value plays"""
        try:
            # This is a simplified filler - in practice you'd use optimization
            # For now, just add reasonable players to demonstrate concept
            
            # Get available players for each position
            for pos in needed_positions[:4]:  # Limit to avoid complexity
                pos_players = self.players_data[
                    (self.players_data['Position'] == pos) & 
                    (self.players_data['Salary'] <= budget/len(needed_positions))
                ].nlargest(1, 'enhanced_fppg')
                
                if not pos_players.empty:
                    player = pos_players.iloc[0]
                    current_players.append(player)
                    budget -= player['Salary']
            
            return len(current_players) >= 8  # At least 8 players for demonstration
            
        except Exception as e:
            return False
    
    def generate_contrarian_lineups(self):
        """Generate complete contrarian-focused lineups"""
        logger.info("🏆 GENERATING CONTRARIAN LINEUPS BASED ON WINNING ANALYSIS")
        logger.info("=" * 60)
        
        if not self.load_data():
            return []
        
        # Find contrarian opportunities
        opportunities = self.identify_contrarian_game_stacks()
        
        # Build contrarian stacks
        contrarian_stacks = self.build_contrarian_stacks(opportunities)
        
        logger.info(f"\n🎯 TOP CONTRARIAN STACKS:")
        for i, stack in enumerate(contrarian_stacks[:5], 1):
            logger.info(f"{i}. {stack['team']} {stack['size']}-Stack | ${stack['total_salary']:,} | {stack['total_projection']:.1f} pts | {stack['avg_ownership']:.1f}% own")
            for player in stack['players']:
                logger.info(f"   • {player['Nickname']} ({player['Position']}) - ${player['Salary']} | {player['enhanced_fppg']:.1f} pts | {player.get('ownership', 5):.1f}%")
        
        # Build complete lineups
        complete_lineups = self.build_complete_lineups(contrarian_stacks)
        
        logger.info(f"\n✅ GENERATED {len(complete_lineups)} CONTRARIAN LINEUPS")
        
        return complete_lineups
    
    def save_contrarian_lineups(self, lineups):
        """Save contrarian lineups to CSV"""
        if not lineups:
            return
        
        # Convert to DataFrame format
        lineup_data = []
        for lineup in lineups:
            players = lineup['players']
            
            # Create lineup row (simplified - you'd need proper position mapping)
            row = {
                'Lineup_ID': lineup['lineup_id'],
                'Total_Salary': lineup['total_salary'],
                'Projected_Points': lineup['total_projection'],
                'Avg_Ownership': lineup['avg_ownership'],
                'Contrarian_Stack': lineup['contrarian_stack'],
                'Leverage_Score': lineup['leverage_score']
            }
            
            # Add players (simplified mapping)
            for i, player in enumerate(players[:9]):
                row[f'Player_{i+1}'] = player['Nickname']
                row[f'Position_{i+1}'] = player['Position']
                row[f'Salary_{i+1}'] = player['Salary']
                row[f'Projection_{i+1}'] = player['enhanced_fppg']
                row[f'Ownership_{i+1}'] = player.get('ownership', 5.0)
            
            lineup_data.append(row)
        
        # Save to CSV
        df = pd.DataFrame(lineup_data)
        filename = f"../data/contrarian_lineups_20250815_backtest.csv"
        df.to_csv(filename, index=False)
        logger.info(f"💾 SAVED: Contrarian lineups to {filename}")
        
        return filename

if __name__ == "__main__":
    optimizer = ContrarianLineupOptimizer()
    lineups = optimizer.generate_contrarian_lineups()
    
    if lineups:
        optimizer.save_contrarian_lineups(lineups)
        logger.info(f"🎯 ANALYSIS COMPLETE: Generated {len(lineups)} contrarian lineups for backtest")
