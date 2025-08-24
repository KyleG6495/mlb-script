#!/usr/bin/env python3
"""
Enhanced PrizePicks Expected Value Analyzer

Uses trained ML models to predict player performance and calculate expected value
against PrizePicks lines with improved accuracy and validation.
"""

import pandas as pd
import numpy as np
import joblib
import os
import glob
import math
from datetime import datetime, timedelta
from scipy.stats import poisson, norm

class PrizePicksEVAnalyzer:
    def __init__(self):
        self.prizepicks_data = None
        self.predictions = {}
        self.ev_results = []
        
    def load_prizepicks_data(self):
        """Load PrizePicks data from CSV"""
        print("TARGET: Loading PrizePicks data...")
        
        data_file = '../data/prizepicks_mlb.csv'
        if not os.path.exists(data_file):
            print("ERROR: PrizePicks data file not found. Run convert_prizepicks_to_csv.py first.")
            return False
            
        self.prizepicks_data = pd.read_csv(data_file)
        print(f"SUCCESS: Loaded PrizePicks data: {len(self.prizepicks_data)} players")
        
        # Transform data from wide format to long format for analysis
        stat_columns = [col for col in self.prizepicks_data.columns if col != 'player_name']
        
        # Show available prop types and their counts
        print("DATA: Available prop types:")
        for stat in stat_columns:
            non_null_count = self.prizepicks_data[stat].notna().sum()
            if non_null_count > 0:
                print(f"   {stat}: {non_null_count} props")
        
        return True
        
    def load_ml_predictions(self):
        """Load ML predictions from the models directory"""
        print("DATA: Loading ML predictions...")
        
        # Look for prediction files in the models directory
        prediction_files = {
            'hits': 'models/hits/predictions_hits.csv',
            'home_runs': 'models/home_runs/predictions_home_runs.csv',
            'total_bases': 'models/total_bases/predictions_total_bases.csv',
            'runs': 'models/runs/predictions_runs.csv',
            'rbi': 'models/rbi/predictions_rbi.csv',
            'strikeouts': 'models/strikeouts/predictions_strikeouts.csv'
        }
        
        predictions_loaded = 0
        
        for stat, file_path in prediction_files.items():
            full_path = os.path.join('..', 'Scripts', file_path)
            if os.path.exists(full_path):
                try:
                    df = pd.read_csv(full_path)
                    if len(df) > 0 and 'name' in df.columns and 'predicted' in df.columns:
                        # Filter for recent dates (last 14 days for more current predictions)
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            recent_cutoff = datetime.now() - timedelta(days=14)
                            recent_df = df[df['date'] >= recent_cutoff]
                            
                            # If we don't have recent data, use the most recent available
                            if len(recent_df) == 0:
                                recent_cutoff = datetime.now() - timedelta(days=60)
                                recent_df = df[df['date'] >= recent_cutoff]
                                
                            df = recent_df if len(recent_df) > 0 else df
                        
                        # Get the most recent prediction for each player
                        if 'date' in df.columns:
                            df = df.sort_values('date').groupby('name').tail(1)
                        
                        # Clean predictions - apply reasonable bounds
                        df['predicted'] = self.apply_prediction_bounds(df['predicted'].copy(), stat)
                        
                        # Create the format expected by the analyzer
                        pred_df = df[['name', 'predicted']].copy()
                        pred_df.columns = ['name', 'prediction']
                        
                        self.predictions[stat] = pred_df
                        predictions_loaded += 1
                        print(f"  SUCCESS: Loaded {stat} predictions: {len(pred_df)} players")
                        
                        # Show some sample predictions for validation
                        if len(pred_df) > 0:
                            sample = pred_df['prediction']
                            print(f"    Range: {sample.min():.3f} - {sample.max():.3f}, Avg: {sample.mean():.3f}")
                    
                except Exception as e:
                    print(f"  ERROR: Error reading {full_path}: {e}")
            else:
                print(f"  ERROR: File not found: {full_path}")
        
        print(f"SUCCESS: Loaded predictions for {predictions_loaded} stat types")
        return predictions_loaded > 0
        
    def apply_prediction_bounds(self, predictions, stat_type):
        """Apply reasonable bounds to predictions based on stat type"""
        if stat_type == 'home_runs':
            # Home runs should be non-negative and reasonable (max ~2 per game)
            return np.clip(predictions, 0.0, 2.0)
        elif stat_type == 'hits':
            # Hits should be between 0 and ~4 per game
            return np.clip(predictions, 0.0, 4.0)
        elif stat_type == 'runs':
            # Runs should be between 0 and ~3 per game
            return np.clip(predictions, 0.0, 3.0)
        elif stat_type == 'rbi':
            # RBIs should be between 0 and ~5 per game
            return np.clip(predictions, 0.0, 5.0)
        elif stat_type == 'total_bases':
            # Total bases should be between 0 and ~10 per game
            return np.clip(predictions, 0.0, 10.0)
        elif stat_type == 'strikeouts':
            # Strikeouts should be between 0 and ~15 per game
            return np.clip(predictions, 0.0, 15.0)
        else:
            # Default bounds
            return np.clip(predictions, 0.0, predictions.max())
    
    def normal_cdf(self, x, mean, std):
        """Calculate cumulative distribution function for normal distribution"""
        if std <= 0:
            return 1.0 if x >= mean else 0.0
        z = (x - mean) / std
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def calculate_ev(self, prediction, line, bet_type, stat_type):
        """Calculate expected value for a bet"""
        try:
            # Determine probability based on stat type and distribution
            if stat_type.lower() in ['home_runs', 'runs', 'rbi', 'hits']:
                # Use Poisson distribution for counting stats
                lambda_param = max(prediction, 0.001)  # Avoid zero
                if bet_type == 'OVER':
                    prob_win = 1 - poisson.cdf(line, lambda_param)
                else:  # UNDER
                    prob_win = poisson.cdf(line, lambda_param)
            else:
                # Use normal distribution for other stats
                std_dev = max(prediction * 0.5, 0.1)  # Reasonable standard deviation
                if bet_type == 'OVER':
                    prob_win = 1 - self.normal_cdf(line, prediction, std_dev)
                else:  # UNDER
                    prob_win = self.normal_cdf(line, prediction, std_dev)
            
            # Ensure probability is within bounds
            prob_win = max(0.001, min(0.999, prob_win))
            
            # Calculate implied probability from PrizePicks odds (assume -110)
            implied_prob = 0.52381  # 52.381% for -110 odds
            
            # Calculate expected value
            payout_odds = 0.9091  # Net payout for -110 odds
            ev = (prob_win * payout_odds) - ((1 - prob_win) * 1.0)
            
            # Calculate edge
            edge = (prob_win - implied_prob) / implied_prob
            
            return {
                'ev': ev,
                'edge': edge,
                'prob_win': prob_win,
                'implied_prob': implied_prob
            }
            
        except Exception as e:
            print(f"Error calculating EV: {e}")
            return None
    
    def analyze_opportunities(self):
        """Analyze all PrizePicks opportunities for positive EV"""
        print(" ANALYZING PRIZEPICKS OPPORTUNITIES")
        print("=" * 50)
        
        if self.prizepicks_data is None or not self.predictions:
            print("ERROR: Missing data or predictions")
            return
        
        # Map PrizePicks stat columns to our prediction keys
        stat_mapping = {
            'Hits': 'hits',
            'Home Runs': 'home_runs',
            'Total Bases': 'total_bases',
            'Runs': 'runs',
            'RBIs': 'rbi',
            'Hitter Strikeouts': 'strikeouts',
            'Pitcher Strikeouts': 'strikeouts'
        }
        
        opportunities = []
        total_props = 0
        
        # Iterate through each player and their props
        for _, player_row in self.prizepicks_data.iterrows():
            player_name = player_row['player_name']
            
            # Check each stat column
            for stat_column in self.prizepicks_data.columns:
                if stat_column == 'player_name':
                    continue
                    
                line = player_row[stat_column]
                if pd.isna(line):
                    continue
                    
                total_props += 1
                
                # Map to our prediction key
                pred_key = stat_mapping.get(stat_column)
                if not pred_key or pred_key not in self.predictions:
                    continue
                
                # Find player prediction
                pred_df = self.predictions[pred_key]
                player_pred = pred_df[pred_df['name'].str.contains(player_name, case=False, na=False)]
                
                if len(player_pred) == 0:
                    # Try partial name match
                    name_parts = player_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        player_pred = pred_df[
                            (pred_df['name'].str.contains(first_name, case=False, na=False)) &
                            (pred_df['name'].str.contains(last_name, case=False, na=False))
                        ]
                
                if len(player_pred) == 0:
                    continue
                    
                prediction = player_pred.iloc[0]['prediction']
                
                # Calculate EV for both OVER and UNDER
                for bet_type in ['OVER', 'UNDER']:
                    ev_calc = self.calculate_ev(prediction, line, bet_type, stat_column)
                    
                    if ev_calc and ev_calc['edge'] > 0.05:  # 5% minimum edge
                        opportunities.append({
                            'player': player_name,
                            'stat': stat_column,
                            'line': line,
                            'bet_type': bet_type,
                            'prediction': prediction,
                            'ev': ev_calc['ev'],
                            'edge': ev_calc['edge'],
                            'prob_win': ev_calc['prob_win'],
                            'model_source': ' ML Model'
                        })
        
        # Sort by edge (highest first)
        opportunities.sort(key=lambda x: x['edge'], reverse=True)
        self.ev_results = opportunities
        
        print(f"TARGET: Found {len(opportunities)} EV opportunities from {total_props} total props")
        
        # Display top opportunities
        if opportunities:
            print(" TOP PRIZEPICKS EV PLAYS:")
            print("-" * 60)
            
            for i, opp in enumerate(opportunities[:20], 1):
                print(f"{i:2d}. {opp['player']:<20} {opp['stat']:<20} {opp['bet_type']:<5} {opp['line']}")
                print(f"     Pred: {opp['prediction']:.3f} | Edge: {opp['edge']:+.1%} | {opp['model_source']}")
        
        return opportunities
    
    def save_results(self):
        """Save detailed EV analysis to CSV"""
        if not self.ev_results:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f"../data/prizepicks_ev_analysis_enhanced_{timestamp}.csv"
        
        df = pd.DataFrame(self.ev_results)
        df.to_csv(output_file, index=False)
        print(f" Enhanced EV analysis saved: {output_file}")
        
        # Summary statistics
        total_opps = len(self.ev_results)
        avg_edge = df['edge'].mean()
        best_edge = df['edge'].max()
        over_bets = len(df[df['bet_type'] == 'OVER'])
        under_bets = len(df[df['bet_type'] == 'UNDER'])
        
        print("DATA: SUMMARY:")
        print(f"   Total opportunities: {total_opps}")
        print(f"   Average edge: {avg_edge:.1%}")
        print(f"   Best edge: {best_edge:.1%}")
        print(f"   OVER bets: {over_bets} ({over_bets/total_opps:.1%})")
        print(f"   UNDER bets: {under_bets} ({under_bets/total_opps:.1%})")

def main():
    print("TARGET: ENHANCED PRIZEPICKS EXPECTED VALUE ANALYZER")
    print("=" * 50)
    
    analyzer = PrizePicksEVAnalyzer()
    
    # Load data and predictions
    if not analyzer.load_prizepicks_data():
        return
    
    if not analyzer.load_ml_predictions():
        print("ERROR: Failed to load ML predictions")
        return
    
    # Analyze opportunities
    opportunities = analyzer.analyze_opportunities()
    
    if opportunities:
        analyzer.save_results()
    else:
        print("ERROR: No EV opportunities found")
    
    print("COMPLETE: Enhanced PrizePicks EV analysis complete!")

if __name__ == "__main__":
    main()
