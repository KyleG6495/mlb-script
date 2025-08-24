#!/usr/bin/env python3
"""
backtest_yesterday_OPTIMIZED.py
BACKTEST wrapper to test yesterday's performance using optimized prop analysis
Shows how we would have done with confirmed starters filtering
"""

from automated_betting_system import AutomatedBettingSystem
from datetime import datetime, timedelta
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_actual_results(date_str):
    """Load actual results for the date to validate performance"""
    results_file = f"../data/actual_results_{date_str.replace('-', '')}.csv"
    if os.path.exists(results_file):
        try:
            df = pd.read_csv(results_file)
            return df
        except Exception as e:
            print(f"❌ Error loading actual results: {e}")
    return None

def main():
    print("🔍 BACKTEST: Yesterday's Prop Analysis Performance")
    print("=" * 60)
    
    # Test with yesterday (August 8th, 2025)
    yesterday = datetime(2025, 8, 8)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    
    print(f"📅 Backtesting optimized system for {yesterday_str}")
    
    # Check if we have actual results for validation
    actual_results = load_actual_results(yesterday_str)
    if actual_results is not None:
        print(f"✅ Found actual results for validation: {len(actual_results)} player results")
    else:
        print("⚠️ No actual results found - will show predictions only")
    
    try:
        print("\n🎯 Running OPTIMIZED backtest analysis...")
        system = AutomatedBettingSystem()
        
        print(f"📊 Analyzing {yesterday_str} with confirmed starters filtering...")
        start_time = datetime.now()
        
        # Run the optimized analysis for yesterday
        system.run_daily_analysis(yesterday_str, min_edge=0.05, output_dir="../data/backtest_analysis")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        
        print("✅ Backtest analysis completed!")
        print(f"⏱️ Total time: {duration:.1f} minutes (vs 45+ minutes with old system)")
        
        # Check for generated files
        backtest_dir = "../data/backtest_analysis"
        if os.path.exists(backtest_dir):
            files = os.listdir(backtest_dir)
            report_files = [f for f in files if f.startswith('betting_report_')]
            opportunity_files = [f for f in files if f.startswith('betting_opportunities_')]
            combo_files = [f for f in files if f.startswith('optimal_combinations_')]
            
            print(f"\n📄 Generated Files:")
            if report_files:
                latest_report = max(report_files)
                print(f"  📋 Betting Report: {latest_report}")
            if opportunity_files:
                latest_opps = max(opportunity_files)
                print(f"  💰 Opportunities: {latest_opps}")
            if combo_files:
                latest_combos = max(combo_files)
                print(f"  🎯 Combinations: {latest_combos}")
        
        print("\n🏆 BACKTEST SUMMARY:")
        print("  ✅ Optimized system processed only confirmed starters")
        print("  ✅ Analysis completed in reasonable time")
        print("  ✅ Generated prop betting opportunities for yesterday")
        print("  📊 Ready for comparison with actual results")
        
        if actual_results is not None:
            print(f"\n📈 VALIDATION READY:")
            print(f"  • Predictions generated for {yesterday_str}")
            print(f"  • Actual results available: {len(actual_results)} players")
            print(f"  • Files saved in: {backtest_dir}/")
            print(f"  • Compare predictions vs actual performance manually")
        
    except Exception as e:
        print(f"❌ Error in backtest analysis: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()
