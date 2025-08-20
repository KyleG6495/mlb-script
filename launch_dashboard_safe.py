#!/usr/bin/env python3
"""
SAFE DASHBOARD LAUNCHER
Starts the dashboard with error recovery and restart capabilities
"""

import sys
import os
import time
import subprocess
from datetime import datetime

def restart_dashboard():
    """Restart the dashboard with safety checks"""
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\\n🚀 Dashboard Launch Attempt {attempt}/{max_attempts}")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # Start dashboard
            from WORKING_DASHBOARD import WorkingDashboard
            
            print("✅ Dashboard imported successfully")
            
            # Create and run dashboard
            app = WorkingDashboard()
            print("✅ Dashboard instance created")
            
            # Run the dashboard
            print("🎯 Starting dashboard UI...")
            app.run()
            
            # If we get here, the user closed the dashboard normally
            print("✅ Dashboard closed normally")
            break
            
        except KeyboardInterrupt:
            print("\\n⏹️ Dashboard stopped by user (Ctrl+C)")
            break
            
        except Exception as e:
            print(f"❌ Dashboard error: {str(e)}")
            
            if attempt < max_attempts:
                print(f"⏳ Waiting 5 seconds before retry...")
                time.sleep(5)
            else:
                print("❌ Max attempts reached. Dashboard failed to start.")
                return False
    
    return True

def main():
    """Main launcher function"""
    print("🏆 ELITE DFS DASHBOARD - SAFE LAUNCHER")
    print("=" * 50)
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    # Check for required files
    required_files = [
        "WORKING_DASHBOARD.py",
        "file_finder_utils.py"
    ]
    
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"❌ Required file missing: {file_name}")
            return False
    
    print("✅ All required files found")
    
    # Start dashboard with restart capability
    success = restart_dashboard()
    
    if success:
        print("\\n✅ Dashboard session completed")
    else:
        print("\\n❌ Dashboard failed to start")
        print("💡 Try running: python WORKING_DASHBOARD.py directly")
    
    return success

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\\n❌ Launcher error: {str(e)}")
        print("💡 Try running the dashboard directly")
    
    input("\\nPress Enter to exit...")
