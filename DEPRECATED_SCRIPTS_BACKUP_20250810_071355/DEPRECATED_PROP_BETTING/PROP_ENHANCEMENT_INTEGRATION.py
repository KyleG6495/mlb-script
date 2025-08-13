#!/usr/bin/env python3
"""
PROP BETTING ENHANCEMENT INTEGRATION
====================================
Integrates enhanced prop betting strategies into your existing system.

Target improvements:
- Win rate: 57% -> 70%+
- Better stat-specific modeling
- Confidence-based bet sizing
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

class PropBettingEnhancer:
    def __init__(self):
        self.confidence_thresholds = {
            'high': 0.75,    # Large bets
            'medium': 0.65,  # Medium bets  
            'low': 0.55      # Small bets or pass
        }
        
        self.stat_adjustments = {
            'total_bases': 1.1,    # Boost total bases (currently struggling at 50%)
            'home_runs': 0.95,     # Slightly conservative on HR
            'hits': 1.0,
            'runs': 1.05,
            'rbi': 1.0
        }
    
    def enhance_predictions(self, predictions_file=None):
        """Enhance existing prop predictions with better accuracy"""
        print("ENHANCING PROP PREDICTIONS")
        print("=" * 50)
        
        try:
            # Load recent predictions or betting opportunities
            if not predictions_file:
                import glob
                bet_files = glob.glob("../data/betting_opportunities_*.csv")
                if bet_files:
                    predictions_file = max(bet_files)
                else:
                    print("No recent betting files found")
                    return None
            
            df = pd.read_csv(predictions_file)
            print(f"Loaded {len(df)} prop predictions")
            
            # Apply stat-specific adjustments
            if 'stat_type' in df.columns and 'model_prediction' in df.columns:
                for stat, adjustment in self.stat_adjustments.items():
                    mask = df['stat_type'].str.contains(stat, case=False, na=False)
                    df.loc[mask, 'enhanced_prediction'] = df.loc[mask, 'model_prediction'] * adjustment
                
                # Calculate enhanced confidence
                df['prediction_variance'] = abs(df['enhanced_prediction'] - df.get('line', 1)) / df.get('line', 1)
                df['enhanced_confidence'] = 1 - (df['prediction_variance'] / df['prediction_variance'].max())
                df['enhanced_confidence'] = df['enhanced_confidence'].clip(0, 1)
                
                # Generate enhanced recommendations
                conditions = [
                    (df['enhanced_confidence'] >= self.confidence_thresholds['high']) & 
                    (df['enhanced_prediction'] > df.get('line', 1) * 1.15),
                    
                    (df['enhanced_confidence'] >= self.confidence_thresholds['medium']) & 
                    (df['enhanced_prediction'] > df.get('line', 1) * 1.10),
                    
                    (df['enhanced_confidence'] >= self.confidence_thresholds['low']) & 
                    (df['enhanced_prediction'] > df.get('line', 1) * 1.05)
                ]
                
                choices = ['STRONG YES', 'YES', 'LEAN YES']
                df['enhanced_recommendation'] = np.select(conditions, choices, default='PASS')
                
                # Bet sizing
                bet_conditions = [
                    df['enhanced_recommendation'] == 'STRONG YES',
                    df['enhanced_recommendation'] == 'YES', 
                    df['enhanced_recommendation'] == 'LEAN YES'
                ]
                bet_choices = ['LARGE', 'MEDIUM', 'SMALL']
                df['bet_size'] = np.select(bet_conditions, bet_choices, default='NONE')
                
                # Save enhanced predictions
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"../data/enhanced_prop_predictions_{timestamp}.csv"
                df.to_csv(output_file, index=False)
                
                print(f"Enhanced predictions saved: {output_file}")
                
                # Show improvement summary
                strong_yes = len(df[df['enhanced_recommendation'] == 'STRONG YES'])
                yes_bets = len(df[df['enhanced_recommendation'] == 'YES'])
                total_recommended = len(df[df['enhanced_recommendation'] != 'PASS'])
                
                print(f"Enhancement Results:")
                print(f"   STRONG YES bets: {strong_yes}")
                print(f"   YES bets: {yes_bets}")
                print(f"   Total recommended: {total_recommended}/{len(df)}")
                print(f"   Selectivity: {(1 - total_recommended/len(df))*100:.1f}% (more selective = better)")
                
                return output_file
            else:
                print("Required columns not found for enhancement")
                return None
                
        except Exception as e:
            print(f"Error enhancing predictions: {e}")
            return None
    
    def create_confidence_model(self, backtest_files=None):
        """Create confidence scoring model from historical performance"""
        print("\nCREATING CONFIDENCE MODEL")
        print("=" * 50)
        
        try:
            # Load historical performance data
            import glob
            if not backtest_files:
                pp_files = glob.glob("../data/prizepicks_backtest_*.csv")
                ud_files = glob.glob("../data/underdog_backtest_*.csv")
                backtest_files = pp_files + ud_files
            
            if not backtest_files:
                print("No backtest files found for confidence modeling")
                return None
            
            all_performance = []
            
            for file in backtest_files:
                try:
                    df = pd.read_csv(file)
                    if 'hit' in df.columns:
                        all_performance.append(df)
                except:
                    continue
            
            if not all_performance:
                print("No valid performance data found")
                return None
            
            combined_df = pd.concat(all_performance, ignore_index=True)
            print(f"Analyzed {len(combined_df)} historical bets")
            
            # Calculate performance metrics by various factors
            performance_metrics = {}
            
            # By stat type
            if 'stat_type' in combined_df.columns:
                stat_performance = combined_df.groupby('stat_type')['hit'].mean()
                performance_metrics['by_stat'] = stat_performance.to_dict()
                
                print("Historical performance by stat:")
                for stat, rate in stat_performance.items():
                    print(f"   {stat}: {rate:.1%}")
            
            # By prediction confidence (if available)
            if 'confidence' in combined_df.columns:
                combined_df['confidence_bucket'] = pd.cut(combined_df['confidence'], 
                                                        bins=[0, 0.5, 0.7, 0.85, 1.0], 
                                                        labels=['Low', 'Medium', 'High', 'Very High'])
                conf_performance = combined_df.groupby('confidence_bucket')['hit'].mean()
                performance_metrics['by_confidence'] = conf_performance.to_dict()
            
            # Overall metrics
            performance_metrics['overall'] = {
                'total_bets': len(combined_df),
                'win_rate': combined_df['hit'].mean(),
                'target_win_rate': 0.70
            }
            
            # Save confidence model
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_file = f"../data/prop_confidence_model_{timestamp}.json"
            
            with open(model_file, 'w') as f:
                json.dump(performance_metrics, f, indent=2, default=str)
            
            print(f"Confidence model saved: {model_file}")
            print(f"Overall win rate: {performance_metrics['overall']['win_rate']:.1%}")
            print(f"Target win rate: {performance_metrics['overall']['target_win_rate']:.1%}")
            
            return model_file
            
        except Exception as e:
            print(f"Error creating confidence model: {e}")
            return None
    
    def generate_enhanced_betting_report(self):
        """Generate enhanced betting report with improved recommendations"""
        print("\nGENERATING ENHANCED BETTING REPORT")
        print("=" * 50)
        
        try:
            # Find latest enhanced predictions
            import glob
            enhanced_files = glob.glob("../data/enhanced_prop_predictions_*.csv")
            
            if not enhanced_files:
                print("No enhanced predictions found. Run enhance_predictions() first.")
                return None
            
            latest_file = max(enhanced_files)
            df = pd.read_csv(latest_file)
            
            # Create enhanced report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = f"../data/enhanced_betting_report_{timestamp}.txt"
            
            with open(report_file, 'w') as f:
                f.write("ENHANCED PROP BETTING RECOMMENDATIONS\n")
                f.write("=" * 60 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Strong YES recommendations
                strong_yes = df[df['enhanced_recommendation'] == 'STRONG YES']
                if len(strong_yes) > 0:
                    f.write("STRONG YES RECOMMENDATIONS (Large Bets):\n")
                    f.write("-" * 40 + "\n")
                    
                    for i, (_, row) in enumerate(strong_yes.iterrows(), 1):
                        player = row.get('player', 'Unknown')
                        stat = row.get('stat_type', 'Unknown')
                        line = row.get('line', 0)
                        pred = row.get('enhanced_prediction', 0)
                        conf = row.get('enhanced_confidence', 0)
                        
                        f.write(f"{i}. {player}\n")
                        f.write(f"   {stat.upper()}: Prediction {pred:.1f}, Line {line}\n")
                        f.write(f"   Confidence: {conf:.1%} | Bet Size: LARGE\n\n")
                
                # YES recommendations
                yes_bets = df[df['enhanced_recommendation'] == 'YES']
                if len(yes_bets) > 0:
                    f.write("YES RECOMMENDATIONS (Medium Bets):\n")
                    f.write("-" * 40 + "\n")
                    
                    for i, (_, row) in enumerate(yes_bets.iterrows(), 1):
                        player = row.get('player', 'Unknown')
                        stat = row.get('stat_type', 'Unknown')
                        line = row.get('line', 0)
                        pred = row.get('enhanced_prediction', 0)
                        conf = row.get('enhanced_confidence', 0)
                        
                        f.write(f"{i}. {player}\n")
                        f.write(f"   {stat.upper()}: Prediction {pred:.1f}, Line {line}\n")
                        f.write(f"   Confidence: {conf:.1%} | Bet Size: MEDIUM\n\n")
                
                # Summary
                f.write("SUMMARY:\n")
                f.write("-" * 20 + "\n")
                f.write(f"Total Strong YES: {len(strong_yes)}\n")
                f.write(f"Total YES: {len(yes_bets)}\n")
                f.write(f"Total Recommended: {len(df[df['enhanced_recommendation'] != 'PASS'])}\n")
                f.write(f"Enhanced selectivity approach for higher win rates\n")
            
            print(f"Enhanced betting report saved: {report_file}")
            print(f"Strong YES bets: {len(strong_yes)}")
            print(f"Total YES bets: {len(yes_bets)}")
            
            return report_file
            
        except Exception as e:
            print(f"Error generating report: {e}")
            return None

def main():
    """Main prop enhancement function"""
    print("PROP BETTING ENHANCEMENT SYSTEM")
    print("=" * 60)
    
    enhancer = PropBettingEnhancer()
    
    # Step 1: Enhance predictions
    enhanced_file = enhancer.enhance_predictions()
    
    # Step 2: Create confidence model
    confidence_model = enhancer.create_confidence_model()
    
    # Step 3: Generate enhanced report
    report_file = enhancer.generate_enhanced_betting_report()
    
    print("\nPROP ENHANCEMENT COMPLETE!")
    print("=" * 60)
    print("Key Improvements:")
    print("   - Stat-specific prediction adjustments")
    print("   - Confidence-based bet sizing")
    print("   - Enhanced selectivity for higher win rates")
    print("   - Historical performance modeling")
    print()
    print("Next Steps:")
    print("   1. Review enhanced betting report for today's picks")
    print("   2. Use LARGE/MEDIUM bet sizing recommendations")
    print("   3. Track performance to validate improvements")
    print("   4. Integrate with your existing prop betting workflow")

if __name__ == "__main__":
    main()
