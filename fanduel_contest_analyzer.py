#!/usr/bin/env python3
"""
FANDUEL CONTEST ANALYZER
========================
Analyzes FanDuel contest results to identify high-winning lineups and patterns.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent / "data"

class FanDuelContestAnalyzer:
    def __init__(self):
        self.base_url = "https://www.fanduel.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def get_contest_results_manual(self, contest_id=None, date=None):
        """
        Manual method to analyze contest results
        This requires user to manually provide contest data
        """
        logger.info("LINEUP: FanDuel Contest Analyzer - Manual Mode")
        logger.info("=" * 50)
        
        if not date:
            date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
        logger.info(f" Analyzing contests for: {date}")
        logger.info("\nINFO: CONTEST DATA COLLECTION GUIDE:")
        logger.info(" You don't need to have played to analyze winning patterns!")
        logger.info("1. Go to FanDuel.com (no login required for public contests)")
        logger.info("2. Navigate to 'Lobby'  'MLB'  'Completed Contests'")
        logger.info("3. Look for major tournaments (Main Event, Late Slate, etc.)")
        logger.info("4. Click 'View Leaderboard' on high-entry contests")
        logger.info("5. Study top 10-20 winning lineups and their patterns")
        logger.info("6. Copy the lineup details and enter them below for analysis")
        
        return self._prompt_for_manual_data()
    
    def _prompt_for_manual_data(self):
        """Prompt user for manual contest data entry"""
        print("\n" + "="*60)
        print("MANUAL CONTEST DATA ENTRY")
        print("="*60)
        print("Please enter winning lineup data (or 'done' to finish):")
        print("Format: Player,Position,Salary,Points")
        print("Example: Bryce Harper,1B,3800,24.5")
        print()
        
        lineups = []
        lineup_num = 1
        
        while True:
            print(f"\n--- LINEUP #{lineup_num} ---")
            contest_name = input("Contest Name (or 'done' to finish): ").strip()
            
            if contest_name.lower() == 'done':
                break
                
            total_points = input("Total Points: ").strip()
            
            players = []
            for i in range(9):  # FanDuel MLB has 9 positions
                player_data = input(f"Player {i+1} (Player,Position,Salary,Points): ").strip()
                if player_data:
                    try:
                        name, pos, salary, points = player_data.split(',')
                        players.append({
                            'name': name.strip(),
                            'position': pos.strip(),
                            'salary': int(salary.strip()),
                            'points': float(points.strip())
                        })
                    except ValueError:
                        print("Invalid format. Skipping this player.")
            
            if players:
                lineups.append({
                    'contest_name': contest_name,
                    'total_points': float(total_points) if total_points else sum(p['points'] for p in players),
                    'players': players
                })
                lineup_num += 1
        
        return self._analyze_manual_lineups(lineups)
    
    def _analyze_manual_lineups(self, lineups):
        """Analyze manually entered lineups"""
        if not lineups:
            logger.warning("WARNING: No lineup data provided")
            return
            
        logger.info(f"DATA: Analyzing {len(lineups)} winning lineups...")
        
        # Convert to DataFrame for analysis
        all_players = []
        lineup_summaries = []
        
        for i, lineup in enumerate(lineups):
            lineup_id = f"winning_lineup_{i+1}"
            
            lineup_summaries.append({
                'lineup_id': lineup_id,
                'contest_name': lineup['contest_name'],
                'total_points': lineup['total_points'],
                'total_salary': sum(p['salary'] for p in lineup['players']),
                'avg_salary_per_player': sum(p['salary'] for p in lineup['players']) / len(lineup['players']),
                'num_players': len(lineup['players'])
            })
            
            for player in lineup['players']:
                all_players.append({
                    'lineup_id': lineup_id,
                    'contest_name': lineup['contest_name'],
                    'player_name': player['name'],
                    'position': player['position'],
                    'salary': player['salary'],
                    'points': player['points'],
                    'value': player['points'] / player['salary'] * 1000 if player['salary'] > 0 else 0
                })
        
        df_lineups = pd.DataFrame(lineup_summaries)
        df_players = pd.DataFrame(all_players)
        
        # Generate analysis
        self._generate_winning_analysis(df_lineups, df_players)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        lineup_file = BASE_DIR / f"winning_lineups_analysis_{timestamp}.csv"
        player_file = BASE_DIR / f"winning_players_analysis_{timestamp}.csv"
        
        df_lineups.to_csv(lineup_file, index=False)
        df_players.to_csv(player_file, index=False)
        
        logger.info(f" Saved lineup analysis: {lineup_file}")
        logger.info(f" Saved player analysis: {player_file}")
        
        return df_lineups, df_players
    
    def _generate_winning_analysis(self, df_lineups, df_players):
        """Generate analysis of winning patterns"""
        logger.info("\nLINEUP: WINNING LINEUP ANALYSIS:")
        logger.info("=" * 50)
        
        # Lineup-level analysis
        logger.info(f"DATA: Total winning lineups analyzed: {len(df_lineups)}")
        logger.info(f"TARGET: Average winning score: {df_lineups['total_points'].mean():.1f}")
        logger.info(f"MONEY: Average salary used: ${df_lineups['total_salary'].mean():,.0f}")
        logger.info(f"PROGRESS: Highest scoring lineup: {df_lineups['total_points'].max():.1f}")
        logger.info(f" Lowest scoring lineup: {df_lineups['total_points'].min():.1f}")
        
        # Player-level analysis
        logger.info("\nOWNERSHIP: PLAYER ANALYSIS:")
        logger.info("-" * 30)
        
        # Most valuable players (points per $1K salary)
        top_value = df_players.nlargest(10, 'value')
        logger.info(" TOP VALUE PLAYERS (Points per $1K):")
        for _, player in top_value.iterrows():
            logger.info(f"   {player['player_name']} ({player['position']}): {player['value']:.2f} - {player['points']:.1f} pts @ ${player['salary']:,}")
        
        # Position analysis
        logger.info("\n POSITION BREAKDOWN:")
        pos_analysis = df_players.groupby('position').agg({
            'points': ['mean', 'max'],
            'salary': 'mean',
            'value': 'mean'
        }).round(2)
        
        for pos in pos_analysis.index:
            avg_pts = pos_analysis.loc[pos, ('points', 'mean')]
            max_pts = pos_analysis.loc[pos, ('points', 'max')]
            avg_sal = pos_analysis.loc[pos, ('salary', 'mean')]
            avg_val = pos_analysis.loc[pos, ('value', 'mean')]
            logger.info(f"   {pos}: Avg {avg_pts:.1f} pts (Max {max_pts:.1f}), ${avg_sal:,.0f} salary, {avg_val:.2f} value")
        
        # Salary distribution analysis
        logger.info("\nMONEY: SALARY DISTRIBUTION:")
        salary_ranges = [
            (0, 3000, "Budget"),
            (3000, 4000, "Mid-tier"),
            (4000, 5000, "Premium"),
            (5000, float('inf'), "Studs")
        ]
        
        for min_sal, max_sal, label in salary_ranges:
            players_in_range = df_players[(df_players['salary'] >= min_sal) & (df_players['salary'] < max_sal)]
            if len(players_in_range) > 0:
                avg_pts = players_in_range['points'].mean()
                count = len(players_in_range)
                logger.info(f"   {label} (${min_sal:,}+): {count} players, {avg_pts:.1f} avg pts")
    
    def analyze_your_performance(self, your_lineups_file=None, winning_lineups_df=None, winning_players_df=None):
        """Compare your lineups against winning patterns"""
        logger.info("\n COMPARING YOUR LINEUPS TO WINNERS...")
        
        # Find your most recent lineup file
        if not your_lineups_file:
            pattern = str(BASE_DIR / "enhanced_ml_dfs_lineups_*.csv")
            import glob
            files = glob.glob(pattern)
            if files:
                your_lineups_file = max(files, key=lambda x: Path(x).stat().st_mtime)
                logger.info(f" Using your lineup file: {Path(your_lineups_file).name}")
            else:
                logger.warning("WARNING: No lineup files found to compare")
                return
        
        # Load your lineups
        your_df = pd.read_csv(your_lineups_file)
        
        # Basic comparison
        logger.info(f"DATA: Your lineups: {len(your_df['lineup_id'].unique())} total")
        
        # Analyze your salary usage patterns
        lineup_analysis = your_df.groupby('lineup_id').agg({
            'salary': 'sum',
            'ml_projected_fppg': 'sum'
        }).reset_index()
        
        your_avg_salary = lineup_analysis['salary'].mean()
        your_avg_projection = lineup_analysis['ml_projected_fppg'].mean()
        
        logger.info(f"MONEY: Your avg salary usage: ${your_avg_salary:,.0f}")
        logger.info(f"TARGET: Your avg projected score: {your_avg_projection:.1f}")
        
        # If we have winning lineup data, do detailed comparison
        if winning_lineups_df is not None and winning_players_df is not None:
            logger.info("\nLINEUP: DETAILED COMPARISON TO WINNERS:")
            logger.info("-" * 50)
            
            # Salary comparison
            winner_avg_salary = winning_lineups_df['total_salary'].mean()
            salary_diff = your_avg_salary - winner_avg_salary
            logger.info(f"MONEY: Salary Usage:")
            logger.info(f"   Winners: ${winner_avg_salary:,.0f}")
            logger.info(f"   You: ${your_avg_salary:,.0f}")
            logger.info(f"   Difference: ${salary_diff:+,.0f} {'(leaving money on table)' if salary_diff < 0 else '(using more than winners)'}")
            
            # Score comparison
            winner_avg_score = winning_lineups_df['total_points'].mean()
            score_diff = your_avg_projection - winner_avg_score
            logger.info(f"\nTARGET: Scoring:")
            logger.info(f"   Winners actual: {winner_avg_score:.1f}")
            logger.info(f"   Your projection: {your_avg_projection:.1f}")
            logger.info(f"   Gap to close: {-score_diff:.1f} points")
            
            # Position spending comparison
            self._compare_position_spending(your_df, winning_players_df)
            
            # Player overlap analysis
            self._analyze_player_overlap(your_df, winning_players_df)
            
            # Value analysis
            self._compare_value_strategies(your_df, winning_players_df)
            
        else:
            logger.info("\nTIP: To get detailed comparison:")
            logger.info("1. Run option 1 first to enter winning lineup data")
            logger.info("2. Then run option 3 for complete analysis")
        
    def demo_with_sample_data(self):
        """Demo the comparison with sample winning lineup data"""
        logger.info(" DEMO MODE - Sample Winning Lineup Analysis")
        logger.info("=" * 50)
        
        # Create sample winning lineup data (realistic FanDuel $35K salary cap)
        sample_lineups = [{
            'contest_name': 'Main Event GPP',
            'total_points': 167.8,
            'players': [
                {'name': 'Zack Wheeler', 'position': 'P', 'salary': 7600, 'points': 32.5},
                {'name': 'Salvador Perez', 'position': 'C', 'salary': 3100, 'points': 18.2},
                {'name': 'Vladimir Guerrero Jr.', 'position': '1B', 'salary': 4200, 'points': 21.1},
                {'name': 'Jose Altuve', 'position': '2B', 'salary': 3600, 'points': 15.8},
                {'name': 'Manny Machado', 'position': '3B', 'salary': 3900, 'points': 19.4},
                {'name': 'Trea Turner', 'position': 'SS', 'salary': 3800, 'points': 14.2},
                {'name': 'Ronald Acuna Jr.', 'position': 'OF', 'salary': 4300, 'points': 23.6},
                {'name': 'Kyle Schwarber', 'position': 'OF', 'salary': 3200, 'points': 16.7},
                {'name': 'Jesse Winker', 'position': 'OF', 'salary': 2700, 'points': 6.3}
            ]  # Total: $33,400
        }, {
            'contest_name': 'Late Slate Tournament', 
            'total_points': 154.2,
            'players': [
                {'name': 'Shane Baz', 'position': 'P', 'salary': 7200, 'points': 28.1},
                {'name': 'J.T. Realmuto', 'position': 'C', 'salary': 3400, 'points': 11.8},
                {'name': 'Pete Alonso', 'position': '1B', 'salary': 3700, 'points': 19.5},
                {'name': 'Gleyber Torres', 'position': '2B', 'salary': 3300, 'points': 12.4},
                {'name': 'Rafael Devers', 'position': '3B', 'salary': 4100, 'points': 17.9},
                {'name': 'Bo Bichette', 'position': 'SS', 'salary': 3500, 'points': 8.6},
                {'name': 'Juan Soto', 'position': 'OF', 'salary': 4400, 'points': 22.3},
                {'name': 'Teoscar Hernandez', 'position': 'OF', 'salary': 3300, 'points': 18.1},
                {'name': 'Austin Riley', 'position': 'OF', 'salary': 3200, 'points': 15.5}
            ]  # Total: $34,100
        }]
        
        # Analyze sample data
        df_lineups, df_players = self._analyze_manual_lineups(sample_lineups)
        
        # Compare to your lineups
        if df_lineups is not None and df_players is not None:
            self.analyze_your_performance(winning_lineups_df=df_lineups, winning_players_df=df_players)
            
        logger.info("\nTIP: This was a DEMO with sample data!")
        logger.info("   To analyze real winners, run option 1 or 3 with actual FanDuel data")
        
        return df_lineups, df_players
    
    def _compare_position_spending(self, your_df, winning_players_df):
        """Compare position-by-position spending patterns"""
        logger.info("\nMONEY: POSITION SPENDING COMPARISON:")
        logger.info("-" * 40)
        
        # Your position spending
        your_pos_spending = your_df.groupby('position')['salary'].mean()
        
        # Winners' position spending
        winners_pos_spending = winning_players_df.groupby('position')['salary'].mean()
        
        # Compare each position
        all_positions = set(your_pos_spending.index) | set(winners_pos_spending.index)
        
        for pos in sorted(all_positions):
            your_spend = your_pos_spending.get(pos, 0)
            winner_spend = winners_pos_spending.get(pos, 0)
            diff = your_spend - winner_spend
            
            if your_spend > 0 and winner_spend > 0:
                logger.info(f"   {pos:3}: You ${your_spend:,.0f} | Winners ${winner_spend:,.0f} | Diff ${diff:+,.0f}")
            elif your_spend > 0:
                logger.info(f"   {pos:3}: You ${your_spend:,.0f} | Winners: N/A")
            elif winner_spend > 0:
                logger.info(f"   {pos:3}: You: N/A | Winners ${winner_spend:,.0f}")
    
    def _analyze_player_overlap(self, your_df, winning_players_df):
        """Analyze which players appeared in both your lineups and winning lineups"""
        logger.info("\nOWNERSHIP: PLAYER OVERLAP ANALYSIS:")
        logger.info("-" * 35)
        
        your_players = set(your_df['name'].str.lower())
        winning_players = set(winning_players_df['player_name'].str.lower())
        
        overlap = your_players & winning_players
        your_only = your_players - winning_players
        winners_only = winning_players - your_players
        
        logger.info(f"TARGET: Players in both: {len(overlap)}")
        logger.info(f"DATA: Your unique players: {len(your_only)}")
        logger.info(f"LINEUP: Winners' unique players: {len(winners_only)}")
        
        if overlap:
            logger.info(f"\nSUCCESS: SHARED PLAYERS:")
            for player in sorted(overlap):
                logger.info(f"   {player.title()}")
        
        if winners_only:
            logger.info(f"\nERROR: PLAYERS YOU MISSED:")
            winning_unique = winning_players_df[winning_players_df['player_name'].str.lower().isin(winners_only)]
            top_missed = winning_unique.nlargest(5, 'value')
            for _, player in top_missed.iterrows():
                logger.info(f"   {player['player_name']} ({player['position']}): {player['points']:.1f} pts @ ${player['salary']:,} = {player['value']:.2f} value")
    
    def _compare_value_strategies(self, your_df, winning_players_df):
        """Compare value (points per dollar) strategies"""
        logger.info("\nPROGRESS: VALUE STRATEGY COMPARISON:")
        logger.info("-" * 35)
        
        # Calculate your value metrics (need actual results for this)
        logger.info("TIP: Your value analysis requires actual game results")
        logger.info("   Run analyze_dfs_performance.py to see your actual values")
        
        # Show winners' value distribution
        winners_value_avg = winning_players_df['value'].mean()
        winners_value_top = winning_players_df['value'].quantile(0.75)
        
        logger.info(f"\nLINEUP: WINNERS' VALUE METRICS:")
        logger.info(f"   Average value: {winners_value_avg:.2f} points per $1K")
        logger.info(f"   Top 25% threshold: {winners_value_top:.2f} points per $1K")
        
        # Show value by position for winners
        logger.info(f"\n WINNERS' VALUE BY POSITION:")
        pos_value = winning_players_df.groupby('position')['value'].mean().sort_values(ascending=False)
        for pos, value in pos_value.items():
            logger.info(f"   {pos}: {value:.2f} avg value")
    
    def get_optimal_stacks(self, df_players):
        """Identify common stacking patterns in winning lineups"""
        logger.info("\n STACKING ANALYSIS:")
        logger.info("-" * 30)
        
        # Team stacking analysis
        if 'team' in df_players.columns:
            team_counts = df_players.groupby(['lineup_id', 'team']).size()
            stacks = team_counts[team_counts >= 2].reset_index()
            stacks.columns = ['lineup_id', 'team', 'players_from_team']
            
            popular_stacks = stacks.groupby('team')['players_from_team'].agg(['count', 'mean']).sort_values('count', ascending=False)
            
            logger.info(" POPULAR TEAM STACKS:")
            for team, data in popular_stacks.head(5).iterrows():
                logger.info(f"   {team}: Used in {data['count']} lineups, avg {data['mean']:.1f} players")
    
    def generate_winning_recommendations(self, df_players):
        """Generate recommendations based on winning patterns"""
        logger.info("\nTIP: RECOMMENDATIONS FOR FUTURE LINEUPS:")
        logger.info("=" * 50)
        
        # Value thresholds
        high_value_threshold = df_players['value'].quantile(0.75)
        
        logger.info(f"TARGET: Target players with value > {high_value_threshold:.2f} points per $1K")
        
        # Position spending recommendations
        pos_spending = df_players.groupby('position')['salary'].mean().sort_values(ascending=False)
        
        logger.info("MONEY: OPTIMAL POSITION SPENDING:")
        for pos, avg_salary in pos_spending.items():
            logger.info(f"   {pos}: ~${avg_salary:,.0f}")
        
        # High-upside plays
        high_scorers = df_players[df_players['points'] >= df_players['points'].quantile(0.8)]
        
        logger.info(f"\nSTART: HIGH-UPSIDE PLAYS (Top 20% scorers):")
        for pos in high_scorers['position'].unique():
            pos_players = high_scorers[high_scorers['position'] == pos]['player_name'].unique()
            if len(pos_players) > 0:
                logger.info(f"   {pos}: {', '.join(pos_players[:3])}")

def main():
    """Main execution function"""
    analyzer = FanDuelContestAnalyzer()
    
    print("\n" + "="*60)
    print("LINEUP: FANDUEL CONTEST ANALYZER")
    print("="*60)
    print("Choose an option:")
    print("1. Analyze winning lineups (manual entry)")
    print("2. Compare your performance to winners (basic)")
    print("3. Full analysis: Enter winners + detailed comparison")
    print("4. Load previous winning analysis and compare")
    print("5. DEMO: Show comparison with sample winning data")
    print()
    
    choice = input("Enter your choice (1-5): ").strip()
    
    if choice == "1":
        analyzer.get_contest_results_manual()
    elif choice == "2":
        analyzer.analyze_your_performance()
    elif choice == "3":
        # Get winning data first, then do detailed comparison
        df_lineups, df_players = analyzer.get_contest_results_manual()
        if df_lineups is not None and df_players is not None:
            analyzer.analyze_your_performance(winning_lineups_df=df_lineups, winning_players_df=df_players)
            analyzer.get_optimal_stacks(df_players)
            analyzer.generate_winning_recommendations(df_players)
    elif choice == "4":
        # Load most recent winning analysis files
        import glob
        lineup_files = glob.glob(str(BASE_DIR / "winning_lineups_analysis_*.csv"))
        player_files = glob.glob(str(BASE_DIR / "winning_players_analysis_*.csv"))
        
        if lineup_files and player_files:
            latest_lineup_file = max(lineup_files, key=lambda x: Path(x).stat().st_mtime)
            latest_player_file = max(player_files, key=lambda x: Path(x).stat().st_mtime)
            
            df_lineups = pd.read_csv(latest_lineup_file)
            df_players = pd.read_csv(latest_player_file)
            
            logger.info(f" Loaded previous analysis: {Path(latest_lineup_file).name}")
            analyzer.analyze_your_performance(winning_lineups_df=df_lineups, winning_players_df=df_players)
        else:
            logger.warning("WARNING: No previous winning analysis files found. Run option 1 first.")
    elif choice == "5":
        # Demo with sample data
        analyzer.demo_with_sample_data()
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
