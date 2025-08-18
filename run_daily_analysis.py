#!/usr/bin/env python3
"""
run_daily_analysis.py
Quick wrapper script to run the daily betting analysis
"""

from automated_betting_system import AutomatedBettingSystem
from datetime import datetime

def main():
    print("TARGET: Starting Daily ML Analysis...")
    
    try:
        system = AutomatedBettingSystem()
        today = datetime.now().strftime('%Y-%m-%d')
        
        print(f" Running analysis for {today}")
        system.run_daily_analysis(today, min_edge=0.05)
        
        print("SUCCESS: Daily analysis completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Error in daily analysis: {e}")
        raise

if __name__ == "__main__":
    main()
