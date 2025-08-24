"""
DFS LINEUP BACKTEST VALIDATOR
============================

Input actual MLB results from July 21, 2025 to validate how our enhanced
DFS lineups would have performed vs the old method.

This will calculate actual fantasy points scored by each lineup and compare
performance to see if the enhancements worked.
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class DFSBacktestValidator:
    def __init__(self):
        self.fanduel_scoring = {
            'single': 3,
            'double': 6,  # 3 for hit + 3 for double
            'triple': 9,  # 3 for hit + 6 for triple
            'home_run': 10,  # 3 for hit + 7 for home run
            'rbi': 3.5,
            'run': 3.2,
            'walk': 2,
            'hbp': 2,
            'stolen_base': 6
        }
    
    def create_results_template(self, date_str='20250721'):
        """Create template for entering actual player stats from July 21"""
        
        template_path = f"../data/mlb_actual_results_{date_str}.csv"
        
        if os.path.exists(template_path):
            print(f"SUCCESS: Results template already exists: {template_path}")
            print(f" Please fill in actual stats and re-run validation")
            return template_path
        
        # Create comprehensive template with all possible players
        template_data = {
            'Name': [
                'Aaron Judge', 'Byron Buxton', 'Cal Raleigh', 'Bobby Witt Jr.',
                'Pete Alonso', 'Jose Ramirez', 'Ketel Marte', 'Jazz Chisholm Jr.',
                'Brewer Hicklen', 'Noelvi Marte', 'Wyatt Langford', 'Freddie Freeman',
                'Corey Seager', 'Jose Altuve', 'Ivan Herrera', 'Gleyber Torres',
                'Shohei Ohtani', 'Juan Soto', 'Ronald Acuna Jr.', 'Mookie Betts',
                'Vladimir Guerrero Jr.', 'Yordan Alvarez', 'Mike Trout', 'Kyle Tucker',
                'Trea Turner', 'Manny Machado', 'Rafael Devers', 'Bo Bichette'
            ],
            'Team': [
                'NYY', 'MIN', 'SEA', 'KC', 'NYM', 'CLE', 'ARI', 'NYY',
                'DET', 'CIN', 'TEX', 'LAD', 'TEX', 'HOU', 'STL', 'DET',
                'LAD', 'NYY', 'ATL', 'LAD', 'TOR', 'HOU', 'LAA', 'HOU',
                'LAD', 'SD', 'BOS', 'TOR'
            ],
            'AB': [0] * 28,        # At Bats
            'H': [0] * 28,         # Hits
            'R': [0] * 28,         # Runs
            'RBI': [0] * 28,       # RBIs
            'HR': [0] * 28,        # Home Runs
            'SB': [0] * 28,        # Stolen Bases
            '2B': [0] * 28,        # Doubles
            '3B': [0] * 28,        # Triples
            'BB': [0] * 28,        # Walks
            'HBP': [0] * 28,       # Hit by Pitch
            'K': [0] * 28,         # Strikeouts
            'Game_Played': [1] * 28,  # 1 if played, 0 if didn't play
            'Notes': [''] * 28     # Game notes
        }
        
        template_df = pd.DataFrame(template_data)
        template_df.to_csv(template_path, index=False)
        
        print(f" Created results template: {template_path}")
        print(f"")
        print(f"TARGET: INSTRUCTIONS:")
        print(f"1. Open {template_path} in Excel or CSV editor")
        print(f"2. Fill in ACTUAL stats for each player from July 21, 2025")
        print(f"3. Use 0 for players who didn't play")
        print(f"4. Save the file and re-run this validator")
        print(f"")
        print(f"DATA: STAT DEFINITIONS:")
        print(f"   AB = At Bats, H = Hits, R = Runs, RBI = RBIs")
        print(f"   HR = Home Runs, 2B = Doubles, 3B = Triples")
        print(f"   BB = Walks, HBP = Hit by Pitch, SB = Stolen Bases")
        print(f"   Game_Played = 1 if played, 0 if didn't play")
        
        return template_path
    
    def calculate_fantasy_points(self, player_stats):
        """Calculate FanDuel fantasy points for a player"""
        
        if player_stats.get('Game_Played', 1) == 0:
            return 0.0  # Player didn't play
        
        # Get basic stats
        hits = player_stats.get('H', 0)
        doubles = player_stats.get('2B', 0)
        triples = player_stats.get('3B', 0)
        home_runs = player_stats.get('HR', 0)
        rbis = player_stats.get('RBI', 0)
        runs = player_stats.get('R', 0)
        walks = player_stats.get('BB', 0)
        hbp = player_stats.get('HBP', 0)
        stolen_bases = player_stats.get('SB', 0)
        
        # Calculate singles
        singles = max(0, hits - doubles - triples - home_runs)
        
        # Calculate fantasy points using FanDuel scoring
        points = (
            singles * self.fanduel_scoring['single'] +
            doubles * self.fanduel_scoring['double'] +
            triples * self.fanduel_scoring['triple'] +
            home_runs * self.fanduel_scoring['home_run'] +
            rbis * self.fanduel_scoring['rbi'] +
            runs * self.fanduel_scoring['run'] +
            walks * self.fanduel_scoring['walk'] +
            hbp * self.fanduel_scoring['hbp'] +
            stolen_bases * self.fanduel_scoring['stolen_base']
        )
        
        return round(points, 1)
    
    def load_actual_results(self, results_file):
        """Load actual player results from CSV"""
        
        if not os.path.exists(results_file):
            print(f"ERROR: Results file not found: {results_file}")
            return None
        
        try:
            df = pd.read_csv(results_file)
            print(f"SUCCESS: Loaded actual results for {len(df)} players")
            
            # Calculate fantasy points for each player
            df['Actual_FPPG'] = df.apply(self.calculate_fantasy_points, axis=1)
            
            # Create lookup dictionary
            results_dict = {}
            for _, row in df.iterrows():
                name = row['Name'].strip()
                results_dict[name] = {
                    'actual_fppg': row['Actual_FPPG'],
                    'hits': row.get('H', 0),
                    'home_runs': row.get('HR', 0),
                    'rbis': row.get('RBI', 0),
                    'runs': row.get('R', 0),
                    'stolen_bases': row.get('SB', 0),
                    'walks': row.get('BB', 0),
                    'game_played': row.get('Game_Played', 1)
                }
            
            return results_dict
            
        except Exception as e:
            print(f"ERROR: Error loading results: {str(e)}")
            return None
    
    def validate_lineups(self, lineup_file, results_dict):
        """Validate lineup performance against actual results"""
        
        if not os.path.exists(lineup_file):
            print(f"ERROR: Lineup file not found: {lineup_file}")
            return None
        
        try:
            lineup_df = pd.read_csv(lineup_file)
            print(f"SUCCESS: Loaded {len(lineup_df)} lineup entries")
            
            # Group by lineup_id
            lineup_results = []
            
            for lineup_id in lineup_df['lineup_id'].unique():
                lineup_players = lineup_df[lineup_df['lineup_id'] == lineup_id]
                
                if len(lineup_players) != 9:
                    print(f"WARNING: Lineup {lineup_id} has {len(lineup_players)} players (should be 9)")
                    continue
                
                # Calculate actual performance
                actual_total = 0
                projected_total = 0
                lineup_salary = 0
                strategy = lineup_players.iloc[0]['strategy']
                players_found = 0
                player_details = []
                
                for _, player in lineup_players.iterrows():
                    player_name = player['name']
                    projected_fppg = player['enhanced_fppg']
                    salary = player['salary']
                    
                    # Find actual performance
                    actual_performance = self.find_player_performance(player_name, results_dict)
                    
                    if actual_performance is not None:
                        actual_fppg = actual_performance['actual_fppg']
                        players_found += 1
                    else:
                        actual_fppg = 0
                        print(f"   WARNING: No results found for {player_name}")
                    
                    actual_total += actual_fppg
                    projected_total += projected_fppg
                    lineup_salary += salary
                    
                    player_details.append({
                        'name': player_name,
                        'position': player['position'],
                        'salary': salary,
                        'projected': projected_fppg,
                        'actual': actual_fppg,
                        'difference': actual_fppg - projected_fppg
                    })
                
                # Store lineup result
                lineup_results.append({
                    'lineup_id': lineup_id,
                    'strategy': strategy,
                    'total_salary': lineup_salary,
                    'projected_fppg': projected_total,
                    'actual_fppg': actual_total,
                    'difference': actual_total - projected_total,
                    'accuracy': (actual_total / projected_total) if projected_total > 0 else 0,
                    'players_found': players_found,
                    'player_details': player_details
                })
            
            return lineup_results
            
        except Exception as e:
            print(f"ERROR: Error validating lineups: {str(e)}")
            return None
    
    def find_player_performance(self, player_name, results_dict):
        """Find player performance with fuzzy matching"""
        
        # Direct match
        if player_name in results_dict:
            return results_dict[player_name]
        
        # Try fuzzy matching
        for result_name in results_dict.keys():
            # Check if last names match
            player_last = player_name.split()[-1].lower()
            result_last = result_name.split()[-1].lower()
            
            if player_last == result_last:
                return results_dict[result_name]
            
            # Check if player name is contained in result name or vice versa
            if player_last in result_name.lower() or result_last in player_name.lower():
                return results_dict[result_name]
        
        return None
    
    def analyze_results(self, lineup_results):
        """Analyze and display validation results"""
        
        if not lineup_results:
            print("ERROR: No lineup results to analyze")
            return
        
        print(f"\nLINEUP: DFS LINEUP BACKTEST VALIDATION RESULTS")
        print("=" * 60)
        
        # Overall performance
        total_lineups = len(lineup_results)
        avg_projected = np.mean([r['projected_fppg'] for r in lineup_results])
        avg_actual = np.mean([r['actual_fppg'] for r in lineup_results])
        avg_difference = avg_actual - avg_projected
        
        print(f"Total Lineups Analyzed: {total_lineups}")
        print(f"Average Projected FPPG: {avg_projected:.1f}")
        print(f"Average Actual FPPG: {avg_actual:.1f}")
        print(f"Average Difference: {avg_difference:+.1f} ({avg_difference/avg_projected:+.1%})")
        
        # Performance by strategy
        print(f"\nDATA: PERFORMANCE BY STRATEGY:")
        strategies = {}
        for result in lineup_results:
            strategy = result['strategy']
            if strategy not in strategies:
                strategies[strategy] = []
            strategies[strategy].append(result)
        
        for strategy, results in strategies.items():
            strategy_projected = np.mean([r['projected_fppg'] for r in results])
            strategy_actual = np.mean([r['actual_fppg'] for r in results])
            strategy_diff = strategy_actual - strategy_projected
            
            print(f"  {strategy:>8}: {strategy_actual:5.1f} actual vs {strategy_projected:5.1f} projected ({strategy_diff:+4.1f})")
        
        # High-scoring lineups
        high_scoring = [r for r in lineup_results if r['actual_fppg'] >= 150]
        elite_scoring = [r for r in lineup_results if r['actual_fppg'] >= 180]
        legendary_scoring = [r for r in lineup_results if r['actual_fppg'] >= 210]
        
        print(f"\nTARGET: HIGH-SCORING LINEUP ANALYSIS:")
        print(f"150+ Point Lineups: {len(high_scoring)} ({len(high_scoring)/total_lineups:.1%})")
        print(f"180+ Point Lineups: {len(elite_scoring)} ({len(elite_scoring)/total_lineups:.1%})")
        print(f"210+ Point Lineups: {len(legendary_scoring)} ({len(legendary_scoring)/total_lineups:.1%})")
        
        # Top performing lineups
        sorted_lineups = sorted(lineup_results, key=lambda x: x['actual_fppg'], reverse=True)
        
        print(f"\nLINEUP: TOP 5 ACTUAL PERFORMING LINEUPS:")
        print("-" * 60)
        
        for i, result in enumerate(sorted_lineups[:5]):
            print(f"\n#{i+1} - Lineup {result['lineup_id']} ({result['strategy']}):")
            print(f"   Actual: {result['actual_fppg']:.1f} FPPG | Projected: {result['projected_fppg']:.1f} | Diff: {result['difference']:+.1f}")
            print(f"   Salary: ${result['total_salary']:,}")
            
            # Show player breakdown
            for player in result['player_details']:
                status = "SUCCESS:" if player['actual'] > player['projected'] else "ERROR:" if player['actual'] < player['projected'] else ""
                print(f"     {status} {player['name']:<20} {player['position']:<4} ${player['salary']:,} | {player['actual']:4.1f} vs {player['projected']:4.1f} ({player['difference']:+4.1f})")
        
        # Biggest surprises (positive and negative)
        biggest_beats = sorted(lineup_results, key=lambda x: x['difference'], reverse=True)[:3]
        biggest_misses = sorted(lineup_results, key=lambda x: x['difference'])[:3]
        
        print(f"\nPROGRESS: BIGGEST POSITIVE SURPRISES:")
        for result in biggest_beats:
            print(f"   Lineup {result['lineup_id']:2d}: {result['actual_fppg']:5.1f} actual vs {result['projected_fppg']:5.1f} projected (+{result['difference']:4.1f})")
        
        print(f"\n BIGGEST DISAPPOINTMENTS:")
        for result in biggest_misses:
            print(f"   Lineup {result['lineup_id']:2d}: {result['actual_fppg']:5.1f} actual vs {result['projected_fppg']:5.1f} projected ({result['difference']:+4.1f})")
        
        # Prediction accuracy analysis
        accurate_lineups = [r for r in lineup_results if abs(r['difference']) <= 20]
        very_accurate = [r for r in lineup_results if abs(r['difference']) <= 10]
        
        print(f"\nTARGET: PREDICTION ACCURACY:")
        print(f"Within 20 points: {len(accurate_lineups)} ({len(accurate_lineups)/total_lineups:.1%})")
        print(f"Within 10 points: {len(very_accurate)} ({len(very_accurate)/total_lineups:.1%})")
        
        return lineup_results
    
    def save_validation_results(self, lineup_results, output_file):
        """Save detailed validation results"""
        
        if not lineup_results:
            return
        
        # Flatten results for CSV
        flattened_results = []
        
        for result in lineup_results:
            for player in result['player_details']:
                flattened_results.append({
                    'lineup_id': result['lineup_id'],
                    'strategy': result['strategy'],
                    'lineup_projected_total': result['projected_fppg'],
                    'lineup_actual_total': result['actual_fppg'],
                    'lineup_difference': result['difference'],
                    'lineup_salary': result['total_salary'],
                    'player_name': player['name'],
                    'player_position': player['position'],
                    'player_salary': player['salary'],
                    'player_projected': player['projected'],
                    'player_actual': player['actual'],
                    'player_difference': player['difference']
                })
        
        results_df = pd.DataFrame(flattened_results)
        results_df.to_csv(output_file, index=False)
        
        print(f"\n Detailed validation results saved: {output_file}")

def main():
    """Run DFS lineup backtest validation"""
    
    print("TARGET: DFS LINEUP BACKTEST VALIDATOR")
    print("=" * 50)
    print("Validate July 21, 2025 enhanced lineup performance")
    print()
    
    validator = DFSBacktestValidator()
    
    # Create or check for results template
    results_template = validator.create_results_template()
    
    # Check if results are filled in
    results_dict = validator.load_actual_results(results_template)
    
    if results_dict is None:
        print(f"\n Please fill in the results template and re-run this script")
        return
    
    # Check if any actual results were entered
    total_actual_points = sum(player['actual_fppg'] for player in results_dict.values())
    
    if total_actual_points == 0:
        print(f"\nWARNING: No actual fantasy points found in results file")
        print(f" Please enter real player stats from July 21, 2025 and re-run")
        return
    
    print(f"SUCCESS: Found actual results with {total_actual_points:.1f} total fantasy points")
    
    # Load and validate lineups
    lineup_file = r'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\enhanced_backtest_lineups_20250721.csv'
    
    lineup_results = validator.validate_lineups(lineup_file, results_dict)
    
    if lineup_results is None:
        return
    
    # Analyze results
    validator.analyze_results(lineup_results)
    
    # Save detailed results
    output_file = r'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\dfs_validation_results_20250721.csv'
    validator.save_validation_results(lineup_results, output_file)
    
    print(f"\nSUCCESS: VALIDATION COMPLETE!")
    print(f"TARGET: This analysis shows how the enhanced DFS models performed")
    print(f"DATA: Compare these results to your actual submitted lineups")
    print(f"START: Use insights to further improve the optimization models")

if __name__ == "__main__":
    main()
