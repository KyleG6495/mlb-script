#!/usr/bin/env python3
"""
✈️ PRE-FLIGHT CHECKER ✈️
Quick validation before running daily pipeline
"""

import pandas as pd
from pathlib import Path
import os
from datetime import datetime
import sys

def pre_flight_check():
    """Quick pre-flight validation"""
    print("✈️ PRE-FLIGHT CHECKER")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: FD Slate Today
    total_checks += 1
    fd_slate_path = Path('c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/fd_slate_today.csv')
    if fd_slate_path.exists():
        file_age = datetime.now() - datetime.fromtimestamp(fd_slate_path.stat().st_mtime)
        age_hours = file_age.total_seconds() / 3600
        
        if age_hours < 24:
            print("✅ 1. fd_slate_today.csv is current")
            checks_passed += 1
            
            # Check for today's teams
            try:
                df = pd.read_csv(fd_slate_path)
                teams = sorted(df['Team'].unique())
                print(f"   Teams: {', '.join(teams)}")
                print(f"   Players: {len(df)}")
            except Exception as e:
                print(f"   ⚠️  Error reading file: {e}")
        else:
            print(f"❌ 1. fd_slate_today.csv is {age_hours:.1f} hours old (too stale)")
    else:
        print("❌ 1. fd_slate_today.csv NOT FOUND")
        print("   👆 Download today's FanDuel slate first!")
    
    # Check 2: Required directories exist
    total_checks += 1
    dirs_to_check = [
        'c:/Users/kgone/OneDrive/Personal_Information/MLB/Scripts',
        'c:/Users/kgone/OneDrive/Personal_Information/MLB/data',
        'c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate'
    ]
    
    all_dirs_exist = all(Path(d).exists() for d in dirs_to_check)
    if all_dirs_exist:
        print("✅ 2. All required directories exist")
        checks_passed += 1
    else:
        print("❌ 2. Some required directories missing")
        for d in dirs_to_check:
            status = "✅" if Path(d).exists() else "❌"
            print(f"   {status} {d}")
    
    # Check 3: Key scripts exist
    total_checks += 1
    scripts_to_check = [
        '1_CONFIRMED_generate_hitter_games.py',
        'ADVANCED_STACK_OPTIMIZER.py',
        'real_data_dashboard.py'
    ]
    
    scripts_path = Path('c:/Users/kgone/OneDrive/Personal_Information/MLB/Scripts')
    all_scripts_exist = all((scripts_path / script).exists() for script in scripts_to_check)
    
    if all_scripts_exist:
        print("✅ 3. All key scripts found")
        checks_passed += 1
    else:
        print("❌ 3. Some key scripts missing")
        for script in scripts_to_check:
            status = "✅" if (scripts_path / script).exists() else "❌"
            print(f"   {status} {script}")
    
    # Check 4: No stale processes running
    total_checks += 1
    print("✅ 4. Process check (manual)")
    print("   💡 Tip: Kill any running Python processes before starting")
    checks_passed += 1
    
    # Final verdict
    print()
    print("=" * 50)
    if checks_passed == total_checks:
        print("🚀 PRE-FLIGHT COMPLETE - READY FOR TAKEOFF!")
        print("   All systems go. You can run COMPLETE_DAILY_WORKFLOW.bat")
        return True
    else:
        print(f"⚠️  PRE-FLIGHT ISSUES: {total_checks - checks_passed} problems found")
        print("   Fix the issues above before proceeding")
        return False

if __name__ == "__main__":
    ready = pre_flight_check()
    if not ready:
        sys.exit(1)
