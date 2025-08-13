"""
🔥🔥 ULTIMATE ENSEMBLE-POWERED BETTING SYSTEM 🔥🔥
Integration of advanced ensemble learning with sophisticated betting analytics
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional
from advanced_ensemble_system import AdvancedEnsembleBettingSystem
from supercharged_betting_system import SuperchargedBettingSystem
from automated_betting_system import AutomatedBettingSystem

class UltimateEnsembleBettingSystem:
    """The most advanced betting system combining ensemble learning with betting analytics"""
    
    def __init__(self):
        self.ensemble_system = AdvancedEnsembleBettingSystem()
        self.betting_system = AutomatedBettingSystem()
        self.prediction_quality_tracker = {}
        self.ensemble_performance_log = []
        
    def load_ensemble_predictions(self, timestamp: str = None) -> Dict:
        """Load the latest ensemble predictions"""
        
        ensemble_dir = Path("./ensemble_predictions")
        
        if not ensemble_dir.exists():
            logging.error("❌ No ensemble predictions found")
            return {}
        
        # Find the latest predictions if no timestamp specified
        if timestamp is None:
            pred_files = list(ensemble_dir.glob("*_ensemble_*.csv"))
            if not pred_files:
                logging.error("❌ No ensemble prediction files found")
                return {}
            
            # Get the most recent timestamp
            timestamps = [f.name.split('_')[-1].replace('.csv', '') for f in pred_files]
            timestamp = max(timestamps)
        
        # Load predictions for each category
        predictions = {}
        categories = ['hits', 'total_bases', 'runs', 'rbi', 'home_runs', 
                     'hitter_strikeouts', 'stolen_bases', 'hrr', 'pitcher_strikeouts']
        
        for category in categories:
            file_path = ensemble_dir / f"{category}_ensemble_{timestamp}.csv"
            if file_path.exists():
                df = pd.read_csv(file_path)
                predictions[category] = df
                logging.info(f"📊 Loaded ensemble {category}: {len(df)} predictions")
        
        return predictions
    
    def enhance_ensemble_predictions(self, ensemble_predictions: Dict) -> Dict:
        """Enhance ensemble predictions with additional analytics"""
        
        enhanced_predictions = {}
        
        for category, pred_df in ensemble_predictions.items():
            enhanced_df = pred_df.copy()
            
            # Add prediction quality metrics
            enhanced_df['prediction_quality'] = self._assess_prediction_quality(
                enhanced_df[f'predicted_{category}'], category
            )
            
            # Add ensemble strength score
            if 'ensemble_confidence' in enhanced_df.columns and 'model_agreement' in enhanced_df.columns:
                enhanced_df['ensemble_strength'] = (
                    enhanced_df['ensemble_confidence'] * 0.6 + 
                    enhanced_df['model_agreement'] * 0.4
                )
            else:
                enhanced_df['ensemble_strength'] = 0.7  # Default
            
            # Add volatility assessment
            enhanced_df['prediction_volatility'] = self._calculate_prediction_volatility(
                enhanced_df[f'predicted_{category}']
            )
            
            # Add market timing score
            enhanced_df['market_timing_score'] = self._calculate_market_timing_score(category)
            
            enhanced_predictions[category] = enhanced_df
            
        return enhanced_predictions
    
    def _assess_prediction_quality(self, predictions: pd.Series, category: str) -> pd.Series:
        """Assess the quality of predictions for a category"""
        
        # Quality factors:
        # 1. Realistic range
        # 2. Appropriate distribution
        # 3. No extreme outliers
        
        baselines = {
            'hits': {'min': 0, 'max': 5, 'mean': 1.15},
            'total_bases': {'min': 0, 'max': 8, 'mean': 1.75},
            'runs': {'min': 0, 'max': 4, 'mean': 0.65},
            'rbi': {'min': 0, 'max': 6, 'mean': 0.60},
            'home_runs': {'min': 0, 'max': 3, 'mean': 0.12},
            'hitter_strikeouts': {'min': 0, 'max': 4, 'mean': 0.95},
            'pitcher_strikeouts': {'min': 0, 'max': 15, 'mean': 6.2},
            'stolen_bases': {'min': 0, 'max': 3, 'mean': 0.08},
            'hrr': {'min': 0, 'max': 8, 'mean': 1.9}
        }
        
        baseline = baselines.get(category, {'min': 0, 'max': 10, 'mean': 1.0})
        
        # Check if predictions are in reasonable range
        in_range = ((predictions >= baseline['min'] - 0.5) & 
                   (predictions <= baseline['max'] + 1.0)).astype(float)
        
        # Check how close predictions are to expected mean
        distance_from_mean = np.abs(predictions - baseline['mean']) / baseline['mean']
        mean_quality = np.exp(-distance_from_mean)  # Exponential decay from mean
        
        # Combined quality score
        quality = (in_range * 0.6 + mean_quality * 0.4)
        
        return quality
    
    def _calculate_prediction_volatility(self, predictions: pd.Series) -> pd.Series:
        """Calculate prediction volatility (lower is more stable)"""
        
        # Use rolling standard deviation as volatility measure
        volatility = np.abs(predictions - predictions.median()) / (predictions.std() + 1e-6)
        
        # Normalize to 0-1 scale (lower is better)
        volatility = np.clip(1.0 - volatility / (volatility.max() + 1e-6), 0, 1)
        
        return volatility
    
    def _calculate_market_timing_score(self, category: str) -> float:
        """Calculate market timing score based on category and current conditions"""
        
        # Time-based factors
        hour = datetime.now().hour
        
        # Categories perform better at different times
        timing_preferences = {
            'hits': {'peak_hours': [19, 20, 21], 'score': 0.8},
            'home_runs': {'peak_hours': [20, 21, 22], 'score': 0.9},
            'pitcher_strikeouts': {'peak_hours': [18, 19, 20], 'score': 0.85},
            'stolen_bases': {'peak_hours': [19, 20], 'score': 0.7}
        }
        
        pref = timing_preferences.get(category, {'peak_hours': [19, 20], 'score': 0.75})
        
        if hour in pref['peak_hours']:
            return pref['score']
        else:
            return pref['score'] * 0.8  # Reduced score for off-peak
    
    def find_ensemble_opportunities(self, enhanced_predictions: Dict, min_edge: float = 0.05) -> List[Dict]:
        """Find betting opportunities using ensemble predictions"""
        
        # Load sportsbook lines
        lines = self.betting_system.load_sportsbook_lines()
        
        if not lines:
            logging.error("❌ No sportsbook lines loaded")
            return []
        
        opportunities = []
        
        # Process each category
        for category, pred_df in enhanced_predictions.items():
            category_opportunities = self._find_category_opportunities(
                category, pred_df, lines, min_edge
            )
            opportunities.extend(category_opportunities)
        
        # Sort by ensemble-adjusted edge
        opportunities.sort(key=lambda x: x.get('ensemble_adjusted_edge', 0), reverse=True)
        
        logging.info(f"🎯 Found {len(opportunities)} ensemble opportunities")
        return opportunities
    
    def _find_category_opportunities(self, category: str, pred_df: pd.DataFrame, 
                                   lines: Dict, min_edge: float) -> List[Dict]:
        """Find opportunities for a specific category"""
        
        opportunities = []
        
        # Stat mapping for sportsbooks
        stat_mapping = {
            'hitter_strikeouts': ['Batter Strikeouts', 'Hitter Strikeouts', 'strikeouts'],
            'pitcher_strikeouts': ['Pitcher Strikeouts', 'Strikeouts'],
            'hits': ['Hits', 'hits'],
            'total_bases': ['Total Bases', 'total_bases'],
            'runs': ['Runs', 'runs'], 
            'rbi': ['RBIs', 'rbi'],
            'home_runs': ['Home Runs', 'home_runs'],
            'stolen_bases': ['Stolen Bases', 'stolen_bases'],
            'hrr': ['H+R+RBI', 'hrr']
        }
        
        if category not in stat_mapping:
            return opportunities
        
        stat_names = stat_mapping[category]
        
        # Process each player prediction
        for _, pred_row in pred_df.iterrows():
            player_name = pred_row['name']
            prediction = pred_row[f'predicted_{category}']
            ensemble_confidence = pred_row.get('ensemble_confidence', 0.5)
            ensemble_strength = pred_row.get('ensemble_strength', 0.7)
            prediction_quality = pred_row.get('prediction_quality', 0.7)
            
            # Skip low-quality predictions
            if prediction_quality < 0.3:
                continue
            
            # Search all sportsbooks
            for source, line_df in lines.items():
                matching_lines = self._find_matching_lines(
                    player_name, stat_names, source, line_df, category
                )
                
                for line_row in matching_lines:
                    opp = self._calculate_ensemble_opportunity(
                        player_name, category, prediction, line_row, source,
                        ensemble_confidence, ensemble_strength, prediction_quality
                    )
                    
                    if opp and opp['ensemble_adjusted_edge'] >= min_edge:
                        opportunities.append(opp)
        
        return opportunities
    
    def _find_matching_lines(self, player_name: str, stat_names: List[str], 
                           source: str, line_df: pd.DataFrame, category: str) -> List[Dict]:
        """Find matching lines for a player/stat combination"""
        
        matching_lines = []
        
        if source == 'prizepicks':
            # Skip home runs for PrizePicks (OVER only)
            if category == 'home_runs':
                return matching_lines
                
            for stat_name in stat_names:
                matches = line_df[
                    (line_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                    (line_df['variable'] == stat_name)
                ]
                matching_lines.extend(matches.to_dict('records'))
        
        elif source == 'underdog':
            for stat_name in stat_names:
                matches = line_df[
                    (line_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                    (line_df['stat_type'] == stat_name)
                ]
                matching_lines.extend(matches.to_dict('records'))
        
        return matching_lines
    
    def _calculate_ensemble_opportunity(self, player: str, category: str, prediction: float,
                                      line_row: Dict, source: str, ensemble_confidence: float,
                                      ensemble_strength: float, prediction_quality: float) -> Optional[Dict]:
        """Calculate betting opportunity with ensemble enhancements"""
        
        line_value = line_row['line']
        odds = line_row.get('odds', -110)
        
        # Calculate model probability using normal distribution
        if category in ['pitcher_strikeouts', 'hitter_strikeouts']:
            std_dev = max(1.5, prediction * 0.35)
        elif category in ['hits', 'runs', 'rbi']:
            std_dev = max(1.0, prediction * 0.4)
        elif category == 'total_bases':
            std_dev = max(1.5, prediction * 0.35)
        elif category == 'home_runs':
            std_dev = max(0.5, prediction * 0.5)
        else:
            std_dev = max(1.0, prediction * 0.3)
        
        from scipy import stats
        model_prob_over = 1 - stats.norm.cdf(line_value, loc=prediction, scale=std_dev)
        model_prob_over = max(0.01, min(0.99, model_prob_over))
        
        # Calculate implied probability from odds
        if odds > 0:
            implied_prob = 100 / (odds + 100)
        else:
            implied_prob = abs(odds) / (abs(odds) + 100)
        
        # Calculate expected values
        if model_prob_over > implied_prob:
            win_prob = model_prob_over
            payout = 1 / implied_prob - 1
            ev_over = (win_prob * payout) - ((1 - win_prob) * 1)
        else:
            ev_over = 0
        
        if (1 - model_prob_over) > (1 - implied_prob):
            win_prob = 1 - model_prob_over
            payout = 1 / (1 - implied_prob) - 1
            ev_under = (win_prob * payout) - ((1 - win_prob) * 1)
        else:
            ev_under = 0
        
        # Determine best bet
        if ev_over > ev_under and ev_over > 0.01:
            recommended_bet = 'OVER'
            edge = ev_over
        elif ev_under > 0.01:
            recommended_bet = 'UNDER'
            edge = ev_under
        else:
            return None
        
        # Ensemble adjustments
        ensemble_adjusted_edge = edge * ensemble_strength * prediction_quality
        
        # Calculate Kelly sizing with ensemble factors
        win_prob = model_prob_over if recommended_bet == 'OVER' else (1 - model_prob_over)
        if edge > 0 and win_prob > 0:
            kelly_full = (win_prob * (1 + edge) - 1) / edge
            kelly_quarter = kelly_full * 0.25 * ensemble_confidence  # Adjust by confidence
        else:
            kelly_full = kelly_quarter = 0
        
        return {
            'player': player,
            'category': category,
            'source': source,
            'line': line_value,
            'prediction': prediction,
            'model_prob_over': model_prob_over,
            'implied_prob': implied_prob,
            'recommended_bet': recommended_bet,
            'expected_value': edge,
            'edge': edge,
            'ensemble_confidence': ensemble_confidence,
            'ensemble_strength': ensemble_strength,
            'prediction_quality': prediction_quality,
            'ensemble_adjusted_edge': ensemble_adjusted_edge,
            'kelly_full': max(0, kelly_full),
            'kelly_quarter': max(0, kelly_quarter),
            'confidence_level': self._get_confidence_level(ensemble_adjusted_edge),
            'odds': odds
        }
    
    def _get_confidence_level(self, edge: float) -> str:
        """Determine confidence level based on ensemble-adjusted edge"""
        if edge >= 0.20:
            return 'ELITE'
        elif edge >= 0.15:
            return 'VERY_HIGH'
        elif edge >= 0.10:
            return 'HIGH'
        elif edge >= 0.05:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def generate_ultimate_report(self, opportunities: List[Dict]) -> str:
        """Generate comprehensive ensemble betting report"""
        
        if not opportunities:
            return "❌ No opportunities found"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed CSV
        df = pd.DataFrame(opportunities)
        csv_file = f"./betting_analysis/ultimate_ensemble_opportunities_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        
        # Generate comprehensive report
        report = []
        report.append("🔥🔥 ULTIMATE ENSEMBLE BETTING SYSTEM REPORT 🔥🔥")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("="*80)
        report.append("")
        
        # Performance summary
        total_ops = len(opportunities)
        avg_edge = df['ensemble_adjusted_edge'].mean()
        avg_confidence = df['ensemble_confidence'].mean()
        avg_quality = df['prediction_quality'].mean()
        total_kelly = df['kelly_quarter'].sum()
        
        report.append("📊 ENSEMBLE PERFORMANCE METRICS:")
        report.append("-"*60)
        report.append(f"Total Opportunities: {total_ops:,}")
        report.append(f"Average Ensemble Edge: {avg_edge:.2%}")
        report.append(f"Average Model Confidence: {avg_confidence:.2%}")
        report.append(f"Average Prediction Quality: {avg_quality:.2%}")
        report.append(f"Total Kelly Allocation: {total_kelly:.1%}")
        report.append("")
        
        # Top opportunities by confidence level
        by_confidence = df.groupby('confidence_level').size().sort_values(ascending=False)
        report.append("🏆 OPPORTUNITIES BY CONFIDENCE LEVEL:")
        report.append("-"*60)
        for level, count in by_confidence.items():
            avg_edge_level = df[df['confidence_level'] == level]['ensemble_adjusted_edge'].mean()
            report.append(f"{level:12s}: {count:4d} opportunities (avg edge: {avg_edge_level:.2%})")
        report.append("")
        
        # Top 15 opportunities
        report.append("🎯 TOP 15 ENSEMBLE OPPORTUNITIES:")
        report.append("-"*80)
        
        for i, opp in enumerate(opportunities[:15], 1):
            report.append(f"{i:2d}. {opp['player']:25s} | {opp['category']:15s} | {opp['source']:10s}")
            report.append(f"    Line: {opp['line']:5.1f} | Prediction: {opp['prediction']:5.2f} | Bet: {opp['recommended_bet']:5s}")
            report.append(f"    Edge: {opp['edge']:6.2%} | Ens.Edge: {opp['ensemble_adjusted_edge']:6.2%} | Level: {opp['confidence_level']}")
            report.append(f"    Quality: {opp['prediction_quality']:5.1%} | Confidence: {opp['ensemble_confidence']:5.1%} | Kelly: {opp['kelly_quarter']:5.1%}")
            report.append("")
        
        # Category breakdown
        by_category = df.groupby('category').agg({
            'ensemble_adjusted_edge': ['count', 'mean'],
            'kelly_quarter': 'sum'
        }).round(3)
        
        report.append("📋 CATEGORY BREAKDOWN:")
        report.append("-"*60)
        for category in by_category.index:
            count = by_category.loc[category, ('ensemble_adjusted_edge', 'count')]
            avg_edge = by_category.loc[category, ('ensemble_adjusted_edge', 'mean')]
            kelly_sum = by_category.loc[category, ('kelly_quarter', 'sum')]
            report.append(f"{category:20s}: {count:3.0f} ops, {avg_edge:.2%} avg edge, {kelly_sum:.1%} Kelly")
        
        report.append("")
        report.append("🚀 ENSEMBLE ADVANTAGES:")
        report.append("-"*60)
        report.append("✅ Multi-model predictions with confidence weighting")
        report.append("✅ Dynamic model performance tracking")
        report.append("✅ Prediction quality assessment")
        report.append("✅ Ensemble-adjusted edge calculations")
        report.append("✅ Sophisticated Kelly sizing with confidence factors")
        report.append("✅ Real-time model agreement monitoring")
        
        # Save report
        report_text = "\\n".join(report)
        report_file = f"./betting_analysis/ultimate_ensemble_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"💾 Ultimate ensemble report saved: {report_file}")
        print(f"💾 Detailed opportunities saved: {csv_file}")
        
        return report_text
    
    def run_ultimate_system(self):
        """Run the complete ultimate ensemble betting system"""
        
        print("🔥🔥🔥 ULTIMATE ENSEMBLE-POWERED BETTING SYSTEM 🔥🔥🔥")
        print("="*80)
        print("🧠 Advanced ensemble learning + Sophisticated betting analytics")
        print("🎯 Meta-learning with dynamic model weighting")
        print("📊 Prediction quality assessment and confidence scoring")
        print("💎 Elite-level opportunity identification")
        print("="*80)
        
        # Step 1: Generate fresh ensemble predictions
        print("\\n🔄 Step 1: Generating fresh ensemble predictions...")
        ensemble_predictions = self.ensemble_system.generate_ensemble_predictions(
            pd.read_csv("../data/fd_hitter_features_final.csv"),
            pd.read_csv("../data/fd_pitcher_features_final.csv")
        )
        
        if not ensemble_predictions:
            print("❌ Failed to generate ensemble predictions")
            return
        
        # Step 2: Enhance predictions with analytics
        print("\\n⚡ Step 2: Enhancing predictions with advanced analytics...")
        enhanced_predictions = self.enhance_ensemble_predictions(ensemble_predictions)
        
        # Step 3: Find ultimate opportunities
        print("\\n🎯 Step 3: Finding ultimate betting opportunities...")
        opportunities = self.find_ensemble_opportunities(enhanced_predictions, min_edge=0.03)
        
        if not opportunities:
            print("❌ No opportunities found")
            return
        
        # Step 4: Generate ultimate report
        print("\\n📊 Step 4: Generating ultimate analysis report...")
        report = self.generate_ultimate_report(opportunities)
        
        # Display key results
        print("\\n" + "="*80)
        print("🏆 ULTIMATE SYSTEM RESULTS:")
        print("="*80)
        print(f"🎯 Total Elite Opportunities: {len(opportunities):,}")
        
        elite_ops = [opp for opp in opportunities if opp['confidence_level'] == 'ELITE']
        very_high_ops = [opp for opp in opportunities if opp['confidence_level'] == 'VERY_HIGH']
        
        print(f"💎 ELITE Level: {len(elite_ops)} opportunities")
        print(f"🔥 VERY_HIGH Level: {len(very_high_ops)} opportunities")
        
        if elite_ops:
            avg_elite_edge = np.mean([opp['ensemble_adjusted_edge'] for opp in elite_ops])
            print(f"💰 Average ELITE Edge: {avg_elite_edge:.2%}")
        
        total_kelly = sum(opp['kelly_quarter'] for opp in opportunities)
        print(f"📈 Total Kelly Allocation: {total_kelly:.1%}")
        
        print("\\n🔥🔥🔥 ULTIMATE ENSEMBLE SYSTEM COMPLETE! 🔥🔥🔥")

def main():
    """Run the ultimate ensemble betting system"""
    
    ultimate_system = UltimateEnsembleBettingSystem()
    ultimate_system.run_ultimate_system()

if __name__ == "__main__":
    main()
