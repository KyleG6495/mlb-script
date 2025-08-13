#!/usr/bin/env python3
"""
PrizePicks Expected Value Analyzer

Uses trained ML models to predict player performance and calculate expected value
against PrizePicks lines, similar to the Underdog Fantasy analyzer.
"""

import pandas as pd
import numpy as np
import joblib
import os
import glob
import math
from datetime import datetime, timedelta

class PrizePicksEVAnalyzer:
    def __init__(self):
        self.models = {}
        self.predictions = {}
        self.prizepicks_data = None
        
    def load_ml_models(self):
        """Load all trained ML models"""
        print("🤖 Loading trained ML models...")
        
        model_dirs = glob.glob("../Scripts/models/*")
        models_loaded = 0
        
        for model_dir in model_dirs:
            if os.path.isdir(model_dir):
                stat_name = os.path.basename(model_dir)
                model_file = os.path.join(model_dir, "best_model.pkl")
                
                if os.path.exists(model_file):
                    try:
                        self.models[stat_name] = joblib.load(model_file)
                        models_loaded += 1
                        print(f"  ✅ Loaded {stat_name} model")
                    except Exception as e:
                        print(f"  ❌ Failed to load {stat_name}: {e}")
        
        print(f"✅ Loaded {models_loaded} ML models")
        return models_loaded > 0
    
    def load_ml_predictions(self):
        """Load ML predictions from the models directory"""
        print("📊 Loading ML predictions...")
        
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
                        # Filter for recent dates (last 30 days)
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'])
                            recent_cutoff = datetime.now() - timedelta(days=30)
                            df = df[df['date'] >= recent_cutoff]
                        
                        # Get the most recent prediction for each player
                        if 'date' in df.columns:
                            df = df.sort_values('date').groupby('name').tail(1)
                        
                        # Create the format expected by the analyzer
                        pred_df = df[['name', 'predicted']].copy()
                        pred_df.columns = ['name', 'prediction']
                        
                        self.predictions[stat] = pred_df
                        predictions_loaded += 1
                        print(f"  ✅ Loaded {stat} predictions: {len(pred_df)} players")
                        
                        # Show some sample predictions for validation
                        if len(pred_df) > 0:
                            sample = pred_df.head(3)
                            print(f"    Sample predictions: {sample['prediction'].min():.2f} - {sample['prediction'].max():.2f}")
                    
                except Exception as e:
                    print(f"  ❌ Error reading {full_path}: {e}")
            else:
                print(f"  ❌ File not found: {full_path}")
        
        print(f"✅ Loaded predictions for {predictions_loaded} stat types")
        return predictions_loaded > 0
    
    def load_prizepicks_data(self):
        """Load PrizePicks data from CSV"""
        print("🎯 Loading PrizePicks data...")
        
        csv_path = "../data/prizepicks_mlb.csv"
        
        if not os.path.exists(csv_path):
            print(f"❌ PrizePicks CSV not found: {csv_path}")
            print("💡 Run convert_prizepicks_to_csv.py first!")
            return False
        
        try:
            self.prizepicks_data = pd.read_csv(csv_path)
            print(f"✅ Loaded PrizePicks data: {len(self.prizepicks_data)} players")
            
            # Show available prop types
            prop_columns = [col for col in self.prizepicks_data.columns if col != 'player_name']
            available_props = []
            for col in prop_columns:
                non_null_count = self.prizepicks_data[col].notna().sum()
                if non_null_count > 0:
                    available_props.append((col, non_null_count))
            
            available_props.sort(key=lambda x: x[1], reverse=True)
            print(f"📊 Available prop types:")
            for prop, count in available_props[:10]:
                print(f"  • {prop}: {count} props")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading PrizePicks data: {e}")
            return False
    
    def standardize_stat_names(self):
        """Create mapping between PrizePicks stat names and our model names"""
        return {
            # PrizePicks name -> Our model name
            'Home Runs': 'home_runs',
            'Hits': 'hits', 
            'Total Bases': 'total_bases',
            'Runs': 'runs',
            'RBIs': 'rbi',
            'Hitter Strikeouts': 'strikeouts',
            'Pitcher Strikeouts': 'strikeouts',
            'Hits Allowed': 'hits_allowed',
            'Walks Allowed': 'walks_allowed',
            'Earned Runs Allowed': 'earned_runs_allowed',
            'Pitching Outs': 'outs'
        }
    
    def calculate_expected_value(self, predicted_value, prizepicks_line, stat_type):
        """Calculate expected value for over/under bets"""
        
        # PrizePicks uses fixed multipliers (typically 2x for single picks)
        payout_multiplier = 2.0  # Standard PrizePicks 2x payout
        
        # Calculate probabilities
        if stat_type in ['home_runs', 'hits', 'runs', 'rbi', 'total_bases', 'strikeouts']:
            # For counting stats, use Poisson-like probability
            prob_over = 1 - self.poisson_cdf(prizepicks_line, predicted_value)
            prob_under = self.poisson_cdf(prizepicks_line, predicted_value)
        else:
            # For other stats, use normal distribution approximation
            std_dev = predicted_value * 0.3  # Assume 30% standard deviation
            prob_over = 1 - self.normal_cdf(prizepicks_line, predicted_value, std_dev)
            prob_under = self.normal_cdf(prizepicks_line, predicted_value, std_dev)
        
        # Calculate expected values (accounting for -100% loss when wrong)
        ev_over = (prob_over * (payout_multiplier - 1)) - (prob_under * 1)
        ev_under = (prob_under * (payout_multiplier - 1)) - (prob_over * 1)
        
        return {
            'prob_over': prob_over,
            'prob_under': prob_under,
            'ev_over': ev_over,
            'ev_under': ev_under,
            'edge_over': (prob_over - 0.5) * 100,  # Edge over 50-50
            'edge_under': (prob_under - 0.5) * 100
        }
    
    def poisson_cdf(self, k, lam):
        """Cumulative distribution function for Poisson distribution"""
        if lam <= 0:
            return 1.0 if k >= 0 else 0.0
        
        # Use approximation for practical calculation
        import math
        total = 0.0
        for i in range(int(k) + 1):
            total += (lam ** i) * math.exp(-lam) / math.factorial(i)
        return min(total, 1.0)
    
    def normal_cdf(self, x, mu, sigma):
        """Cumulative distribution function for normal distribution"""
        if sigma <= 0:
            return 1.0 if x >= mu else 0.0
        
        # Standard normal approximation
        z = (x - mu) / sigma
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def analyze_prizepicks_opportunities(self):
        """Find the best EV opportunities in PrizePicks"""
        print("\n🔥 ANALYZING PRIZEPICKS OPPORTUNITIES")
        print("=" * 50)
        
        if self.prizepicks_data is None:
            print("❌ No PrizePicks data loaded")
            return []
        
        stat_mapping = self.standardize_stat_names()
        opportunities = []
        
        # Analyze each player and stat combination
        for _, player_row in self.prizepicks_data.iterrows():
            player_name = player_row['player_name']
            
            # Check each stat type
            for pp_stat, model_stat in stat_mapping.items():
                if pp_stat in self.prizepicks_data.columns:
                    pp_line = player_row[pp_stat]
                    
                    if pd.notna(pp_line):
                        # Try to find prediction for this player/stat
                        prediction = self.get_prediction(player_name, model_stat)
                        
                        if prediction is not None:
                            # Calculate EV
                            ev_analysis = self.calculate_expected_value(prediction, pp_line, model_stat)
                            
                            # Only keep significant edges (>5%)
                            if abs(ev_analysis['edge_over']) > 5 or abs(ev_analysis['edge_under']) > 5:
                                
                                # Determine best bet
                                if ev_analysis['ev_over'] > ev_analysis['ev_under']:
                                    best_bet = 'OVER'
                                    best_ev = ev_analysis['ev_over']
                                    best_edge = ev_analysis['edge_over']
                                    best_prob = ev_analysis['prob_over']
                                else:
                                    best_bet = 'UNDER'
                                    best_ev = ev_analysis['ev_under']
                                    best_edge = ev_analysis['edge_under']
                                    best_prob = ev_analysis['prob_under']
                                
                                opportunities.append({
                                    'player': player_name,
                                    'stat': pp_stat,
                                    'line': pp_line,
                                    'prediction': prediction,
                                    'bet_type': best_bet,
                                    'expected_value': best_ev,
                                    'edge_percent': best_edge,
                                    'win_probability': best_prob,
                                    'source': self.get_prediction_source(player_name, model_stat)
                                })
        
        # Sort by expected value
        opportunities.sort(key=lambda x: x['expected_value'], reverse=True)
        
        print(f"🎯 Found {len(opportunities)} EV opportunities")
        return opportunities
    
    def get_prediction(self, player_name, stat_type):
        """Get ML prediction for a player/stat combination"""
        
        # Try to find in loaded predictions
        if stat_type in self.predictions:
            pred_df = self.predictions[stat_type]
            
            # Try exact name match first
            exact_match = pred_df[pred_df['name'].str.lower() == player_name.lower()]
            if not exact_match.empty:
                return exact_match[stat_type].iloc[0] if stat_type in exact_match.columns else exact_match.iloc[0, 1]
            
            # Try partial name match
            partial_match = pred_df[pred_df['name'].str.lower().str.contains(player_name.lower().split()[0])]
            if not partial_match.empty:
                return partial_match[stat_type].iloc[0] if stat_type in partial_match.columns else partial_match.iloc[0, 1]
        
        return None
    
    def get_prediction_source(self, player_name, stat_type):
        """Determine the source of the prediction"""
        if self.get_prediction(player_name, stat_type) is not None:
            return "🤖 ML Model"
        return "📊 Season Stats"
    
    def create_ev_report(self, opportunities):
        """Create a detailed EV report"""
        print(f"\n🔥 TOP PRIZEPICKS EV PLAYS:")
        print("-" * 60)
        
        if not opportunities:
            print("❌ No significant EV opportunities found")
            return
        
        # Show top 15 opportunities
        for i, opp in enumerate(opportunities[:15], 1):
            print(f"{i:2d}. {opp['player']:<20} {opp['stat']:<20} {opp['bet_type']:>5} {opp['line']}")
            print(f"    🔥 Pred: {opp['prediction']:.3f} | Edge: {opp['edge_percent']:+.1f}% | {opp['source']}")
        
        # Save detailed report
        opportunities_df = pd.DataFrame(opportunities)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        output_file = f"../data/prizepicks_ev_analysis_{timestamp}.csv"
        opportunities_df.to_csv(output_file, index=False)
        print(f"\n💾 Detailed EV analysis saved: {output_file}")
        
        # Summary stats
        print(f"\n📊 SUMMARY:")
        print(f"   Total opportunities: {len(opportunities)}")
        print(f"   Average edge: {opportunities_df['edge_percent'].mean():.1f}%")
        print(f"   Best edge: {opportunities_df['edge_percent'].max():.1f}%")
        
        over_bets = opportunities_df[opportunities_df['bet_type'] == 'OVER']
        under_bets = opportunities_df[opportunities_df['bet_type'] == 'UNDER']
        print(f"   OVER bets: {len(over_bets)} ({len(over_bets)/len(opportunities)*100:.1f}%)")
        print(f"   UNDER bets: {len(under_bets)} ({len(under_bets)/len(opportunities)*100:.1f}%)")
    
    def run_analysis(self):
        """Run complete PrizePicks EV analysis"""
        print("🎯 PRIZEPICKS EXPECTED VALUE ANALYZER")
        print("=" * 50)
        
        # Load data
        if not self.load_prizepicks_data():
            return
        
        # Try to load ML predictions
        if not self.load_ml_predictions():
            print("⚠️ No ML predictions available, analysis may be limited")
        
        # Run EV analysis
        opportunities = self.analyze_prizepicks_opportunities()
        
        # Generate report
        self.create_ev_report(opportunities)
        
        print(f"\n🎉 PrizePicks EV analysis complete!")

if __name__ == "__main__":
    analyzer = PrizePicksEVAnalyzer()
    analyzer.run_analysis()
