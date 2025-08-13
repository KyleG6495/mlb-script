#!/usr/bin/env python3
"""
run_daily_analysis_OPTIMIZED.py
FAST wrapper script for daily prop analysis - processes only confirmed starters
OPTIMIZED: ~60-80 players instead of 400K+
"""

from automated_betting_system import AutomatedBettingSystem
from datetime import datetime
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_active_players_count():
    """Get count of active players for validation"""
    confirmed_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_confirmed_starters_only.csv"
    if os.path.exists(confirmed_file):
        try:
            df = pd.read_csv(confirmed_file)
            return len(df)
        except:
            return 0
    return 0

def main():
    print("🚀 OPTIMIZED Daily ML Analysis - Confirmed Starters Only")
    print("=" * 60)
    
    # Validate we're using the right dataset
    active_count = get_active_players_count()
    print(f"📊 Processing {active_count} confirmed starters (not 400K+ players)")
    
    if active_count > 1000:
        print("❌ WARNING: Still processing too many players!")
        print("   Expected: ~60-80 confirmed starters")
        print(f"   Actual: {active_count} players")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return
    
    try:
        print("\n🎯 Starting analysis...")
        system = AutomatedBettingSystem()
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📅 Running OPTIMIZED analysis for {today}")
        start_time = datetime.now()
        
        system.run_daily_analysis(today, min_edge=0.05)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        print("✅ Daily analysis completed successfully!")
        print(f"⏱️ Total time: {duration:.1f} minutes")
        
        if duration > 20:
            print("⚠️ WARNING: Still taking too long - further optimization needed")
        else:
            print("🎉 GREAT: Analysis completed in reasonable time!")
        
    except Exception as e:
        print(f"❌ Error in daily analysis: {e}")
        raise

if __name__ == "__main__":
    main()
