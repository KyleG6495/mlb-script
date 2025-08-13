#!/usr/bin/env python3
"""
model_driven_arbitrage.py

Advanced arbitrage detection using your trained ML models to identify profitable betting opportunities.
This script:
1. Loads your trained models for strikeouts, hits, total bases, etc.
2. Generates predictions for today's slate
3. Compares model predictions vs sportsbook lines
4. Calculates expected value and identifies arbitrage opportunities
5. Recommends bets with highest edge

Usage:
    python model_driven_arbitrage.py --output-dir ./arbitrage_analysis
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
from scipy import stats
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class ModelDrivenArbitrage:
    def __init__(self, models_dir="./models"):
        self.models_dir = Path(models_dir)
        self.models = {}
        self.predictions = {}
        
    def load_models(self):
        """Load all trained models"""
        model_categories = [
            "strikeouts", "hits", "total_bases", "runs", "rbi", 
            "home_runs", "stolen_bases"
        ]
        
        for category in model_categories:
            model_path = self.models_dir / category / f"{category}_model.pkl"
            if model_path.exists():
                try:
                    self.models[category] = joblib.load(model_path)
                    logging.info(f"✅ Loaded {category} model")
                except Exception as e:
                    logging.warning(f"❌ Failed to load {category} model: {e}")
            else:
                logging.warning(f"🔍 Model not found: {model_path}")
    
    def load_sportsbook_lines(self):
        """Load lines from both PrizePicks and Underdog Fantasy"""
        # PrizePicks data
        pp_file = "../data/PP_mlb_picks_20250719_175116.xlsx"
        ud_file = "../data/today_pitcher_props_2025-07-19.csv"
        
        lines = {}
        
        # Load PrizePicks
        if os.path.exists(pp_file):
            pp_df = pd.read_excel(pp_file)
            logging.info(f"📊 Loaded PrizePicks: {len(pp_df)} players")
            
            # Convert to long format for easier processing
            pp_long = pd.melt(
                pp_df, 
                id_vars=['player_name'], 
                value_name='line'
            ).dropna(subset=['line'])
            pp_long['source'] = 'PrizePicks'
            lines['prizepicks'] = pp_long
            
        # Load Underdog Fantasy
        if os.path.exists(ud_file):
            ud_df = pd.read_csv(ud_file)
            logging.info(f"📊 Loaded Underdog: {len(ud_df)} props")
            ud_df['source'] = 'Underdog'
            lines['underdog'] = ud_df
        
        return lines
    
    def generate_predictions(self, features_file):
        """Generate predictions using loaded models"""
        if not os.path.exists(features_file):
            logging.error(f"Features file not found: {features_file}")
            return {}
        
        df = pd.read_csv(features_file)
        logging.info(f"📋 Loaded features for {len(df)} players")
        
        predictions = {}
        
        for category, model in self.models.items():
            try:
                # Prepare features for this model
                expected_features = list(model.feature_names_in_)
                X = df.select_dtypes(include=[np.number]).copy()
                
                # Add missing features (fill with zero)
                for col in expected_features:
                    if col not in X.columns:
                        X[col] = 0
                
                # Ensure column order matches training
                X = X[expected_features]
                
                # Generate predictions
                preds = model.predict(X)
                
                # Store with player info
                pred_df = df[['player_id', 'name']].copy() if 'name' in df.columns else df[['player_id']].copy()
                pred_df[f'predicted_{category}'] = preds
                
                predictions[category] = pred_df
                logging.info(f"✅ Generated {category} predictions for {len(pred_df)} players")
                
            except Exception as e:
                logging.error(f"❌ Failed to predict {category}: {e}")
        
        return predictions
    
    def calculate_probability_over_line(self, prediction, line, sigma=1.24):
        """Calculate P(actual ≥ line) using normal distribution"""
        return 1 - stats.norm.cdf(line, loc=prediction, scale=sigma)
    
    def calculate_expected_value(self, prob_over, line, odds=-110):
        """Calculate expected value of a bet"""
        # Convert American odds to decimal
        if odds > 0:
            decimal_odds = (odds / 100) + 1
        else:
            decimal_odds = (100 / abs(odds)) + 1
        
        # Expected value calculation
        # EV = (probability of win * payout) - (probability of loss * stake)
        prob_win = prob_over
        prob_loss = 1 - prob_over
        payout = decimal_odds - 1  # Profit if win (assuming $1 bet)
        stake = 1
        
        ev = (prob_win * payout) - (prob_loss * stake)
        return ev
    
    def find_arbitrage_opportunities(self, predictions, lines):
        """Find arbitrage opportunities between model predictions and sportsbook lines"""
        opportunities = []
        
        for category, pred_df in predictions.items():
            for _, pred_row in pred_df.iterrows():
                player_name = pred_row.get('name', f"Player_{pred_row['player_id']}")
                prediction = pred_row[f'predicted_{category}']
                
                # Find matching lines for this player and category
                for source, line_df in lines.items():
                    if source == 'prizepicks':
                        # Match by player name and stat type
                        stat_mapping = {
                            'strikeouts': 'Pitcher Strikeouts',
                            'hits': 'Hits',
                            'total_bases': 'Total Bases',
                            'runs': 'Runs',
                            'rbi': 'RBIs',
                            'home_runs': 'Home Runs'
                        }
                        
                        if category in stat_mapping:
                            stat_col = stat_mapping[category]
                            player_lines = line_df[
                                (line_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                                (line_df['variable'] == stat_col)
                            ]
                            
                            for _, line_row in player_lines.iterrows():
                                line_value = line_row['line']
                                
                                # Calculate probability and expected value
                                prob_over = self.calculate_probability_over_line(prediction, line_value)
                                ev_over = self.calculate_expected_value(prob_over, line_value)
                                ev_under = self.calculate_expected_value(1 - prob_over, line_value)
                                
                                # Determine if there's an edge
                                edge = max(ev_over, ev_under)
                                bet_side = "OVER" if ev_over > ev_under else "UNDER"
                                
                                if edge > 0.05:  # 5% edge threshold
                                    opportunities.append({
                                        'player': player_name,
                                        'category': category,
                                        'source': source,
                                        'line': line_value,
                                        'prediction': prediction,
                                        'prob_over': prob_over,
                                        'prob_under': 1 - prob_over,
                                        'ev_over': ev_over,
                                        'ev_under': ev_under,
                                        'recommended_bet': bet_side,
                                        'edge': edge,
                                        'confidence': 'HIGH' if edge > 0.15 else 'MEDIUM' if edge > 0.10 else 'LOW'
                                    })
                    
                    elif source == 'underdog':
                        # Match Underdog Fantasy props
                        stat_mapping = {
                            'strikeouts': 'Pitcher Strikeouts'
                        }
                        
                        if category in stat_mapping:
                            stat_type = stat_mapping[category]
                            player_lines = line_df[
                                (line_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                                (line_df['stat_type'] == stat_type)
                            ]
                            
                            for _, line_row in player_lines.iterrows():
                                line_value = line_row['line']
                                
                                prob_over = self.calculate_probability_over_line(prediction, line_value)
                                ev_over = self.calculate_expected_value(prob_over, line_value)
                                ev_under = self.calculate_expected_value(1 - prob_over, line_value)
                                
                                edge = max(ev_over, ev_under)
                                bet_side = "OVER" if ev_over > ev_under else "UNDER"
                                
                                if edge > 0.05:
                                    opportunities.append({
                                        'player': player_name,
                                        'category': category,
                                        'source': source,
                                        'line': line_value,
                                        'prediction': prediction,
                                        'prob_over': prob_over,
                                        'prob_under': 1 - prob_over,
                                        'ev_over': ev_over,
                                        'ev_under': ev_under,
                                        'recommended_bet': bet_side,
                                        'edge': edge,
                                        'confidence': 'HIGH' if edge > 0.15 else 'MEDIUM' if edge > 0.10 else 'LOW'
                                    })
        
        return opportunities
    
    def cross_book_arbitrage(self, lines):
        """Find pure arbitrage opportunities between different sportsbooks"""
        arb_ops = []
        
        # Compare PrizePicks vs Underdog for same props
        if 'prizepicks' in lines and 'underdog' in lines:
            pp_df = lines['prizepicks']
            ud_df = lines['underdog']
            
            # Find matching props
            for _, pp_row in pp_df.iterrows():
                if pp_row['variable'] == 'Pitcher Strikeouts':
                    player_name = pp_row['player_name']
                    pp_line = pp_row['line']
                    
                    # Find matching Underdog prop
                    ud_matches = ud_df[
                        (ud_df['player_name'].str.contains(player_name.split()[0], case=False, na=False)) &
                        (ud_df['stat_type'] == 'Pitcher Strikeouts')
                    ]
                    
                    for _, ud_row in ud_matches.iterrows():
                        ud_line = ud_row['line']
                        
                        # Check for line discrepancy (potential arbitrage)
                        line_diff = abs(pp_line - ud_line)
                        if line_diff >= 2.0:  # Significant difference
                            better_book = 'PrizePicks' if pp_line < ud_line else 'Underdog'
                            worse_book = 'Underdog' if better_book == 'PrizePicks' else 'PrizePicks'
                            
                            arb_ops.append({
                                'player': player_name,
                                'stat': 'Pitcher Strikeouts',
                                'pp_line': pp_line,
                                'ud_line': ud_line,
                                'line_difference': line_diff,
                                'opportunity': f"Bet UNDER {max(pp_line, ud_line)} on {better_book}, OVER {min(pp_line, ud_line)} on {worse_book}",
                                'type': 'CROSS_BOOK_ARBITRAGE'
                            })
        
        return arb_ops
    
    def generate_report(self, opportunities, arb_ops, output_dir):
        """Generate comprehensive arbitrage report"""
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Model-based opportunities
        if opportunities:
            opps_df = pd.DataFrame(opportunities)
            opps_df = opps_df.sort_values('edge', ascending=False)
            
            opps_file = f"{output_dir}/model_arbitrage_opportunities_{timestamp}.csv"
            opps_df.to_csv(opps_file, index=False)
            
            # Summary report
            summary_file = f"{output_dir}/arbitrage_summary_{timestamp}.txt"
            with open(summary_file, 'w') as f:
                f.write(f"MLB MODEL-DRIVEN ARBITRAGE REPORT\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*60}\n\n")
                
                f.write(f"🎯 TOP 10 BETTING OPPORTUNITIES:\n")
                f.write(f"{'-'*60}\n")
                
                for i, (_, opp) in enumerate(opps_df.head(10).iterrows(), 1):
                    f.write(f"{i:2d}. {opp['player']:20s} | {opp['category']:12s} | {opp['source']:10s}\n")
                    f.write(f"    Line: {opp['line']:5.1f} | Prediction: {opp['prediction']:5.1f} | Bet: {opp['recommended_bet']:5s}\n")
                    f.write(f"    Edge: {opp['edge']:6.2%} | Confidence: {opp['confidence']:6s}\n")
                    f.write(f"    Prob Over: {opp['prob_over']:5.1%} | EV Over: {opp['ev_over']:+6.3f} | EV Under: {opp['ev_under']:+6.3f}\n\n")
                
                # Summary stats
                high_conf = len(opps_df[opps_df['confidence'] == 'HIGH'])
                medium_conf = len(opps_df[opps_df['confidence'] == 'MEDIUM'])
                avg_edge = opps_df['edge'].mean()
                
                f.write(f"📊 SUMMARY STATISTICS:\n")
                f.write(f"{'-'*30}\n")
                f.write(f"Total Opportunities: {len(opps_df)}\n")
                f.write(f"High Confidence: {high_conf}\n")
                f.write(f"Medium Confidence: {medium_conf}\n")
                f.write(f"Average Edge: {avg_edge:.2%}\n")
            
            logging.info(f"✅ Model arbitrage report saved: {opps_file}")
            logging.info(f"✅ Summary report saved: {summary_file}")
        
        # Cross-book arbitrage
        if arb_ops:
            arb_df = pd.DataFrame(arb_ops)
            arb_file = f"{output_dir}/cross_book_arbitrage_{timestamp}.csv"
            arb_df.to_csv(arb_file, index=False)
            logging.info(f"✅ Cross-book arbitrage saved: {arb_file}")
    
    def run_analysis(self, features_file, output_dir):
        """Run complete arbitrage analysis"""
        logging.info("🚀 Starting Model-Driven Arbitrage Analysis")
        
        # Load models
        self.load_models()
        if not self.models:
            logging.error("❌ No models loaded. Train models first!")
            return
        
        # Generate predictions
        predictions = self.generate_predictions(features_file)
        if not predictions:
            logging.error("❌ No predictions generated")
            return
        
        # Load sportsbook lines
        lines = self.load_sportsbook_lines()
        if not lines:
            logging.error("❌ No sportsbook lines loaded")
            return
        
        # Find arbitrage opportunities
        opportunities = self.find_arbitrage_opportunities(predictions, lines)
        arb_ops = self.cross_book_arbitrage(lines)
        
        # Generate report
        self.generate_report(opportunities, arb_ops, output_dir)
        
        logging.info(f"🎯 Found {len(opportunities)} model-based opportunities")
        logging.info(f"⚡ Found {len(arb_ops)} cross-book arbitrage opportunities")

def main():
    parser = argparse.ArgumentParser(description="Model-driven arbitrage detection")
    parser.add_argument("--models-dir", default="./models", help="Directory containing trained models")
    parser.add_argument("--features", default="../data/pitcher_features_probables.csv", help="Features file for predictions")
    parser.add_argument("--output-dir", default="./arbitrage_analysis", help="Output directory for reports")
    
    args = parser.parse_args()
    
    arbitrage = ModelDrivenArbitrage(args.models_dir)
    arbitrage.run_analysis(args.features, args.output_dir)

if __name__ == "__main__":
    main()
