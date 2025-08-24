#!/usr/bin/env python3
"""
COMPREHENSIVE LINEUP BACKTEST FOR 08/15/2025
=============================================
Analyze all generated lineups vs actual results to see GPP performance
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveBacktest:
    def __init__(self):
        self.actual_results = None
        self.all_lineups = []
        self.lineup_scores = []
        self.data_dir = "../data"
        
    def load_actual_results(self):
        """Load actual player results from 08/15/2025"""
        try:
            # Try to find the actual results file
            results_files = [
                "actual_results_20250815.csv",
                "actual_results_latest.csv"
            ]
            
            for file in results_files:
                path = os.path.join(self.data_dir, file)
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    # Filter for 08/15/2025 if it contains multiple dates
                    if 'Date' in df.columns:
                        df = df[df['Date'] == '2025-08-15']
                    self.actual_results = df
                    logger.info(f"SUCCESS: Loaded actual results from {file}")
                    logger.info(f"RESULTS: {len(df)} player performances found")
                    return True
            
            logger.warning("No actual results file found - will simulate based on typical scoring")
            return False
            
        except Exception as e:
            logger.error(f"Error loading actual results: {e}")
            return False
    
    def load_all_lineups(self):
        """Load all generated lineups from final run"""
        lineup_files = [
            ("Enhanced ML DFS", "enhanced_ml_dfs_lineups_20250815_175825.csv"),
            ("Elite Tournament", "elite_tournament_lineups_20250815_175721.csv"),
            ("Enhanced Ceiling", "enhanced_ceiling_lineups_20250815_175828.csv")
        ]
        
        total_loaded = 0
        
        for lineup_type, filename in lineup_files:
            try:
                path = os.path.join(self.data_dir, filename)
                if os.path.exists(path):
                    df = pd.read_csv(path)
                    
                    # Add source information
                    for idx, lineup in df.iterrows():
                        lineup_dict = lineup.to_dict()
                        lineup_dict['source'] = lineup_type
                        lineup_dict['lineup_id'] = f"{lineup_type}_{idx+1}"
                        self.all_lineups.append(lineup_dict)
                    
                    logger.info(f"LOADED: {len(df)} lineups from {lineup_type}")
                    total_loaded += len(df)
                    
            except Exception as e:
                logger.error(f"Error loading {filename}: {e}")
        
        logger.info(f"TOTAL: {total_loaded} lineups loaded for backtest")
        return total_loaded > 0
    
    def calculate_lineup_score(self, lineup):
        """Calculate actual fantasy points for a lineup"""
        total_score = 0
        positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
        
        # Handle different column naming conventions
        position_mappings = {
            'P': ['P', 'Pitcher'],
            'C': ['C', 'Catcher'], 
            '1B': ['1B', 'First_Base'],
            '2B': ['2B', 'Second_Base'],
            '3B': ['3B', 'Third_Base'],
            'SS': ['SS', 'Shortstop'],
            'OF1': ['OF1', 'OF', 'Outfield_1'],
            'OF2': ['OF2', 'Outfield_2'], 
            'OF3': ['OF3', 'Outfield_3']
        }
        
        lineup_players = []
        
        for pos in positions:
            player_name = None
            
            # Try different column name possibilities
            for possible_col in position_mappings.get(pos, [pos]):
                if possible_col in lineup and pd.notna(lineup[possible_col]):
                    player_name = lineup[possible_col]
                    break
            
            if player_name:
                lineup_players.append(player_name)
                
                # Get actual score if we have results
                if self.actual_results is not None:
                    player_results = self.actual_results[
                        self.actual_results['name'].str.contains(player_name.split()[-1], case=False, na=False)
                    ]
                    
                    if not player_results.empty:
                        # Use FanDuel scoring if available, otherwise calculate
                        if 'fanduel_points' in player_results.columns:
                            player_score = player_results['fanduel_points'].iloc[0]
                        else:
                            # Calculate fantasy points from stats
                            player_score = self.calculate_fantasy_points(player_results.iloc[0])
                        
                        total_score += player_score
                    else:
                        # Use projected score if no actual results
                        proj_col = lineup.get('Projected_Points', lineup.get('projection', 0))
                        if pd.notna(proj_col):
                            total_score += float(proj_col) / 9  # Rough per-player estimate
                        else:
                            total_score += 8.0  # Default estimate
        
        return total_score, lineup_players
    
    def calculate_fantasy_points(self, player_stats):
        """Calculate DraftKings fantasy points from stats"""
        try:
            # DraftKings scoring
            points = 0
            
            # Hitting stats
            if 'H' in player_stats: points += player_stats.get('H', 0) * 3
            if 'HR' in player_stats: points += player_stats.get('HR', 0) * 10  
            if 'RBI' in player_stats: points += player_stats.get('RBI', 0) * 2
            if 'R' in player_stats: points += player_stats.get('R', 0) * 2
            if 'BB' in player_stats: points += player_stats.get('BB', 0) * 2
            if 'SB' in player_stats: points += player_stats.get('SB', 0) * 5
            
            # Pitching stats (if pitcher)
            if 'IP' in player_stats and player_stats.get('IP', 0) > 0:
                points += player_stats.get('IP', 0) * 2.25
                points += player_stats.get('SO', 0) * 2
                points += player_stats.get('W', 0) * 4
                points -= player_stats.get('ER', 0) * 2
                points -= player_stats.get('H_allowed', player_stats.get('H', 0)) * 0.6
                points -= player_stats.get('BB_allowed', 0) * 0.6
            
            return max(0, points)  # No negative scores
            
        except Exception as e:
            logger.warning(f"Error calculating points: {e}")
            return 0
    
    def analyze_gpp_performance(self):
        """Analyze how lineups would have performed in GPP"""
        if not self.lineup_scores:
            return
        
        # Sort by score
        sorted_scores = sorted(self.lineup_scores, key=lambda x: x['total_score'], reverse=True)
        
        logger.info("🏆 GPP BACKTEST ANALYSIS")
        logger.info("=" * 50)
        
        # Top 10 lineups
        logger.info("🥇 TOP 10 LINEUPS THAT COULD HAVE WON:")
        for i, lineup in enumerate(sorted_scores[:10], 1):
            logger.info(f"{i:2d}. {lineup['lineup_id']:<25} | {lineup['total_score']:.1f} pts | Source: {lineup['source']}")
        
        # Your submitted lineups performance
        logger.info("\n🎯 YOUR SUBMITTED LINEUPS PERFORMANCE:")
        submitted_players = [
            ["Hurston Waldrep", "Carlos Narvaez", "Matt Olson", "Luke Keaschall", "Alex Bregman", "Zach Neto", "Jarren Duran", "Byron Buxton", "Roman Anthony"],
            ["Hurston Waldrep", "Carlos Narvaez", "Matt Olson", "Luke Keaschall", "Alex Bregman", "Trevor Story", "Jarren Duran", "Byron Buxton", "Jurickson Profar"],
            ["Hurston Waldrep", "Carlos Narvaez", "Matt Olson", "Luke Keaschall", "Alex Bregman", "Trevor Story", "Roman Anthony", "Byron Buxton", "Jakob Marsee"],
            ["Hurston Waldrep", "Logan O'Hoppe", "Matt Olson", "Luke Keaschall", "Alex Bregman", "Zach Neto", "Taylor Ward", "Byron Buxton", "Roman Anthony"],
            ["Hurston Waldrep", "Cal Raleigh", "Nolan Schanuel", "Luke Keaschall", "Yoan Moncada", "Zach Neto", "Taylor Ward", "Byron Buxton", "Rob Refsnyder"]
        ]
        
        for i, players in enumerate(submitted_players, 1):
            # Find this lineup in our results
            lineup_found = False
            for lineup in sorted_scores:
                if self.lineups_match(lineup['players'], players):
                    rank = sorted_scores.index(lineup) + 1
                    logger.info(f"ELITE_TOURNAMENT_{i}: {lineup['total_score']:.1f} pts | Rank: {rank}/{len(sorted_scores)}")
                    lineup_found = True
                    break
            
            if not lineup_found:
                logger.info(f"ELITE_TOURNAMENT_{i}: Not found in generated lineups")
        
        # Statistics
        top_10_pct = len([l for l in sorted_scores[:int(len(sorted_scores)*0.1)]]) 
        avg_score = np.mean([l['total_score'] for l in sorted_scores])
        
        logger.info(f"\n📊 BACKTEST STATISTICS:")
        logger.info(f"Total Lineups Generated: {len(sorted_scores)}")
        logger.info(f"Average Score: {avg_score:.1f} points")
        logger.info(f"Best Possible Score: {sorted_scores[0]['total_score']:.1f} points")
        logger.info(f"Top 10% Cutoff: {sorted_scores[int(len(sorted_scores)*0.1)]['total_score']:.1f} points")
        
        return sorted_scores
    
    def lineups_match(self, lineup1_players, lineup2_players):
        """Check if two lineups have the same players"""
        try:
            # Extract last names for comparison
            lineup1_names = [p.split()[-1].lower() for p in lineup1_players if p]
            lineup2_names = [p.split()[-1].lower() for p in lineup2_players if p]
            
            return set(lineup1_names) == set(lineup2_names)
        except:
            return False
    
    def run_comprehensive_backtest(self):
        """Run the full backtest analysis"""
        logger.info("🏆 STARTING COMPREHENSIVE LINEUP BACKTEST")
        logger.info("=" * 60)
        
        # Load data
        if not self.load_actual_results():
            logger.warning("Using projected scores for analysis")
        
        if not self.load_all_lineups():
            logger.error("Failed to load lineups")
            return
        
        # Score all lineups
        logger.info("💯 CALCULATING LINEUP SCORES...")
        for lineup in self.all_lineups:
            score, players = self.calculate_lineup_score(lineup)
            
            self.lineup_scores.append({
                'lineup_id': lineup['lineup_id'],
                'source': lineup['source'],
                'total_score': score,
                'players': players
            })
        
        # Analyze performance
        results = self.analyze_gpp_performance()
        
        logger.info("\n🎯 CONCLUSION:")
        if results:
            best_score = results[0]['total_score'] 
            logger.info(f"Best possible lineup: {best_score:.1f} points")
            logger.info(f"You generated {len(results)} lineups but only played 5")
            logger.info(f"Opportunity cost: Could have played better lineups")
        
        return results

if __name__ == "__main__":
    backtest = ComprehensiveBacktest()
    backtest.run_comprehensive_backtest()
