#!/usr/bin/env python3
"""
STABLE DASHBOARD LAUNCHER FOR TONIGHT'S SLATE
Starts dashboard with optimized settings for 7:15 PM slate
"""

import sys
import os
from datetime import datetime

def launch_stable_dashboard():
    """Launch dashboard with stable settings for tonight's slate"""
    print("🏆 STABLE DFS DASHBOARD FOR TONIGHT'S 7:15 PM SLATE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to the correct directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    
    try:
        # Import and start dashboard
        from WORKING_DASHBOARD import WorkingDashboard
        
        print("✅ Dashboard imported successfully")
        print("📊 Loading tonight's FD slate...")
        
        # Create dashboard instance
        app = WorkingDashboard()
        print("✅ Dashboard instance created")
        print("🎯 Dashboard ready for tonight's slate!")
        print("")
        print("💡 TIPS FOR TONIGHT:")
        print("   • Use manual refresh buttons to avoid hanging")
        print("   • Check 'Lineup Status' tab for confirmed lineups")
        print("   • Focus on LAA, COL, ARI stacks per analysis")
        print("   • Auto-refresh is OFF by default for stability")
        print("")
        
        # Run the dashboard
        app.run()
        
        print("✅ Dashboard session completed")
        
    except Exception as e:
        print(f"❌ Dashboard error: {str(e)}")
        print("💡 Try running: python WORKING_DASHBOARD.py directly")
        return False
    
    return True

if __name__ == "__main__":
    try:
        launch_stable_dashboard()
    except Exception as e:
        print(f"❌ Launcher error: {str(e)}")
    
    input("\\nPress Enter to exit...")
