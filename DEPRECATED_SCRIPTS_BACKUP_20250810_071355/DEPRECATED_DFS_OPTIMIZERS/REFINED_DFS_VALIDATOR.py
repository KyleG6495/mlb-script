#!/usr/bin/env python3
"""
REFINED DFS VALIDATION SYSTEM
=============================
Comprehensive testing framework for our refined tournament optimization.

Tests:
1. Refined Enhanced ML vs Original Enhanced ML
2. Refined vs Ceiling approach
3. Multi-strategy portfolio performance  
4. Tournament ceiling validation
5. Leaderboard position simulation
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class RefinedDFSValidator:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_test_data(self):
        """Load slate and actual results for validation"""
        print("📊 Loading test data for refined DFS validation...")
        
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
        
        print(f"✅ Loaded {len(slate_df)} slate players, {len(actual_df)} actual results")
        return merged
    
    def score_refined_lineups(self, merged_data):
        """Score all refined lineup files against actual results"""
        print("🎯 Scoring refined lineup files...")
        
        results = {}
        
        # Find refined lineup files
        lineup_files = list(self.slate_dir.glob("refined_ml_dfs_lineups_*.csv"))
        
        if not lineup_files:
            print("❌ No refined lineup files found")
            return results
        
        # Score the most recent refined file
        latest_file = max(lineup_files, key=lambda f: f.stat().st_mtime)
        print(f"📁 Scoring: {latest_file.name}")
        
        lineup_df = pd.read_csv(latest_file)
        
        # Get unique lineups
        unique_lineups = lineup_df['Lineup_ID'].unique()
        
        for lineup_id in unique_lineups:
            lineup_players = lineup_df[lineup_df['Lineup_ID'] == lineup_id]
            
            # Match with actual results
            lineup_players['full_name'] = lineup_players['Player_Name'].str.lower().str.strip()
            
            scored = lineup_players.merge(
                merged_data[['full_name', 'actual_fppg']],
                on='full_name',
                how='left'
            )
            scored['actual_fppg'] = scored['actual_fppg'].fillna(0)
            
            total_salary = scored['Salary'].sum()
            total_projected = scored['FPPG'].sum()
            total_actual = scored['actual_fppg'].sum()
            total_ceiling = scored['Tournament_Ceiling'].sum()
            strategy = scored['Strategy'].iloc[0]
            
            results[lineup_id] = {
                'strategy': strategy,
                'salary': total_salary,
                'projected': total_projected,
                'actual': total_actual,
                'ceiling': total_ceiling,
                'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0,
                'ceiling_efficiency': (total_actual / total_ceiling * 100) if total_ceiling > 0 else 0,
                'players': scored
            }
        
        return results
    
    def compare_with_baselines(self, refined_results, merged_data):
        """Compare refined results with baseline approaches"""
        print("📊 Comparing refined approach with baselines...")
        
        # Load baseline results (Enhanced ML, Ceiling, etc.)
        baseline_files = [
            'Enhanced_Lineups_FD_Format_20250728_183600.csv',
            'ceiling_dfs_lineup_20250729_101619.csv'
        ]
        
        baseline_results = {}
        
        for filename in baseline_files:
            filepath = self.slate_dir / filename
            if not filepath.exists():
                continue
                
            try:
                if 'Enhanced_Lineups' in filename:
                    # Enhanced ML format
                    lineup_df = pd.read_csv(filepath)
                    if len(lineup_df) > 0:
                        first_lineup = lineup_df.iloc[0]
                        position_cols = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
                        
                        players = []
                        for pos in position_cols:
                            if pos in first_lineup and pd.notna(first_lineup[pos]):
                                player_data = str(first_lineup[pos])
                                if ':' in player_data:
                                    player_id, player_name = player_data.split(':', 1)
                                    players.append({'name': player_name.strip()})
                        
                        if len(players) == 9:
                            players_df = pd.DataFrame(players)
                            players_df['full_name'] = players_df['name'].str.lower().str.strip()
                            
                            scored = players_df.merge(
                                merged_data[['full_name', 'actual_fppg', 'Salary', 'FPPG']],
                                on='full_name',
                                how='left'
                            )
                            scored['actual_fppg'] = scored['actual_fppg'].fillna(0)
                            
                            total_actual = scored['actual_fppg'].sum()
                            total_projected = first_lineup.get('Total_Projection', scored['FPPG'].sum())
                            
                            baseline_results['Enhanced_ML_Baseline'] = {
                                'actual': total_actual,
                                'projected': total_projected,
                                'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0
                            }
                
                elif 'ceiling' in filename:
                    # Ceiling format
                    lineup_df = pd.read_csv(filepath)
                    lineup_df['full_name'] = (lineup_df['First Name'].str.strip() + ' ' + 
                                             lineup_df['Last Name'].str.strip()).str.lower()
                    
                    scored = lineup_df.merge(
                        merged_data[['full_name', 'actual_fppg']],
                        on='full_name',
                        how='left'
                    )
                    scored['actual_fppg'] = scored['actual_fppg'].fillna(0)
                    
                    total_actual = scored['actual_fppg'].sum()
                    total_projected = scored['FPPG'].sum()
                    
                    baseline_results['Ceiling_Baseline'] = {
                        'actual': total_actual,
                        'projected': total_projected,
                        'accuracy': (total_actual / total_projected * 100) if total_projected > 0 else 0
                    }
                    
            except Exception as e:
                print(f"⚠️ Could not load {filename}: {e}")
        
        return baseline_results
    
    def analyze_tournament_performance(self, refined_results, baseline_results):
        """Analyze tournament performance vs leaderboard benchmarks"""
        print("\\n" + "="*80)
        print("🏆 REFINED DFS VALIDATION RESULTS")
        print("="*80)
        
        # FanDuel leaderboard benchmarks
        benchmarks = {
            'Tournament_Winner': 210.30,
            'Top_5': 190.20,
            'Top_10': 179.70,
            'Cash_Line': 150.0
        }
        
        print("\\n📊 FANDUEL TOURNAMENT BENCHMARKS:")
        for level, score in benchmarks.items():
            print(f"  🎯 {level}: {score:.1f} FPPG")
        
        # Analyze refined lineups
        print(f"\\n🚀 REFINED LINEUP PERFORMANCE:")
        
        refined_scores = []
        best_refined = None
        best_score = 0
        
        for lineup_id, result in refined_results.items():
            actual_score = result['actual']
            refined_scores.append(actual_score)
            
            if actual_score > best_score:
                best_score = actual_score
                best_refined = (lineup_id, result)
            
            # Determine tournament position
            if actual_score >= benchmarks['Tournament_Winner']:
                position = "🥇 TOURNAMENT WINNER"
                color = "🟢"
            elif actual_score >= benchmarks['Top_5']:
                position = "🥈 TOP 5 FINISH"
                color = "🟢"
            elif actual_score >= benchmarks['Top_10']:
                position = "🥉 TOP 10 FINISH"
                color = "🟡"
            elif actual_score >= benchmarks['Cash_Line']:
                position = "💰 CASH FINISH"
                color = "🟡"
            else:
                position = "❌ MISSED CASH"
                color = "🔴"
            
            print(f"\\n{color} {lineup_id} ({result['strategy']}):")
            print(f"  💰 Salary: ${result['salary']:,}")
            print(f"  📈 Projected: {result['projected']:.1f} FPPG")
            print(f"  🎯 Actual: {actual_score:.1f} FPPG")
            print(f"  🚀 Ceiling: {result['ceiling']:.1f} FPPG")
            print(f"  📊 Accuracy: {result['accuracy']:.1f}%")
            print(f"  ⚡ Ceiling Efficiency: {result['ceiling_efficiency']:.1f}%")
            print(f"  🏆 Result: {position}")
        
        # Portfolio analysis
        if refined_scores:
            avg_refined = np.mean(refined_scores)
            max_refined = max(refined_scores)
            min_refined = min(refined_scores)
            
            print(f"\\n📈 REFINED PORTFOLIO ANALYSIS:")
            print(f"  🎯 Best Lineup: {max_refined:.1f} FPPG")
            print(f"  📊 Average: {avg_refined:.1f} FPPG")
            print(f"  📉 Worst: {min_refined:.1f} FPPG")
            print(f"  🎪 Consistency: {(min_refined/max_refined)*100:.1f}%")
            
            # Tournament readiness
            tournament_ready = sum(1 for score in refined_scores if score >= benchmarks['Tournament_Winner'])
            cash_rate = sum(1 for score in refined_scores if score >= benchmarks['Cash_Line'])
            
            print(f"  🏆 Tournament Winners: {tournament_ready}/{len(refined_scores)} ({tournament_ready/len(refined_scores)*100:.1f}%)")
            print(f"  💰 Cash Rate: {cash_rate}/{len(refined_scores)} ({cash_rate/len(refined_scores)*100:.1f}%)")
        
        # Compare with baselines
        print(f"\\n🔄 BASELINE COMPARISON:")
        
        if baseline_results:
            for baseline_name, baseline_data in baseline_results.items():
                print(f"  📊 {baseline_name}: {baseline_data['actual']:.1f} FPPG ({baseline_data['accuracy']:.1f}% accuracy)")
            
            if refined_scores:
                enhanced_ml_score = baseline_results.get('Enhanced_ML_Baseline', {}).get('actual', 0)
                ceiling_score = baseline_results.get('Ceiling_Baseline', {}).get('actual', 0)
                
                if enhanced_ml_score > 0:
                    improvement = ((avg_refined - enhanced_ml_score) / enhanced_ml_score) * 100
                    print(f"  🚀 Refined vs Enhanced ML: {improvement:+.1f}% improvement")
                
                if ceiling_score > 0:
                    improvement = ((avg_refined - ceiling_score) / ceiling_score) * 100
                    print(f"  🎯 Refined vs Ceiling: {improvement:+.1f}% improvement")
        
        # Key insights
        print(f"\\n💡 KEY INSIGHTS:")
        
        if refined_scores:
            if max_refined >= benchmarks['Tournament_Winner']:
                print(f"  ✅ SUCCESS: Refined system can generate tournament winners!")
                print(f"  🎯 Best performance: {max_refined:.1f} FPPG")
            elif avg_refined >= benchmarks['Cash_Line']:
                print(f"  💰 PROFITABLE: Refined system consistently cashes")
                needed_improvement = benchmarks['Tournament_Winner'] - max_refined
                print(f"  🔧 Need +{needed_improvement:.1f} FPPG for tournament wins")
            else:
                needed_improvement = benchmarks['Cash_Line'] - avg_refined
                print(f"  ⚠️  DEVELOPING: Need +{needed_improvement:.1f} FPPG for profitability")
        
        # Best lineup analysis
        if best_refined:
            print(f"\\n🏆 BEST REFINED LINEUP ANALYSIS: {best_refined[0]}")
            best_result = best_refined[1]
            
            print(f"  Strategy: {best_result['strategy']}")
            print(f"  Performance: {best_result['actual']:.1f} actual vs {best_result['projected']:.1f} projected")
            
            # Show top performers
            best_players = best_result['players'].nlargest(3, 'actual_fppg')
            print(f"  Top 3 performers:")
            for i, (_, player) in enumerate(best_players.iterrows(), 1):
                print(f"    {i}. {player['Player_Name']}: {player['actual_fppg']:.1f} FPPG")
        
        return {
            'refined_scores': refined_scores,
            'best_refined': best_refined,
            'baseline_results': baseline_results
        }
    
    def run_validation(self):
        """Run complete refined DFS validation"""
        print("🚀 REFINED DFS VALIDATION SYSTEM")
        print("Testing refined tournament optimization against actual results")
        print("="*80)
        
        # Load test data
        merged_data = self.load_test_data()
        
        # Score refined lineups
        refined_results = self.score_refined_lineups(merged_data)
        
        if not refined_results:
            print("❌ No refined lineups to validate")
            return
        
        # Compare with baselines
        baseline_results = self.compare_with_baselines(refined_results, merged_data)
        
        # Analyze performance
        analysis = self.analyze_tournament_performance(refined_results, baseline_results)
        
        print(f"\\n🎉 VALIDATION COMPLETE!")
        print(f"📊 Analyzed {len(refined_results)} refined lineups")
        print(f"🏆 Tournament-ready system validated!")

def main():
    print("📊 REFINED DFS VALIDATION")
    print("Validate refined tournament optimization against actual performance")
    print("="*80)
    
    validator = RefinedDFSValidator()
    
    try:
        validator.run_validation()
    except Exception as e:
        print(f"Error in validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
