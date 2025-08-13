#!/usr/bin/env python3
"""
Live Betting Runner - Continuous Monitoring System
"""
import sys
import os
import time
import schedule
from datetime import datetime, timedelta

def print_status(message):
    """Print status with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{timestamp}] {message}')

def run_betting_analysis():
    """Run the automated betting system"""
    print_status('Running automated betting analysis...')
    
    try:
        # Import and run the betting system
        from automated_betting_system import main as run_betting_system
        
        print_status('Analyzing opportunities...')
        run_betting_system()
        print_status('Analysis complete')
        
    except Exception as e:
        print_status(f'Error in betting analysis: {e}')
        return False
    
    return True

def refresh_lines():
    """Refresh sportsbook lines"""
    print_status('Refreshing sportsbook lines...')
    
    try:
        # Import line refresh functions
        from live_line_updates_clean import refresh_prizepicks_data, refresh_underdog_data
        
        # Refresh both sources
        refresh_prizepicks_data()
        refresh_underdog_data()
        
        print_status('Lines refreshed successfully')
        
    except Exception as e:
        print_status(f'Error refreshing lines: {e}')
        return False
    
    return True

def main():
    """Main live betting loop"""
    print_status('Starting Live Betting Runner')
    print_status('Setting up monitoring schedule...')
    
    # Schedule line refreshes every 30 minutes
    schedule.every(30).minutes.do(refresh_lines)
    
    # Schedule betting analysis every 15 minutes after line refresh
    schedule.every(15).minutes.do(run_betting_analysis)
    
    # Run initial analysis
    print_status('Running initial analysis...')
    refresh_lines()
    time.sleep(5)  # Brief pause
    run_betting_analysis()
    
    print_status('Starting continuous monitoring...')
    print_status('Press Ctrl+C to stop')
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print_status('Stopping live betting runner')
        print_status('Session complete')

if __name__ == '__main__':
    main()
