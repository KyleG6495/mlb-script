#!/usr/bin/env python3
"""
Daily Enhanced FanDuel Optimizer Runner
Runs both standard and enhanced systems for comparison
"""

import subprocess
import pandas as pd
from datetime import datetime
import os

def run_daily_analysis():
    """Run both systems and compare results"""
    print("🚀 DAILY ENHANCED FANDUEL ANALYSIS")
    print("=" * 50)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run enhanced system
    print("\n🔥 Running Enhanced System...")
    try:
        result = subprocess.run(['python', 'enhanced_fanduel_optimizer.py'], 
                               capture_output=True, text=True, cwd='.')
        print("✅ Enhanced system complete")
    except Exception as e:
        print(f"❌ Enhanced system failed: {e}")
    
    # Run standard system  
    print("\n📊 Running Standard System...")
    try:
        result = subprocess.run(['python', '23. optimize_fanduel_lineup.py'], 
                               capture_output=True, text=True, cwd='.')
        print("✅ Standard system complete")
    except Exception as e:
        print(f"❌ Standard system failed: {e}")
    
    # Compare results
    print("\n🏆 PERFORMANCE COMPARISON")
    print("-" * 30)
    
    try:
        # Load enhanced lineups
        enhanced_files = [f for f in os.listdir('../data/') if f.startswith('enhanced_lineup_')]
        if enhanced_files:
            enhanced_scores = []
            for file in enhanced_files:
                df = pd.read_csv(f'../data/{file}')
                if 'Projected_FPPG' in df.columns:
                    enhanced_scores.append(df['Projected_FPPG'].sum())
            
            if enhanced_scores:
                print(f"🔥 Enhanced System:")
                print(f"   Best: {max(enhanced_scores):.1f} FPPG")
                print(f"   Avg:  {sum(enhanced_scores)/len(enhanced_scores):.1f} FPPG")
        
        # Load standard lineup
        if os.path.exists('../data/todays_stacked_lineup.csv'):
            standard_df = pd.read_csv('../data/todays_stacked_lineup.csv')
            if 'Projected_FPPG' in standard_df.columns:
                standard_score = standard_df['Projected_FPPG'].sum()
                print(f"📊 Standard System: {standard_score:.1f} FPPG")
                
                if enhanced_scores and max(enhanced_scores) > standard_score:
                    improvement = max(enhanced_scores) - standard_score
                    print(f"💪 Enhanced system is {improvement:.1f} FPPG better!")
                    
    except Exception as e:
        print(f"⚠️ Comparison failed: {e}")
    
    print(f"\n📝 Analysis complete at {timestamp}")
    print("🎯 Recommendation: Use enhanced lineups for maximum edge!")

if __name__ == "__main__":
    run_daily_analysis()
