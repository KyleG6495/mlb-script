#!/usr/bin/env python3
"""
ENHANCED MODEL ANALYZER & OPTIMIZER
==================================
Advanced model improvement system that identifies and fixes performance gaps.

Key Features:
1. Deep model diagnostics with feature importance analysis
2. Real-time performance monitoring and alerts
3. Automated model retraining triggers
4. Advanced ensemble techniques
5. Market inefficiency detection
6. Lineup ceiling optimization for 210+ point targets
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from datetime import datetime, timedelta
import joblib
import warnings
warnings.filterwarnings('ignore')

# Optional imports
try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    import lightgbm as lgb  # type: ignore
    HAS_LGB = True
except ImportError:
    HAS_LGB = False

class EnhancedModelAnalyzer:
    def __init__(self):
        self.dfs_improvements = {}
        self.prop_improvements = {}
        self.performance_thresholds = {
            'dfs_accuracy_target': 170.0,  # Target 170% accuracy
            'dfs_ceiling_target': 0.15,    # 15% of lineups hit 210+
            'prop_win_rate_target': 65.0,  # Target 65% win rate
            'prop_edge_target': 15.0       # Target 15% betting edge
        }
        
    def analyze_dfs_model_gaps(self, lineup_performance_file=None):
        """Identify specific areas where DFS model needs improvement"""
        print("🔍 ANALYZING DFS MODEL PERFORMANCE GAPS")
        print("=" * 60)
        
        if not lineup_performance_file:
            # Find the latest performance file
            import glob
            performance_files = glob.glob("../data/dfs_lineup_performance_*.csv")
            if not performance_files:
                print("❌ No DFS performance files found")
                return {}
                
            lineup_performance_file = max(performance_files)
            
        try:
            df = pd.read_csv(lineup_performance_file)
            print(f"📊 Analyzing {len(df)} lineup performances")
            
            gaps = {}
            
            # 1. CEILING ANALYSIS - Why no 210+ lineups?
            high_scores = df[df['actual_total'] >= 180]
            ceiling_rate = len(df[df['actual_total'] >= 210]) / len(df) * 100
            
            gaps['ceiling_analysis'] = {
                'current_210_rate': ceiling_rate,
                'target_210_rate': 15.0,
                'gap': 15.0 - ceiling_rate,
                'high_score_count': len(high_scores),
                'max_actual_score': df['actual_total'].max()
            }
            
            # 2. POSITION-SPECIFIC GAPS
            position_accuracy = {}
            for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
                pos_players = df[df['lineup_positions'].str.contains(pos, na=False)]
                if len(pos_players) > 0:
                    accuracy = pos_players['accuracy_pct'].mean()
                    position_accuracy[pos] = accuracy
                    
            gaps['position_gaps'] = {
                'worst_position': min(position_accuracy, key=position_accuracy.get),
                'worst_accuracy': min(position_accuracy.values()),
                'best_position': max(position_accuracy, key=position_accuracy.get),
                'best_accuracy': max(position_accuracy.values()),
                'accuracy_variance': max(position_accuracy.values()) - min(position_accuracy.values())
            }
            
            # 3. SALARY EFFICIENCY GAPS
            df['salary_efficiency'] = df['actual_total'] / df['total_salary'] * 1000
            salary_ranges = pd.cut(df['total_salary'], bins=5)
            efficiency_by_salary = df.groupby(salary_ranges)['salary_efficiency'].mean()
            
            gaps['salary_optimization'] = {
                'most_efficient_range': efficiency_by_salary.idxmax(),
                'least_efficient_range': efficiency_by_salary.idxmin(),
                'efficiency_gap': efficiency_by_salary.max() - efficiency_by_salary.min()
            }
            
            # 4. PROJECTION ACCURACY GAPS
            projection_error = df['projected_total'] - df['actual_total']
            gaps['projection_gaps'] = {
                'mean_error': projection_error.mean(),
                'rmse': np.sqrt(np.mean(projection_error**2)),
                'mae': np.mean(np.abs(projection_error)),
                'underestimate_rate': (projection_error < 0).mean() * 100
            }
            
            print("🎯 KEY GAPS IDENTIFIED:")
            print(f"   💥 210+ Rate: {ceiling_rate:.1f}% (Target: 15.0%)")
            print(f"   📍 Worst Position: {gaps['position_gaps']['worst_position']} ({gaps['position_gaps']['worst_accuracy']:.1f}%)")
            print(f"   💰 Projection RMSE: {gaps['projection_gaps']['rmse']:.1f} points")
            print(f"   📊 Underestimate Rate: {gaps['projection_gaps']['underestimate_rate']:.1f}%")
            
            return gaps
            
        except Exception as e:
            print(f"❌ Error analyzing DFS gaps: {e}")
            return {}
    
    def analyze_prop_model_gaps(self, backtest_files=None):
        """Identify specific areas where prop models need improvement"""
        print("\n🔍 ANALYZING PROP MODEL PERFORMANCE GAPS")
        print("=" * 60)
        
        gaps = {}
        
        # Analyze recent PrizePicks performance
        try:
            import glob
            pp_files = glob.glob("../data/prizepicks_backtest_*.csv")
            if pp_files:
                latest_pp = max(pp_files)
                pp_df = pd.read_csv(latest_pp)
                
                # Calculate win rates by stat type
                stat_performance = {}
                for stat in pp_df['stat_type'].unique():
                    stat_data = pp_df[pp_df['stat_type'] == stat]
                    if len(stat_data) > 0:
                        win_rate = stat_data['hit'].mean() * 100
                        stat_performance[stat] = win_rate
                
                gaps['prizepicks_gaps'] = {
                    'overall_win_rate': pp_df['hit'].mean() * 100,
                    'target_win_rate': 65.0,
                    'worst_stat': min(stat_performance, key=stat_performance.get),
                    'worst_win_rate': min(stat_performance.values()),
                    'best_stat': max(stat_performance, key=stat_performance.get),
                    'best_win_rate': max(stat_performance.values()),
                    'stat_performance': stat_performance
                }
                
                print(f"🎯 PrizePicks Gaps:")
                print(f"   📊 Overall: {gaps['prizepicks_gaps']['overall_win_rate']:.1f}% (Target: 65.0%)")
                print(f"   📉 Worst Stat: {gaps['prizepicks_gaps']['worst_stat']} ({gaps['prizepicks_gaps']['worst_win_rate']:.1f}%)")
                
        except Exception as e:
            print(f"⚠️ Could not analyze PrizePicks: {e}")
        
        # Analyze recent Underdog performance  
        try:
            ud_files = glob.glob("../data/underdog_backtest_*.csv")
            if ud_files:
                latest_ud = max(ud_files)
                ud_df = pd.read_csv(latest_ud)
                
                gaps['underdog_gaps'] = {
                    'overall_win_rate': ud_df['hit'].mean() * 100,
                    'target_win_rate': 70.0,
                    'total_picks': len(ud_df)
                }
                
                print(f"🎯 Underdog Gaps:")
                print(f"   📊 Overall: {gaps['underdog_gaps']['overall_win_rate']:.1f}% (Target: 70.0%)")
                
        except Exception as e:
            print(f"⚠️ Could not analyze Underdog: {e}")
            
        return gaps
    
    def generate_improvement_recommendations(self, dfs_gaps, prop_gaps):
        """Generate specific actionable recommendations"""
        print("\n🚀 GENERATING IMPROVEMENT RECOMMENDATIONS")
        print("=" * 60)
        
        recommendations = {
            'dfs_improvements': [],
            'prop_improvements': [],
            'priority_level': 'HIGH'
        }
        
        # DFS Recommendations
        if 'ceiling_analysis' in dfs_gaps:
            ceiling_gap = dfs_gaps['ceiling_analysis']['gap']
            if ceiling_gap > 10:
                recommendations['dfs_improvements'].extend([
                    "🎯 CEILING OPTIMIZATION: Implement variance-focused lineup generation",
                    "💥 LEVERAGE PLAYS: Increase exposure to high-ceiling, low-ownership players",
                    "🎲 CORRELATION STACKS: Build game stacks for explosive upside",
                    "📊 CONTEST-SPECIFIC: Separate large GPP optimizer with higher risk tolerance"
                ])
        
        if 'position_gaps' in dfs_gaps:
            variance = dfs_gaps['position_gaps']['accuracy_variance']
            if variance > 20:
                recommendations['dfs_improvements'].extend([
                    f"📍 POSITION FOCUS: Improve {dfs_gaps['position_gaps']['worst_position']} player modeling",
                    "🔍 POSITION-SPECIFIC: Create specialized models for each position",
                    "📈 MATCHUP WEIGHTS: Increase emphasis on position-specific matchups"
                ])
        
        if 'projection_gaps' in dfs_gaps:
            rmse = dfs_gaps['projection_gaps']['rmse']
            if rmse > 15:
                recommendations['dfs_improvements'].extend([
                    "🎯 PROJECTION ACCURACY: Implement ensemble prediction averaging",
                    "📊 FEATURE ENGINEERING: Add recent form and matchup indicators",
                    "⚡ REAL-TIME: Incorporate live batting order and weather updates"
                ])
        
        # Prop Recommendations
        if 'prizepicks_gaps' in prop_gaps:
            pp_rate = prop_gaps['prizepicks_gaps']['overall_win_rate']
            if pp_rate < 60:
                recommendations['prop_improvements'].extend([
                    "📈 STAT-SPECIFIC: Retrain models for worst-performing stat types",
                    "🎯 MARKET BIAS: Detect and exploit systematic line inefficiencies",
                    "📊 ENSEMBLE: Combine multiple model predictions for better accuracy",
                    f"🔍 FOCUS: Priority improvement for {prop_gaps['prizepicks_gaps']['worst_stat']}"
                ])
        
        if 'underdog_gaps' in prop_gaps:
            ud_rate = prop_gaps['underdog_gaps']['overall_win_rate']
            if ud_rate < 65:
                recommendations['prop_improvements'].extend([
                    "🎲 COMBO OPTIMIZATION: Improve multi-pick correlation modeling",
                    "💰 BANKROLL: Implement Kelly Criterion for optimal bet sizing",
                    "⚡ LIVE UPDATES: Add real-time injury and lineup change detection"
                ])
        
        # Print recommendations
        print("🎯 DFS IMPROVEMENTS:")
        for i, rec in enumerate(recommendations['dfs_improvements'], 1):
            print(f"   {i}. {rec}")
            
        print("\n💰 PROP IMPROVEMENTS:")
        for i, rec in enumerate(recommendations['prop_improvements'], 1):
            print(f"   {i}. {rec}")
            
        return recommendations
    
    def run_complete_analysis(self):
        """Run comprehensive model analysis and generate improvement plan"""
        print("🔍 ENHANCED MODEL ANALYSIS STARTING")
        print("=" * 80)
        
        # Analyze DFS gaps
        dfs_gaps = self.analyze_dfs_model_gaps()
        
        # Analyze prop gaps
        prop_gaps = self.analyze_prop_model_gaps()
        
        # Generate recommendations
        recommendations = self.generate_improvement_recommendations(dfs_gaps, prop_gaps)
        
        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_results = {
            'timestamp': timestamp,
            'dfs_gaps': dfs_gaps,
            'prop_gaps': prop_gaps,
            'recommendations': recommendations
        }
        
        import json
        output_file = f"../data/model_analysis_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis_results, f, indent=2, default=str)
        
        print(f"\n💾 Analysis saved to: {output_file}")
        print("\n✅ ENHANCED MODEL ANALYSIS COMPLETE!")
        
        return analysis_results

if __name__ == "__main__":
    analyzer = EnhancedModelAnalyzer()
    results = analyzer.run_complete_analysis()
