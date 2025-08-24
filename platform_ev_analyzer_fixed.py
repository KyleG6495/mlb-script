#!/usr/bin/env python3
"""
PrizePicks & Underdog Fantasy Expected Value Analyzer (FIXED)
Creates clean sheets showing the best expected value opportunities for each platform
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

class PlatformEVAnalyzer:
    def __init__(self):
        self.platform_multipliers = {
            'prizepicks': {
                2: 3.0,    # 2-pick: 3x
                3: 6.0,    # 3-pick: 6x  
                4: 10.0,   # 4-pick: 10x
                5: 20.0,   # 5-pick: 20x
                6: 50.0    # 6-pick: 50x
            },
            'underdog': {
                2: 3.0,    # 2-pick: 3x
                3: 6.0,    # 3-pick: 6x
                4: 10.0,   # 4-pick: 10x
                5: 20.0,   # 5-pick: 20x
                6: 40.0    # 6-pick: 40x (different from PP)
            }
        }
        
    def load_prop_data(self):
        """Load today's prop predictions and opportunities"""
        
        # Try to load existing betting opportunities
        betting_files = [
            "../Scripts/betting_analysis/betting_opportunities_20250720_144550.csv",
            "../data/betting_opportunities_latest.csv",
            "../data/prop_predictions_today.csv"
        ]
        
        for file_path in betting_files:
            try:
                if os.path.exists(file_path):
                    print(f"DATA: Loading prop data from: {file_path}")
                    return pd.read_csv(file_path)
            except Exception as e:
                continue
        
        # If no existing file, create sample data
        print("WARNING: No existing prop data found, generating sample...")
        return self.generate_sample_props()
    
    def process_existing_data(self, props_df):
        """Process existing betting opportunities data"""
        
        print(f"DATA: Processing {len(props_df)} existing opportunities...")
        
        # Filter to valid opportunities with reasonable expected values
        filtered_data = []
        
        for _, prop in props_df.iterrows():
            # Skip invalid data
            if pd.isna(prop.get('expected_value', 0)) or prop.get('expected_value', 0) <= 0:
                continue
                
            # Clean up expected value (some might be in wrong format)
            ev = prop['expected_value']
            if ev > 1.0:  # Likely in wrong units
                ev = ev / 100
                
            # Skip unrealistic EVs
            if ev > 0.5:  # 50% EV seems unrealistic
                continue
                
            # Get platform
            platform = prop.get('source', 'unknown')
            if platform not in ['prizepicks', 'underdog']:
                continue
                
            # Determine bet type and line display
            bet_type = prop.get('recommended_bet', 'UNKNOWN')
            line = prop.get('line', 0)
            
            if bet_type == 'OVER':
                line_display = f"O{line}"
                our_prob = prop.get('model_prob_over', 0.5)
            elif bet_type == 'UNDER':
                line_display = f"U{line}"
                our_prob = 1 - prop.get('model_prob_over', 0.5)
            else:
                continue
                
            filtered_data.append({
                'platform': platform,
                'player': prop.get('player', 'Unknown'),
                'category': prop.get('category', 'unknown'),
                'line': line_display,
                'bet_type': bet_type,
                'our_prob': our_prob,
                'implied_prob': prop.get('implied_prob', 0.524),
                'expected_value': ev,
                'edge': prop.get('edge', 0),
                'recommendation': 'YES' if ev > 0 else 'NO',
                'confidence': prop.get('confidence', 'MEDIUM'),
                'prediction': prop.get('prediction', 0)
            })
        
        print(f"SUCCESS: Filtered to {len(filtered_data)} valid opportunities")
        return pd.DataFrame(filtered_data)
    
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
        """Create separate sheets for PrizePicks and Underdog with best opportunities"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        for platform in ['prizepicks', 'underdog']:
            platform_data = ev_df[ev_df['platform'] == platform].copy()
            
            if len(platform_data) == 0:
                print(f"WARNING: No data found for {platform}")
                continue
            
            # Sort by expected value descending
            platform_data = platform_data.sort_values('expected_value', ascending=False)
            
            # Filter to only positive EV bets
            positive_ev = platform_data[platform_data['expected_value'] > 0].copy()
            
            if len(positive_ev) == 0:
                print(f"WARNING: No positive EV opportunities found for {platform}")
                continue
            
            # Add rank and format for display
            positive_ev['rank'] = range(1, len(positive_ev) + 1)
            positive_ev['ev_display'] = positive_ev['expected_value'].apply(lambda x: f"{x:.3f}")
            positive_ev['edge_display'] = positive_ev['edge'].apply(lambda x: f"{x:.1%}")
            positive_ev['prob_display'] = positive_ev['our_prob'].apply(lambda x: f"{x:.1%}")
            
            # Select key columns for the sheet
            sheet_columns = [
                'rank', 'player', 'category', 'line', 'bet_type',
                'prob_display', 'ev_display', 'edge_display', 
                'recommendation', 'confidence'
            ]
            
            final_sheet = positive_ev[sheet_columns].copy()
            final_sheet.columns = [
                'Rank', 'Player', 'Category', 'Line', 'Bet Type',
                'Our Probability', 'Expected Value', 'Edge %',
                'Recommendation', 'Confidence'
            ]
            
            # Save to CSV
            filename = f"../data/{platform}_best_ev_{timestamp}.csv"
            final_sheet.to_csv(filename, index=False)
            
            print(f" {platform.title()} sheet saved: {filename}")
            print(f"TARGET: Found {len(positive_ev)} positive EV opportunities")
            
            # Show top 10
            print(f"\nLINEUP: TOP 10 {platform.upper()} OPPORTUNITIES:")
            print("=" * 80)
            top_10 = final_sheet.head(10)
            for i, row in top_10.iterrows():
                print(f"{row['Rank']:2d}. {row['Player']:20s} {row['Category']:12s} {row['Line']:8s} "
                      f"EV:{row['Expected Value']:8s} Edge:{row['Edge %']:7s} {row['Confidence']:10s}")
    
    def create_combo_analysis(self, ev_df):
        """Analyze best combo opportunities"""
        
        print(f"\n COMBO OPPORTUNITY ANALYSIS")
        print("=" * 50)
        
        for platform in ['prizepicks', 'underdog']:
            platform_data = ev_df[
                (ev_df['platform'] == platform) & 
                (ev_df['expected_value'] > 0) &
                (ev_df['confidence'].isin(['HIGH', 'VERY_HIGH']))
            ].copy()
            
            if len(platform_data) < 2:
                print(f"WARNING: Not enough high-confidence bets for {platform} combos")
                continue
            
            print(f"\n {platform.upper()} COMBO RECOMMENDATIONS:")
            
            # Get top picks for combos
            top_picks = platform_data.nlargest(6, 'expected_value')
            
            for combo_size in [2, 3, 4, 5, 6]:
                if len(top_picks) >= combo_size:
                    picks_for_combo = top_picks.head(combo_size)
                    multiplier = self.platform_multipliers[platform][combo_size]
                    
                    # Calculate combo probability (assuming independence)
                    combo_prob = np.prod(picks_for_combo['our_prob'])
                    combo_ev = (combo_prob * multiplier) - 1.0
                    
                    print(f"  {combo_size}-Pick Combo ({multiplier}x): "
                          f"Prob={combo_prob:.1%}, EV={combo_ev:.3f}")
                    
                    if combo_ev > 0:
                        print(f"    SUCCESS: POSITIVE EV COMBO!")
                        for _, pick in picks_for_combo.iterrows():
                            print(f"       {pick['player']} {pick['category']} {pick['line']}")
    
    def run_full_analysis(self):
        """Run the complete EV analysis for both platforms"""
        
        print("TARGET: PRIZEPICKS & UNDERDOG FANTASY EV ANALYZER")
        print("=" * 60)
        
        # Load prop data
        props_df = self.load_prop_data()
        print(f"DATA: Loaded {len(props_df)} prop opportunities")
        
        # Process the data
        ev_df = self.process_existing_data(props_df)
        print(f"MONEY: Processed {len(ev_df)} valid betting opportunities")
        
        if len(ev_df) == 0:
            print("ERROR: No valid data to analyze")
            return
        
        # Create platform-specific sheets
        self.create_platform_sheets(ev_df)
        
        # Analyze combo opportunities  
        self.create_combo_analysis(ev_df)
        
        # Summary stats
        print(f"\nPROGRESS: SUMMARY STATISTICS:")
        print("=" * 30)
        
        for platform in ['prizepicks', 'underdog']:
            platform_positive_ev = ev_df[
                (ev_df['platform'] == platform) & 
                (ev_df['expected_value'] > 0)
            ]
            
            if len(platform_positive_ev) > 0:
                avg_ev = platform_positive_ev['expected_value'].mean()
                max_ev = platform_positive_ev['expected_value'].max()
                high_conf_count = len(platform_positive_ev[
                    platform_positive_ev['confidence'].isin(['HIGH', 'VERY_HIGH'])
                ])
                
                print(f"{platform.title():12s}: {len(platform_positive_ev):3d} +EV bets, "
                      f"Avg EV: {avg_ev:.3f}, Max EV: {max_ev:.3f}, "
                      f"High Confidence: {high_conf_count}")

def main():
    analyzer = PlatformEVAnalyzer()
    analyzer.run_full_analysis()

if __name__ == "__main__":
    main()
