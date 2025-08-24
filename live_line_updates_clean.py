#!/usr/bin/env python3
"""
Live Line Updates System
Refresh sportsbook data and create live monitoring infrastructure
"""

import os
import pandas as pd
import sys
from datetime import datetime

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(os.path.dirname(script_dir), "data")

def refresh_prizepicks_data():
    """Refresh PrizePicks data if source exists"""
    print("Refreshing PrizePicks data...")
    
    source_file = os.path.join(data_dir, "prizepicks_props.csv")
    live_file = os.path.join(data_dir, "prizepicks_props_live.csv")
    
    if os.path.exists(source_file):
        df = pd.read_csv(source_file)
        df.to_csv(live_file, index=False)
        print(f"   Updated live file with {len(df)} PrizePicks props")
        return df
    else:
        print("   No existing PrizePicks data found")
        return None

def refresh_underdog_data():
    """Refresh Underdog data if source exists"""
    print("Refreshing Underdog data...")
    
    source_file = os.path.join(data_dir, "underdog_props.csv")
    live_file = os.path.join(data_dir, "underdog_props_live.csv")
    
    if os.path.exists(source_file):
        df = pd.read_csv(source_file)
        df.to_csv(live_file, index=False)
        print(f"   Updated live file with {len(df)} Underdog props")
        return df
    else:
        print("   No existing Underdog data found")
        return None

def create_live_betting_runner():
    """Create the live betting runner script"""
    
    live_runner_code = '''#!/usr/bin/env python3
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
'''
    
    runner_path = os.path.join(script_dir, 'live_betting_runner.py')
    with open(runner_path, 'w', encoding='utf-8') as f:
        f.write(live_runner_code)
    
    return runner_path

def main():
    """Main execution function"""
    print("LIVE LINE UPDATES SYSTEM")
    print("=" * 50)
    
    print("1. Testing line refresh functions...")
    refresh_prizepicks_data()
    refresh_underdog_data()
    
    print("\n2. Creating live betting infrastructure...")
    runner_path = create_live_betting_runner()
    print(f"   Live betting runner created: {runner_path}")
    
    print("\n3. Installing required packages...")
    try:
        import schedule
        print("   schedule package already installed")
    except ImportError:
        print("   Installing schedule package...")
        os.system("pip install schedule")
    
    print("\nLIVE SYSTEM SETUP COMPLETE!")
    print("=" * 50)
    print("To start live monitoring:")
    print("  python live_betting_runner.py")
    print("\nFeatures:")
    print("  - Automatic line refreshes every 30 minutes")
    print("  - Betting analysis every 15 minutes")
    print("  - Continuous opportunity monitoring")
    print("  - Real-time status updates")

if __name__ == "__main__":
    main()
