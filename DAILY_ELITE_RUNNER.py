#!/usr/bin/env python3
"""
🎯 DAILY ELITE RUNNER
Daily execution script for Elite MLB System
"""

import os
import subprocess
import datetime

def run_daily_elite_system():
    """Run the complete elite system daily"""
    print("🎯 ELITE MLB DAILY EXECUTION")
    print("=" * 50)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"⏰ Starting at: {timestamp}")
    
    try:
        # Run the elite system
        result = subprocess.run(['python', 'LAUNCH_ELITE_SYSTEM.py'], 
                              capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            print("✅ Elite system executed successfully!")
            print(f"📊 Execution complete at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("⚠️ System completed with warnings")
            print("📋 Check logs for details")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        
    print("\n🎯 DAILY EXECUTION COMPLETE")
    print("📁 Check generated files for results")
    print("📊 Check elite_logs/ for detailed logs")

if __name__ == "__main__":
    run_daily_elite_system()
