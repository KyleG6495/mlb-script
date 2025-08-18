#!/usr/bin/env python3
"""
FIXED PrizePicks & Underdog Fantasy Expected Value Analyzer
Properly calculates EV with realistic probability bounds and correct math
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

class FixedPlatformEVAnalyzer:
    def __init__(self):
        self.platform_multipliers = {
            'prizepicks': {
                2: 3.0, 3: 6.0, 4: 10.0, 5: 20.0, 6: 50.0
            },
            'underdog': {
                2: 3.0, 3: 6.0, 4: 10.0, 5: 20.0, 6: 40.0
            }
        }
        
    def load_and_clean_data(self):
        """Load and properly clean the betting data"""
        
        # Load the source data
        file_path = "../Scripts/betting_analysis/betting_opportunities_20250720_144550.csv"
        if not os.path.exists(file_path):
            print("ERROR: Source data file not found")
            return pd.DataFrame()
            
        df = pd.read_csv(file_path)
        print(f"DATA: Loaded {len(df)} raw opportunities")
        
        # Clean the data step by step
        cleaned_data = []
        
        for _, row in df.iterrows():
            # Skip rows with missing essential data
            if pd.isna(row.get('player')) or pd.isna(row.get('prediction')):
                continue
                
            # Get basic info
            player = row['player']
            category = row['category']
            platform = row.get('source', 'unknown')
            line = float(row['line'])
            prediction = float(row['prediction'])
            
            # Skip non-supported platforms
            if platform not in ['prizepicks', 'underdog']:
                continue
                
            # Calculate realistic probabilities based on prediction vs line
            prob_over = self.calculate_realistic_prob_over(prediction, line, category)
            prob_under = 1 - prob_over
            
            # Calculate proper expected values for -110 odds
            implied_prob = 0.5238  # -110 odds = 52.38% implied probability
            
            # EV calculation: (Win_Prob * Win_Amount) - (Lose_Prob * Lose_Amount)
            # For -110 odds: Win $0.909 for every $1 bet, Lose $1 for every $1 bet
            ev_over = (prob_over * 0.909) - (prob_under * 1.0)
            ev_under = (prob_under * 0.909) - (prob_over * 1.0)
            
            # Only include bets with positive EV and reasonable probabilities
            if ev_over > 0 and 0.05 <= prob_over <= 0.95:
                edge = prob_over - implied_prob
                cleaned_data.append({
                    'platform': platform,
                    'player': player,
                    'category': category,
                    'line': f"O{line}",
                    'bet_type': 'OVER',
                    'our_prob': prob_over,
                    'implied_prob': implied_prob,
                    'expected_value': ev_over,
                    'edge': edge,
                    'confidence': self.get_confidence_level(abs(edge)),
                    'prediction': prediction,
                    'line_value': line
                })
                
            if ev_under > 0 and 0.05 <= prob_under <= 0.95:
                edge = prob_under - implied_prob
                cleaned_data.append({
                    'platform': platform,
                    'player': player,
                    'category': category,
                    'line': f"U{line}",
                    'bet_type': 'UNDER',
                    'our_prob': prob_under,
                    'implied_prob': implied_prob,
                    'expected_value': ev_under,
                    'edge': edge,
                    'confidence': self.get_confidence_level(abs(edge)),
                    'prediction': prediction,
                    'line_value': line
                })
        
        result_df = pd.DataFrame(cleaned_data)
        print(f"SUCCESS: Cleaned to {len(result_df)} valid opportunities")
        return result_df
    
    def calculate_realistic_prob_over(self, prediction, line, category):
        """Calculate realistic probability of going over the line"""
        
        # Category-specific standard deviations (based on typical MLB variance)
        std_dev_map = {
            'hits': 0.8,
            'runs': 0.6,
            'rbis': 0.7,
            'home_runs': 0.4,  # Less variance for rare events
            'total_bases': 1.0,
            'strikeouts': 0.9,
            'walks': 0.5
        }
        
        std_dev = std_dev_map.get(category, 0.8)
        
        # Use normal distribution approximation
        # P(X > line) where X ~ N(prediction, std_dev^2)
        z_score = (line - prediction) / std_dev
        
        # Convert to probability using normal CDF
        from scipy.stats import norm
        prob_over = 1 - norm.cdf(z_score)
        
        # Ensure reasonable bounds
        prob_over = max(0.05, min(0.95, prob_over))
        
        return prob_over
    
    def get_confidence_level(self, edge):
        """Convert edge to confidence level"""
        if edge >= 0.15:
            return "VERY_HIGH"
        elif edge >= 0.10:
            return "HIGH"
        elif edge >= 0.05:
            return "MEDIUM"
        else:
            return "LOW"
    
    def create_platform_sheets(self, ev_df):
        """Create clean sheets for each platform"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        for platform in ['prizepicks', 'underdog']:
            platform_data = ev_df[ev_df['platform'] == platform].copy()
            
            if len(platform_data) == 0:
                print(f"WARNING: No opportunities found for {platform}")
                continue
            
            # Remove duplicates and sort by EV
            platform_data = platform_data.drop_duplicates(
                subset=['player', 'category', 'line', 'bet_type']
            ).sort_values('expected_value', ascending=False)
            
            # Add ranking
            platform_data['rank'] = range(1, len(platform_data) + 1)
            
            # Format for display
            platform_data['ev_display'] = platform_data['expected_value'].apply(lambda x: f"{x:.3f}")
            platform_data['edge_display'] = platform_data['edge'].apply(lambda x: f"{x:.1%}")
            platform_data['prob_display'] = platform_data['our_prob'].apply(lambda x: f"{x:.1%}")
            
            # Create final sheet
            sheet_columns = [
                'rank', 'player', 'category', 'line', 'bet_type',
                'prob_display', 'ev_display', 'edge_display', 
                'confidence'
            ]
            
            final_sheet = platform_data[sheet_columns].copy()
            final_sheet.columns = [
                'Rank', 'Player', 'Category', 'Line', 'Bet Type',
                'Our Probability', 'Expected Value', 'Edge %', 'Confidence'
            ]
            
            # Save to file
            filename = f"../data/{platform}_fixed_ev_{timestamp}.csv"
            final_sheet.to_csv(filename, index=False)
            
            print(f"\n {platform.title()} sheet saved: {filename}")
            print(f"TARGET: Found {len(platform_data)} opportunities")
            
            # Show top 10
            print(f"\nLINEUP: TOP 10 {platform.upper()} OPPORTUNITIES:")
            print("=" * 85)
            top_10 = final_sheet.head(10)
            for i, row in top_10.iterrows():
                print(f"{row['Rank']:2d}. {row['Player'][:18]:18s} {row['Category'][:10]:10s} "
                      f"{row['Line']:6s} EV:{row['Expected Value']:7s} "
                      f"Edge:{row['Edge %']:7s} {row['Confidence']}")
    
    def analyze_best_combos(self, ev_df):
        """Analyze the best combo opportunities"""
        
        print(f"\n COMBO ANALYSIS WITH FIXED CALCULATIONS")
        print("=" * 50)
        
        for platform in ['prizepicks', 'underdog']:
            platform_data = ev_df[
                (ev_df['platform'] == platform) & 
                (ev_df['expected_value'] > 0.02) &  # At least 2% EV
                (ev_df['confidence'].isin(['MEDIUM', 'HIGH', 'VERY_HIGH']))
            ].copy()
            
            if len(platform_data) < 2:
                print(f"WARNING: Not enough quality bets for {platform} combos")
                continue
                
            # Remove duplicates and get top picks
            unique_picks = platform_data.drop_duplicates(
                subset=['player', 'category']
            ).nlargest(6, 'expected_value')
            
            print(f"\nTARGET: {platform.upper()} COMBO OPPORTUNITIES:")
            
            for combo_size in [2, 3, 4, 5, 6]:
                if len(unique_picks) >= combo_size:
                    picks = unique_picks.head(combo_size)
                    multiplier = self.platform_multipliers[platform][combo_size]
                    
                    # Calculate combo probability (assuming independence)
                    combo_prob = np.prod(picks['our_prob'])
                    combo_ev = (combo_prob * multiplier) - 1.0
                    
                    status = "SUCCESS: POSITIVE" if combo_ev > 0 else "ERROR: NEGATIVE"
                    print(f"  {combo_size}-Pick ({multiplier}x): Prob={combo_prob:.2%}, "
                          f"EV={combo_ev:.3f} {status}")
                    
                    if combo_ev > 0 and combo_size <= 3:  # Show details for smaller combos
                        for _, pick in picks.iterrows():
                            print(f"     {pick['player']} {pick['category']} {pick['line']} "
                                  f"({pick['our_prob']:.1%})")
    
    def run_analysis(self):
        """Run the complete fixed analysis"""
        
        print("STEP: FIXED PRIZEPICKS & UNDERDOG EV ANALYZER")
        print("=" * 60)
        
        # Load and clean data with proper calculations
        ev_df = self.load_and_clean_data()
        
        if len(ev_df) == 0:
            print("ERROR: No valid opportunities found after cleaning")
            return
        
        # Create platform sheets
        self.create_platform_sheets(ev_df)
        
        # Analyze combos
        self.analyze_best_combos(ev_df)
        
        # Summary
        print(f"\nDATA: SUMMARY:")
        print("=" * 25)
        for platform in ['prizepicks', 'underdog']:
            platform_ops = ev_df[ev_df['platform'] == platform]
            if len(platform_ops) > 0:
                avg_ev = platform_ops['expected_value'].mean()
                max_ev = platform_ops['expected_value'].max()
                high_conf = len(platform_ops[platform_ops['confidence'].isin(['HIGH', 'VERY_HIGH'])])
                print(f"{platform.title():10s}: {len(platform_ops):3d} opportunities, "
                      f"Avg EV: {avg_ev:.3f}, Max EV: {max_ev:.3f}, High Confidence: {high_conf}")

def main():
    try:
        from scipy.stats import norm
    except ImportError:
        print("WARNING: Installing scipy for probability calculations...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'scipy'])
        from scipy.stats import norm
    
    analyzer = FixedPlatformEVAnalyzer()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
