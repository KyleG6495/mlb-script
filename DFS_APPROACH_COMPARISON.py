#!/usr/bin/env python3
"""
DFS APPROACH COMPARISON SYSTEM
=============================
Compare all our DFS approaches:
1. Original Enhanced ML DFS (106.9 actual FPPG)
2. Filtered Slate Approach (86.7 FPPG)
3. NEW Ceiling-Focused Approach (659.1 ceiling)

Test which approach would have performed best against yesterday's 210+ leaderboard scores.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class DFSApproachComparison:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_test_data(self):
        """Load slate and actual results for testing"""
        print("DATA: Loading test data for approach comparison...")
        
        # Load slate
        slate_file = self.slate_dir / "fd_slate_today.csv"
        slate_df = pd.read_csv(slate_file)
        
        # Load actual results
        actual_file = self.data_dir / "actual_results_latest.csv"
        actual_df = pd.read_csv(actual_file)
        
        # Calculate actual FPPG
        actual_df['actual_fppg'] = (
            actual_df.get('hits', 0) * 3 +
            actual_df.get('runs', 0) * 3.2 +
            actual_df.get('rbis', 0) * 3.5 +
            actual_df.get('home_runs', 0) * 12 +
            actual_df.get('stolen_bases', 0) * 6 +
            actual_df.get('walks', 0) * 3 +
            actual_df.get('doubles', 0) * 6 +
            actual_df.get('triples', 0) * 12 +
            actual_df.get('innings_pitched', 0) * 3.5 +
            actual_df.get('wins', 0) * 12 +
            actual_df.get('earned_runs', 0) * -3
        )
        
        if 'fanduel_points' in actual_df.columns:
            actual_df['actual_fppg'] = actual_df['fanduel_points'].fillna(actual_df['actual_fppg'])
        
        # Merge slate with actuals
        slate_df['full_name'] = (slate_df['First Name'].str.strip() + ' ' + 
                                slate_df['Last Name'].str.strip()).str.lower()
        actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
        
        merged = slate_df.merge(
            actual_df[['full_name', 'actual_fppg']],
            on='full_name',
            how='left'
        )
        merged['actual_fppg'] = merged['actual_fppg'].fillna(0)
        
        print(f"SUCCESS: Loaded {len(slate_df)} slate players, {len(actual_df)} actual results")
        return merged
    
    def score_lineup_file(self, filename, merged_data):
        """Score a lineup file against actual results"""
        filepath = self.slate_dir / filename
        if not filepath.exists():
            return None
        
        lineup_df = pd.read_csv(filepath)
        
        # Handle different lineup file formats
        if 'First Name' in lineup_df.columns:
            # Standard format (like ceiling lineup)
            lineup_df['full_name'] = (lineup_df['First Name'].str.strip() + ' ' + 
                                     lineup_df['Last Name'].str.strip()).str.lower()
            
            scored_lineup = lineup_df.merge(
                merged_data[['full_name', 'actual_fppg']],
                on='full_name',
                how='left'
            )
            scored_lineup['actual_fppg'] = scored_lineup['actual_fppg'].fillna(0)
            
            total_salary = scored_lineup['Salary'].sum()
            total_projected = scored_lineup['FPPG'].sum()
            total_actual = scored_lineup['actual_fppg'].sum()
            
            return {
                'filename': filename,
                'salary': total_salary,
                'projected': total_projected,
                'actual': total_actual,
                'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0,
                'players': scored_lineup
            }
            
        elif 'Lineup_ID' in lineup_df.columns:
            # Enhanced ML format (lineup positions as columns)
            return self.score_enhanced_ml_format(lineup_df, merged_data, filename)
        
        else:
            print(f"    Unknown format for {filename}")
            return None
    
    def score_enhanced_ml_format(self, lineup_df, merged_data, filename):
        """Score Enhanced ML format lineups"""
        # Take first lineup (could expand to score all lineups)
        if len(lineup_df) == 0:
            return None
            
        first_lineup = lineup_df.iloc[0]
        
        # Extract player IDs and names from position columns
        position_cols = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        players = []
        
        for pos in position_cols:
            if pos in first_lineup and pd.notna(first_lineup[pos]):
                player_data = str(first_lineup[pos])
                if ':' in player_data:
                    player_id, player_name = player_data.split(':', 1)
                    players.append({
                        'position': pos,
                        'name': player_name.strip(),
                        'full_name': player_name.strip().lower()
                    })
        
        if len(players) != 9:
            print(f"    Warning: {filename} has {len(players)} players, expected 9")
            return None
        
        # Create DataFrame for scoring
        players_df = pd.DataFrame(players)
        
        # Merge with actual results
        scored_lineup = players_df.merge(
            merged_data[['full_name', 'actual_fppg', 'Salary', 'FPPG']],
            on='full_name',
            how='left'
        )
        scored_lineup['actual_fppg'] = scored_lineup['actual_fppg'].fillna(0)
        scored_lineup['Salary'] = scored_lineup['Salary'].fillna(0)
        scored_lineup['FPPG'] = scored_lineup['FPPG'].fillna(0)
        
        total_salary = first_lineup.get('Total_Salary', scored_lineup['Salary'].sum())
        total_projected = first_lineup.get('Total_Projection', scored_lineup['FPPG'].sum())
        total_actual = scored_lineup['actual_fppg'].sum()
        
        return {
            'filename': filename,
            'salary': total_salary,
            'projected': total_projected,
            'actual': total_actual,
            'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0,
            'players': scored_lineup
        }
    
    def load_production_lineups(self, merged_data):
        """Load and score all available lineup files"""
        print(" Loading all available lineup files...")
        
        results = {}
        
        # Check for various lineup files
        lineup_files = [
            'Enhanced_Lineups_FD_Format_20250728_183600.csv',
            'ceiling_dfs_lineup_20250729_101619.csv'
        ]
        
        # Find any additional lineup files
        for filepath in self.slate_dir.glob("*lineup*.csv"):
            if filepath.name not in lineup_files:
                lineup_files.append(filepath.name)
        
        for filename in lineup_files:
            result = self.score_lineup_file(filename, merged_data)
            if result:
                approach_name = self.identify_approach_type(filename, result)
                results[approach_name] = result
                print(f"  SUCCESS: Loaded {approach_name}: {result['actual']:.1f} actual FPPG")
            else:
                print(f"  ERROR: Could not load {filename}")
        
        return results
    
    def identify_approach_type(self, filename, result):
        """Identify the DFS approach type from filename/content"""
        if 'enhanced_ml' in filename.lower():
            return 'Enhanced_ML_DFS'
        elif 'ceiling' in filename.lower():
            return 'Ceiling_Focused'
        elif 'filtered' in filename.lower():
            return 'Filtered_Slate'
        elif 'validated' in filename.lower():
            return 'Validated_Projection'
        else:
            return f"Unknown_{filename[:15]}"
    
    def generate_optimal_hindsight(self, merged_data):
        """Generate the optimal hindsight lineup for comparison"""
        print("LINEUP: Generating optimal hindsight lineup...")
        
        # Filter to players who actually played
        played_players = merged_data[
            (merged_data['actual_fppg'] > 0) &
            (merged_data['Salary'] > 0)
        ].copy()
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = played_players[~played_players['Id'].isin(used_ids)]
            else:
                candidates = played_players[
                    (played_players['Roster Position'].str.contains(position, na=False)) &
                    (~played_players['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                return None
            
            # Pick highest actual FPPG
            chosen = affordable.loc[affordable['actual_fppg'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        total_salary = sum(p['Salary'] for p in selected_players)
        total_projected = sum(p['FPPG'] for p in selected_players)
        total_actual = sum(p['actual_fppg'] for p in selected_players)
        
        return {
            'filename': 'OPTIMAL_HINDSIGHT',
            'salary': total_salary,
            'projected': total_projected,
            'actual': total_actual,
            'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0,
            'players_list': selected_players
        }
    
    def analyze_leaderboard_performance(self, results):
        """Analyze how each approach compares to FanDuel leaderboard"""
        print("\\n" + "="*80)
        print("LINEUP: DFS APPROACH COMPARISON vs FANDUEL LEADERBOARD")
        print("="*80)
        
        # FanDuel leaderboard benchmarks
        leaderboard_scores = {
            'Tournament_Winner': 210.30,  # 1st place (3-way tie)
            'Top_5': 190.20,              # 5th place
            'Top_10': 179.70,             # 10th place
            'Cash_Line': 150.0            # Estimated cash line
        }
        
        print("\\nDATA: FANDUEL LEADERBOARD BENCHMARKS:")
        for level, score in leaderboard_scores.items():
            print(f"  TARGET: {level}: {score:.1f} FPPG")
        
        print("\\n OUR APPROACHES PERFORMANCE:")
        
        # Sort results by actual performance
        sorted_results = sorted(results.items(), key=lambda x: x[1]['actual'], reverse=True)
        
        for approach_name, result in sorted_results:
            actual_score = result['actual']
            
            # Determine leaderboard position
            if actual_score >= leaderboard_scores['Tournament_Winner']:
                position = " TOURNAMENT WINNER"
                color = ""
            elif actual_score >= leaderboard_scores['Top_5']:
                position = " TOP 5 FINISH"
                color = ""
            elif actual_score >= leaderboard_scores['Top_10']:
                position = " TOP 10 FINISH"
                color = ""
            elif actual_score >= leaderboard_scores['Cash_Line']:
                position = "MONEY: CASH FINISH"
                color = ""
            else:
                position = "ERROR: MISSED CASH"
                color = ""
            
            print(f"\\n{color} {approach_name}:")
            print(f"  MONEY: Salary: ${result['salary']:,}")
            print(f"  PROGRESS: Projected: {result['projected']:.1f} FPPG")
            print(f"  TARGET: Actual: {actual_score:.1f} FPPG")
            print(f"  DATA: Accuracy: {result['accuracy']:.1f}%")
            print(f"  LINEUP: Result: {position}")
            
            # Show distance from tournament win
            win_diff = leaderboard_scores['Tournament_Winner'] - actual_score
            if win_diff > 0:
                print(f"   Gap to Win: -{win_diff:.1f} FPPG")
            else:
                win_surplus = actual_score - leaderboard_scores['Tournament_Winner']
                print(f"   Win Margin: +{win_surplus:.1f} FPPG")
        
        # Performance analysis
        print("\\nTIP: KEY INSIGHTS:")
        
        best_approach = max(results.items(), key=lambda x: x[1]['actual'])
        best_name, best_result = best_approach
        
        print(f"  LINEUP: Best Approach: {best_name} ({best_result['actual']:.1f} FPPG)")
        
        if best_result['actual'] >= leaderboard_scores['Tournament_Winner']:
            print(f"  SUCCESS: TOURNAMENT READY: Our best approach would have WON!")
        elif best_result['actual'] >= leaderboard_scores['Cash_Line']:
            print(f"  MONEY: PROFITABLE: Our best approach would have cashed")
            improvement_needed = leaderboard_scores['Tournament_Winner'] - best_result['actual']
            print(f"  TARGET: Need +{improvement_needed:.1f} FPPG for tournament wins")
        else:
            improvement_needed = leaderboard_scores['Cash_Line'] - best_result['actual']
            print(f"  STEP: Need +{improvement_needed:.1f} FPPG to be profitable")
        
        return best_approach
    
    def detailed_player_analysis(self, best_approach):
        """Analyze the players in our best approach"""
        print("\\n" + "="*80)
        print(f" DETAILED ANALYSIS: {best_approach[0]}")
        print("="*80)
        
        result = best_approach[1]
        
        if 'players' in result:
            players_df = result['players']
        elif 'players_list' in result:
            # Convert list to DataFrame for optimal hindsight
            players_df = pd.DataFrame(result['players_list'])
        else:
            print("No player details available")
            return
        
        print("\\nOWNERSHIP: LINEUP BREAKDOWN:")
        for i, (_, player) in enumerate(players_df.iterrows(), 1):
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player.get('Roster Position', 'N/A')
            salary = player.get('Salary', 0)
            projected = player.get('FPPG', 0)
            actual = player.get('actual_fppg', 0)
            diff = actual - projected
            
            # Performance indicator
            if actual > projected * 1.5:
                indicator = " CEILING"
            elif actual > projected * 1.2:
                indicator = "SUCCESS: EXCEED"
            elif actual >= projected * 0.8:
                indicator = "DATA: SOLID"
            elif actual > 0:
                indicator = "WARNING:  UNDER"
            else:
                indicator = "ERROR: ZERO"
            
            print(f"{i:2}. {indicator} {name:20} ({pos:8}) ${salary:5,} | Proj: {projected:5.1f} | Actual: {actual:5.1f} | Diff: {diff:+6.1f}")
        
        # Summary stats
        total_ceiling = sum(p for p in players_df['actual_fppg'] if p > players_df.loc[players_df['actual_fppg'] == p, 'FPPG'].iloc[0] * 1.2)
        ceiling_players = sum(1 for p in players_df['actual_fppg'] if p > 20)
        
        print(f"\\nPROGRESS: PERFORMANCE SUMMARY:")
        print(f"  TARGET: Players who hit ceiling (20+ FPPG): {ceiling_players}/9")
        print(f"   Total ceiling points: {total_ceiling:.1f}")
        print(f"   Hit rate (scored points): {sum(1 for p in players_df['actual_fppg'] if p > 0)}/9")
    
    def run_comparison(self):
        """Run complete comparison of all DFS approaches"""
        print("START: DFS APPROACH COMPARISON SYSTEM")
        print("Testing all approaches against yesterday's 210+ FPPG leaderboard")
        print("="*80)
        
        # Load data
        merged_data = self.load_test_data()
        
        # Load all lineup approaches
        results = self.load_production_lineups(merged_data)
        
        # Add optimal hindsight
        optimal = self.generate_optimal_hindsight(merged_data)
        if optimal:
            results['Optimal_Hindsight'] = optimal
        
        if not results:
            print("ERROR: No lineup files found to compare")
            return
        
        # Analyze performance vs leaderboard
        best_approach = self.analyze_leaderboard_performance(results)
        
        # Detailed analysis of best approach
        self.detailed_player_analysis(best_approach)
        
        print(f"\\nCOMPLETE: COMPARISON COMPLETE!")
        print(f"DATA: Analyzed {len(results)} different approaches")
        print(f"LINEUP: Best: {best_approach[0]} with {best_approach[1]['actual']:.1f} FPPG")

def main():
    print("DATA: DFS APPROACH COMPARISON")
    print("See how all our approaches stack up against FanDuel's 210+ leaderboard")
    print("="*80)
    
    comparator = DFSApproachComparison()
    
    try:
        comparator.run_comparison()
    except Exception as e:
        print(f"Error in comparison: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
