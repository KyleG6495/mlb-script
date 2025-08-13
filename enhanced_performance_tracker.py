#!/usr/bin/env python3
"""
ENHANCED PERFORMANCE BACKTESTING & TRACKING SYSTEM
=================================================

Track model performance over time and optimize betting strategies:
- Historical prediction accuracy tracking
- Win rate analysis by stat type
- ROI calculation for betting recommendations
- Model performance comparison
- Automated model retraining triggers

This helps optimize your betting edge by tracking what's working.
"""

import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceTracker:
    def __init__(self):
        self.performance_history = []
        self.betting_history = []
        self.model_metrics = {}
        
    def load_historical_results(self, results_dir="../data"):
        """Load historical actual results for comparison"""
        logger.info("📊 Loading historical actual results...")
        
        results_files = []
        
        # Look for actual results files
        for file in os.listdir(results_dir):
            if file.startswith('actual_results_') and file.endswith('.csv'):
                results_files.append(file)
        
        if not results_files:
            logger.warning("❌ No actual results files found")
            return pd.DataFrame()
        
        # Load and combine all results
        all_results = []
        for file in results_files:
            try:
                df = pd.read_csv(os.path.join(results_dir, file))
                df['results_date'] = file.replace('actual_results_', '').replace('.csv', '')
                all_results.append(df)
                logger.info(f"✅ Loaded {file}: {len(df)} player results")
            except Exception as e:
                logger.warning(f"❌ Failed to load {file}: {e}")
        
        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            logger.info(f"📈 Total historical results: {len(combined_results)} player-games")
            return combined_results
        else:
            return pd.DataFrame()
    
    def load_historical_predictions(self, predictions_dir="../data"):
        """Load historical predictions for comparison"""
        logger.info("🔮 Loading historical predictions...")
        
        prediction_files = []
        
        # Look for prediction files
        for file in os.listdir(predictions_dir):
            if (file.startswith('enhanced_predictions_') and 
                file.endswith('.csv') and 
                'latest' not in file):
                prediction_files.append(file)
        
        if not prediction_files:
            logger.warning("❌ No historical prediction files found")
            return pd.DataFrame()
        
        # Load recent predictions (last 30 days)
        recent_predictions = []
        for file in sorted(prediction_files)[-30:]:  # Last 30 files
            try:
                df = pd.read_csv(os.path.join(predictions_dir, file))
                # Extract date from filename
                date_str = file.replace('enhanced_predictions_', '').replace('.csv', '')
                df['prediction_date'] = date_str
                recent_predictions.append(df)
                logger.info(f"✅ Loaded {file}: {len(df)} predictions")
            except Exception as e:
                logger.warning(f"❌ Failed to load {file}: {e}")
        
        if recent_predictions:
            combined_predictions = pd.concat(recent_predictions, ignore_index=True)
            logger.info(f"🎯 Total historical predictions: {len(combined_predictions)}")
            return combined_predictions
        else:
            return pd.DataFrame()
    
    def match_predictions_to_results(self, predictions_df, results_df):
        """Match historical predictions to actual results"""
        logger.info("🔍 Matching predictions to actual results...")
        
        matched_data = []
        
        for _, pred_row in predictions_df.iterrows():
            pred_name = pred_row['player_name'].strip().lower()
            pred_date = pred_row.get('prediction_date', '')
            
            # Find matching result
            matching_results = results_df[
                results_df['Name'].str.lower().str.contains(pred_name.split()[0], na=False) &
                results_df['Name'].str.lower().str.contains(pred_name.split()[-1], na=False)
            ]
            
            if not matching_results.empty:
                result_row = matching_results.iloc[0]  # Take first match
                
                matched_record = {
                    'player_name': pred_row['player_name'],
                    'prediction_date': pred_date,
                    'team': pred_row.get('team', ''),
                }
                
                # Match predictions to actual results
                stat_mappings = {
                    'homeRuns_prediction': 'HR',
                    'hits_prediction': 'H',
                    'totalBases_prediction': 'TB', 
                    'runs_prediction': 'R',
                    'rbi_prediction': 'RBI'
                }
                
                for pred_col, result_col in stat_mappings.items():
                    if pred_col in pred_row.index and result_col in result_row.index:
                        prediction = pred_row[pred_col]
                        actual = result_row[result_col]
                        
                        if pd.notna(prediction) and pd.notna(actual):
                            matched_record.update({
                                f'{pred_col}_predicted': prediction,
                                f'{result_col}_actual': actual,
                                f'{pred_col}_error': abs(prediction - actual),
                                f'{pred_col}_accuracy': 1 - abs(prediction - actual) / max(actual, 0.1)
                            })
                
                matched_data.append(matched_record)
        
        if matched_data:
            matched_df = pd.DataFrame(matched_data)
            logger.info(f"✅ Successfully matched {len(matched_df)} prediction-result pairs")
            return matched_df
        else:
            logger.warning("❌ No predictions could be matched to results")
            return pd.DataFrame()
    
    def calculate_model_accuracy_metrics(self, matched_df):
        """Calculate comprehensive accuracy metrics for each stat"""
        logger.info("📊 Calculating model accuracy metrics...")
        
        metrics = {}
        
        stat_types = ['homeRuns', 'hits', 'totalBases', 'runs', 'rbi']
        
        for stat in stat_types:
            pred_col = f'{stat}_prediction_predicted'
            actual_col_mapping = {
                'homeRuns': 'HR_actual',
                'hits': 'H_actual', 
                'totalBases': 'TB_actual',
                'runs': 'R_actual',
                'rbi': 'RBI_actual'
            }
            actual_col = actual_col_mapping[stat]
            
            if pred_col in matched_df.columns and actual_col in matched_df.columns:
                # Filter out NaN values
                valid_data = matched_df[[pred_col, actual_col]].dropna()
                
                if len(valid_data) < 10:
                    logger.warning(f"❌ Insufficient data for {stat}: {len(valid_data)} samples")
                    continue
                
                predictions = valid_data[pred_col].values
                actuals = valid_data[actual_col].values
                
                # Calculate metrics
                mae = np.mean(np.abs(predictions - actuals))
                rmse = np.sqrt(np.mean((predictions - actuals) ** 2))
                
                # R-squared
                ss_res = np.sum((actuals - predictions) ** 2)
                ss_tot = np.sum((actuals - np.mean(actuals)) ** 2)
                r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
                
                # Correlation
                correlation = np.corrcoef(predictions, actuals)[0, 1] if len(predictions) > 1 else 0
                
                # Directional accuracy (for binary events like HR)
                if stat == 'homeRuns':
                    # Check how often we correctly predict HR vs no HR
                    hr_predictions = predictions > 0.5
                    hr_actuals = actuals > 0
                    directional_accuracy = np.mean(hr_predictions == hr_actuals)
                else:
                    directional_accuracy = None
                
                metrics[stat] = {
                    'samples': len(valid_data),
                    'mae': mae,
                    'rmse': rmse,
                    'r2': r2,
                    'correlation': correlation,
                    'mean_prediction': np.mean(predictions),
                    'mean_actual': np.mean(actuals),
                    'directional_accuracy': directional_accuracy
                }
                
                logger.info(f"📈 {stat:12}: MAE={mae:.3f}, R²={r2:.3f}, "
                           f"Correlation={correlation:.3f} ({len(valid_data)} samples)")
        
        return metrics
    
    def analyze_betting_performance(self, matched_df, betting_threshold=5.0):
        """Analyze performance of betting recommendations"""
        logger.info("💰 Analyzing betting performance...")
        
        # Load historical EV opportunities
        ev_files = []
        for file in os.listdir("../data"):
            if file.startswith('enhanced_ev_opportunities_') and file.endswith('.csv'):
                ev_files.append(file)
        
        if not ev_files:
            logger.warning("❌ No historical EV files found")
            return {}
        
        betting_results = []
        
        # Analyze recent EV files
        for file in sorted(ev_files)[-10:]:  # Last 10 files
            try:
                ev_df = pd.read_csv(f"../data/{file}")
                
                # Filter for high-EV bets only
                high_ev_bets = ev_df[ev_df['expected_value'] > betting_threshold]
                
                if high_ev_bets.empty:
                    continue
                
                # Try to match with actual results
                for _, bet in high_ev_bets.iterrows():
                    player_name = bet['player'].lower()
                    bet_stat = bet['stat']
                    bet_line = bet['line']
                    prediction = bet['prediction']
                    expected_value = bet['expected_value']
                    
                    # Find matching actual result
                    matching_results = matched_df[
                        matched_df['player_name'].str.lower().str.contains(player_name.split()[0], na=False)
                    ]
                    
                    if not matching_results.empty:
                        result_row = matching_results.iloc[0]
                        
                        # Map bet stat to actual result
                        stat_to_actual = {
                            'Hits': 'H_actual',
                            'Home Runs': 'HR_actual',
                            'Total Bases': 'TB_actual',
                            'Runs Scored': 'R_actual',
                            'RBIs': 'RBI_actual'
                        }
                        
                        actual_col = stat_to_actual.get(bet_stat)
                        if actual_col and actual_col in result_row.index:
                            actual_value = result_row[actual_col]
                            
                            # Determine if OVER bet won (PrizePicks only allows OVER)
                            bet_won = actual_value > bet_line
                            
                            betting_results.append({
                                'player': bet['player'],
                                'stat': bet_stat,
                                'line': bet_line,
                                'prediction': prediction,
                                'actual': actual_value,
                                'expected_value': expected_value,
                                'bet_won': bet_won,
                                'source': bet.get('source', 'Unknown'),
                                'date': file.replace('enhanced_ev_opportunities_', '').replace('.csv', '')
                            })
            
            except Exception as e:
                logger.warning(f"❌ Failed to process {file}: {e}")
        
        if not betting_results:
            logger.warning("❌ No betting results to analyze")
            return {}
        
        betting_df = pd.DataFrame(betting_results)
        
        # Calculate betting metrics
        total_bets = len(betting_df)
        winning_bets = betting_df['bet_won'].sum()
        win_rate = winning_bets / total_bets
        
        # Simulate ROI (assuming -110 odds)
        stake_per_bet = 100  # $100 per bet
        total_staked = total_bets * stake_per_bet
        total_winnings = winning_bets * (stake_per_bet * 0.909)  # -110 odds payout
        net_profit = total_winnings - total_staked
        roi = net_profit / total_staked * 100
        
        betting_metrics = {
            'total_bets': total_bets,
            'winning_bets': winning_bets,
            'win_rate': win_rate,
            'roi_percent': roi,
            'net_profit_per_100': net_profit / (total_staked / 100),
            'average_ev': betting_df['expected_value'].mean(),
            'breakeven_needed': 52.4  # Break-even win rate for -110 odds
        }
        
        # Analysis by stat type
        stat_performance = betting_df.groupby('stat').agg({
            'bet_won': ['count', 'sum', 'mean'],
            'expected_value': 'mean'
        }).round(3)
        
        logger.info(f"🎯 BETTING PERFORMANCE SUMMARY:")
        logger.info(f"   Total Bets: {total_bets}")
        logger.info(f"   Win Rate: {win_rate:.1%} (Need 52.4% to break even)")
        logger.info(f"   ROI: {roi:+.1f}%")
        logger.info(f"   Net Profit per $100: ${net_profit / (total_staked / 100):+.2f}")
        
        logger.info(f"\n📊 PERFORMANCE BY STAT:")
        for stat in stat_performance.index:
            count = stat_performance.loc[stat, ('bet_won', 'count')]
            wins = stat_performance.loc[stat, ('bet_won', 'sum')]
            rate = stat_performance.loc[stat, ('bet_won', 'mean')]
            avg_ev = stat_performance.loc[stat, ('expected_value', 'mean')]
            logger.info(f"   {stat:12}: {wins}/{count} ({rate:.1%}) - Avg EV: {avg_ev:.1f}%")
        
        return betting_metrics
    
    def generate_performance_report(self, accuracy_metrics, betting_metrics):
        """Generate comprehensive performance report"""
        logger.info("📋 Generating performance report...")
        
        report = {
            'generated_date': datetime.now().isoformat(),
            'model_accuracy': accuracy_metrics,
            'betting_performance': betting_metrics,
            'recommendations': []
        }
        
        # Generate recommendations based on performance
        recommendations = []
        
        # Model accuracy recommendations
        for stat, metrics in accuracy_metrics.items():
            if metrics['r2'] < 0.3:
                recommendations.append(f"⚠️ {stat} model needs improvement (R² = {metrics['r2']:.3f})")
            elif metrics['r2'] > 0.7:
                recommendations.append(f"✅ {stat} model performing well (R² = {metrics['r2']:.3f})")
        
        # Betting performance recommendations
        if betting_metrics:
            if betting_metrics['win_rate'] < 0.52:
                recommendations.append("⚠️ Win rate below break-even - consider higher EV threshold")
            elif betting_metrics['win_rate'] > 0.55:
                recommendations.append("✅ Win rate above break-even - profitable strategy")
            
            if betting_metrics['roi_percent'] < -5:
                recommendations.append("🚨 Negative ROI - review betting strategy")
            elif betting_metrics['roi_percent'] > 5:
                recommendations.append("💰 Positive ROI - successful betting strategy")
        
        report['recommendations'] = recommendations
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"../data/performance_report_{timestamp}.json"
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Also save as latest
        latest_path = "../data/performance_report_latest.json"
        with open(latest_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"✅ Performance report saved to {report_path}")
        
        # Print summary
        logger.info("\n🎉 PERFORMANCE SUMMARY:")
        for rec in recommendations:
            logger.info(f"   {rec}")
        
        return report
    
    def create_performance_visualizations(self, matched_df, accuracy_metrics):
        """Create performance visualization charts"""
        logger.info("📊 Creating performance visualizations...")
        
        try:
            # Set up the plotting style
            plt.style.use('default')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('MLB Prediction Model Performance Analysis', fontsize=16, fontweight='bold')
            
            # 1. Accuracy by Stat Type
            stats = list(accuracy_metrics.keys())
            r2_scores = [accuracy_metrics[stat]['r2'] for stat in stats]
            
            axes[0, 0].bar(stats, r2_scores, color='skyblue', alpha=0.7)
            axes[0, 0].set_title('Model Accuracy by Stat Type (R²)')
            axes[0, 0].set_ylabel('R² Score')
            axes[0, 0].tick_params(axis='x', rotation=45)
            axes[0, 0].axhline(y=0.5, color='red', linestyle='--', alpha=0.5, label='Good Threshold')
            axes[0, 0].legend()
            
            # 2. Prediction vs Actual Scatter (Home Runs)
            if 'homeRuns_prediction_predicted' in matched_df.columns and 'HR_actual' in matched_df.columns:
                hr_data = matched_df[['homeRuns_prediction_predicted', 'HR_actual']].dropna()
                if len(hr_data) > 0:
                    axes[0, 1].scatter(hr_data['homeRuns_prediction_predicted'], hr_data['HR_actual'], 
                                     alpha=0.6, color='orange')
                    axes[0, 1].plot([0, hr_data['HR_actual'].max()], [0, hr_data['HR_actual'].max()], 
                                   'r--', alpha=0.8, label='Perfect Prediction')
                    axes[0, 1].set_title('Home Runs: Predicted vs Actual')
                    axes[0, 1].set_xlabel('Predicted Home Runs')
                    axes[0, 1].set_ylabel('Actual Home Runs')
                    axes[0, 1].legend()
            
            # 3. Error Distribution
            if 'homeRuns_prediction_error' in matched_df.columns:
                error_data = matched_df['homeRuns_prediction_error'].dropna()
                if len(error_data) > 0:
                    axes[1, 0].hist(error_data, bins=20, alpha=0.7, color='lightgreen', edgecolor='black')
                    axes[1, 0].set_title('Home Runs Prediction Error Distribution')
                    axes[1, 0].set_xlabel('Absolute Error')
                    axes[1, 0].set_ylabel('Frequency')
                    axes[1, 0].axvline(error_data.mean(), color='red', linestyle='--', 
                                      label=f'Mean Error: {error_data.mean():.2f}')
                    axes[1, 0].legend()
            
            # 4. Sample Sizes by Stat
            sample_sizes = [accuracy_metrics[stat]['samples'] for stat in stats]
            
            axes[1, 1].bar(stats, sample_sizes, color='lightcoral', alpha=0.7)
            axes[1, 1].set_title('Sample Sizes by Stat Type')
            axes[1, 1].set_ylabel('Number of Samples')
            axes[1, 1].tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # Save visualization
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            viz_path = f"../data/performance_analysis_{timestamp}.png"
            plt.savefig(viz_path, dpi=300, bbox_inches='tight')
            
            logger.info(f"✅ Performance visualization saved to {viz_path}")
            plt.close()
            
        except Exception as e:
            logger.warning(f"❌ Failed to create visualizations: {e}")

def main():
    """Main performance tracking execution"""
    print("📊 ENHANCED PERFORMANCE BACKTESTING & TRACKING")
    print("=" * 55)
    
    tracker = PerformanceTracker()
    
    # Load historical data
    results_df = tracker.load_historical_results()
    predictions_df = tracker.load_historical_predictions()
    
    if results_df.empty or predictions_df.empty:
        print("❌ Insufficient historical data for analysis")
        print("💡 Collect more data by running the system daily and saving actual results")
        return
    
    # Match predictions to results
    matched_df = tracker.match_predictions_to_results(predictions_df, results_df)
    
    if matched_df.empty:
        print("❌ Could not match predictions to results")
        return
    
    # Calculate accuracy metrics
    accuracy_metrics = tracker.calculate_model_accuracy_metrics(matched_df)
    
    # Analyze betting performance
    betting_metrics = tracker.analyze_betting_performance(matched_df)
    
    # Generate comprehensive report
    report = tracker.generate_performance_report(accuracy_metrics, betting_metrics)
    
    # Create visualizations
    tracker.create_performance_visualizations(matched_df, accuracy_metrics)
    
    print(f"\n✅ Performance analysis complete!")
    print(f"📊 Analyzed {len(matched_df)} prediction-result pairs")
    print(f"💾 Reports saved to performance_report_latest.json")

if __name__ == "__main__":
    main()
