#!/usr/bin/env python3
"""
CONTRARIAN GAME STACK FINDER
============================
Identifies ownership arbitrage opportunities within high-scoring games
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContrarianStackFinder:
    def __init__(self):
        self.games_data = []
        self.ownership_data = None
        self.projections_data = None
        self.contrarian_stacks = []
        
    def load_data(self):
        """Load ownership and projection data"""
        try:
            # Load ownership projections
            ownership_files = [
                "../data/advanced_ownership_projections_20250815_175656.csv",
                "../data/advanced_ownership_projections_20250815_133716.csv"
            ]
            
            for file in ownership_files:
                if os.path.exists(file):
                    self.ownership_data = pd.read_csv(file)
                    logger.info(f"SUCCESS: Loaded ownership data from {file}")
                    break
            
            # Load projections
            proj_files = [
                "../data/enhanced_projections_20250815_133709.csv",
                "../fd_current_slate/fd_slate_today.csv"
            ]
            
            for file in proj_files:
                if os.path.exists(file):
                    self.projections_data = pd.read_csv(file)
                    logger.info(f"SUCCESS: Loaded projections from {file}")
                    break
                    
            return self.ownership_data is not None and self.projections_data is not None
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def identify_game_environments(self):
        """Identify all game environments and their characteristics"""
        if self.projections_data is None:
            return
        
        # Extract unique games
        games = {}
        
        for _, player in self.projections_data.iterrows():
            game = player.get('Game', player.get('game', ''))
            team = player.get('Team', player.get('team', ''))
            
            if game and '@' in game:
                if game not in games:
                    games[game] = {
                        'game': game,
                        'away_team': game.split('@')[0],
                        'home_team': game.split('@')[1],
                        'teams': [],
                        'total_projection': 0,
                        'avg_ownership': 0,
                        'player_count': 0
                    }
                
                games[game]['teams'].append(team)
                
                # Add projection data
                proj = player.get('FPPG', player.get('projection', player.get('enhanced_fppg', 0)))
                if pd.notna(proj):
                    games[game]['total_projection'] += float(proj)
                    games[game]['player_count'] += 1
        
        # Calculate averages and add ownership data
        for game_key, game_data in games.items():
            if game_data['player_count'] > 0:
                game_data['avg_projection'] = game_data['total_projection'] / game_data['player_count']
                
                # Calculate team-level ownership
                away_team = game_data['away_team']
                home_team = game_data['home_team']
                
                game_data['away_ownership'] = self.get_team_ownership(away_team)
                game_data['home_ownership'] = self.get_team_ownership(home_team)
                game_data['ownership_imbalance'] = abs(game_data['away_ownership'] - game_data['home_ownership'])
        
        self.games_data = list(games.values())
        logger.info(f"IDENTIFIED: {len(self.games_data)} game environments")
        
    def get_team_ownership(self, team):
        """Get average ownership for a team"""
        if self.ownership_data is None:
            return 5.0  # Default
            
        team_players = self.ownership_data[
            self.ownership_data['team'].str.contains(team, case=False, na=False)
        ]
        
        if not team_players.empty:
            ownership_col = 'ownership'
            if ownership_col in team_players.columns:
                avg_own = team_players[ownership_col].mean()
                return avg_own * 100 if avg_own < 1 else avg_own
        
        return 5.0  # Default
    
    def find_contrarian_opportunities(self):
        """Find games with ownership arbitrage opportunities"""
        contrarian_games = []
        
        for game in self.games_data:
            # Criteria for contrarian opportunity:
            # 1. Decent total projection (game environment)
            # 2. Significant ownership imbalance between teams
            # 3. At least one team under 5% average ownership
            
            if (game['avg_projection'] > 8.0 and  # Decent game environment
                game['ownership_imbalance'] > 3.0 and  # Ownership imbalance
                min(game['away_ownership'], game['home_ownership']) < 5.0):  # Low-owned team
                
                # Identify the contrarian team (lower owned)
                if game['away_ownership'] < game['home_ownership']:
                    contrarian_team = game['away_team']
                    contrarian_ownership = game['away_ownership']
                    popular_team = game['home_team']
                    popular_ownership = game['home_ownership']
                else:
                    contrarian_team = game['home_team']
                    contrarian_ownership = game['home_ownership']
                    popular_team = game['away_team']
                    popular_ownership = game['away_ownership']
                
                contrarian_games.append({
                    'game': game['game'],
                    'contrarian_team': contrarian_team,
                    'contrarian_ownership': contrarian_ownership,
                    'popular_team': popular_team,
                    'popular_ownership': popular_ownership,
                    'avg_projection': game['avg_projection'],
                    'ownership_edge': popular_ownership - contrarian_ownership,
                    'leverage_score': (popular_ownership - contrarian_ownership) * game['avg_projection']
                })
        
        # Sort by leverage score (highest opportunity first)
        contrarian_games.sort(key=lambda x: x['leverage_score'], reverse=True)
        
        logger.info(f"FOUND: {len(contrarian_games)} contrarian opportunities")
        return contrarian_games
    
    def build_contrarian_stacks(self, contrarian_games):
        """Build actual player stacks from contrarian opportunities"""
        stacks = []
        
        for opportunity in contrarian_games[:5]:  # Top 5 opportunities
            team = opportunity['contrarian_team']
            
            # Find players from this team
            team_players = []
            
            # Check projections data
            if self.projections_data is not None:
                proj_players = self.projections_data[
                    self.projections_data['Team'].str.contains(team, case=False, na=False)
                ]
                
                for _, player in proj_players.iterrows():
                    # Get ownership for this player
                    player_ownership = self.get_player_ownership(player.get('Name', player.get('Nickname', '')))
                    
                    team_players.append({
                        'name': player.get('Name', player.get('Nickname', '')),
                        'position': player.get('Position', ''),
                        'salary': player.get('Salary', 0),
                        'projection': player.get('FPPG', player.get('enhanced_fppg', 0)),
                        'ownership': player_ownership,
                        'value': (player.get('FPPG', player.get('enhanced_fppg', 0)) or 0) / max(player.get('Salary', 1), 1) * 1000
                    })
            
            # Sort by value and ownership (low ownership, high value preferred)
            team_players.sort(key=lambda x: (x['value'] * (10 - x['ownership'])), reverse=True)
            
            # Build stack (top 3-4 players)
            stack_players = team_players[:4]
            total_salary = sum(p['salary'] for p in stack_players)
            total_projection = sum(p['projection'] or 0 for p in stack_players)
            avg_ownership = np.mean([p['ownership'] for p in stack_players])
            
            stacks.append({
                'team': team,
                'game': opportunity['game'],
                'players': stack_players,
                'total_salary': total_salary,
                'total_projection': total_projection,
                'avg_ownership': avg_ownership,
                'leverage_score': opportunity['leverage_score'],
                'ownership_edge': opportunity['ownership_edge']
            })
        
        return stacks
    
    def get_player_ownership(self, player_name):
        """Get ownership projection for a specific player"""
        if self.ownership_data is None or not player_name:
            return 5.0
            
        # Try to find player by name
        player_match = self.ownership_data[
            self.ownership_data['player_name'].str.contains(player_name.split()[-1], case=False, na=False)
        ]
        
        if not player_match.empty:
            ownership = player_match['ownership'].iloc[0]
            return ownership * 100 if ownership < 1 else ownership
        
        return 5.0  # Default ownership
    
    def generate_contrarian_lineups(self, num_lineups=20):
        """Generate lineups focused on contrarian stacks"""
        lineups = []
        
        contrarian_games = self.find_contrarian_opportunities()
        contrarian_stacks = self.build_contrarian_stacks(contrarian_games)
        
        logger.info("🎯 CONTRARIAN OPPORTUNITIES FOUND:")
        for i, opp in enumerate(contrarian_games[:5], 1):
            logger.info(f"{i}. {opp['game']} | {opp['contrarian_team']} ({opp['contrarian_ownership']:.1f}%) vs {opp['popular_team']} ({opp['popular_ownership']:.1f}%) | Edge: {opp['ownership_edge']:.1f}%")
        
        logger.info("\n🏆 CONTRARIAN STACKS BUILT:")
        for i, stack in enumerate(contrarian_stacks, 1):
            logger.info(f"{i}. {stack['team']} Stack | ${stack['total_salary']:,} | {stack['total_projection']:.1f} pts | {stack['avg_ownership']:.1f}% own")
            for player in stack['players']:
                logger.info(f"   • {player['name']} ({player['position']}) - ${player['salary']} | {player['projection']:.1f} pts | {player['ownership']:.1f}%")
        
        return contrarian_stacks
    
    def run_analysis(self):
        """Run the complete contrarian stack analysis"""
        logger.info("🔍 STARTING CONTRARIAN GAME STACK ANALYSIS")
        logger.info("=" * 50)
        
        if not self.load_data():
            logger.error("Failed to load required data")
            return
        
        self.identify_game_environments()
        contrarian_stacks = self.generate_contrarian_lineups()
        
        logger.info(f"\n✅ ANALYSIS COMPLETE: {len(contrarian_stacks)} contrarian stacks identified")
        return contrarian_stacks

if __name__ == "__main__":
    finder = ContrarianStackFinder()
    stacks = finder.run_analysis()
