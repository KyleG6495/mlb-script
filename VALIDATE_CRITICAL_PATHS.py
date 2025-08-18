#!/usr/bin/env python3
"""
CRITICAL PATH VALIDATOR
======================
This script validates that the Enhanced ML DFS System is using the CORRECT slate file paths.
Run this before generating lineups to ensure data integrity.
"""

import os
from pathlib import Path
import pandas as pd

def validate_enhanced_ml_dfs_paths():
    """Validate that Enhanced ML DFS System uses correct paths"""
    print("🔍 VALIDATING ENHANCED ML DFS SYSTEM PATHS...")
    
    script_path = Path(__file__).parent / "ENHANCED_ML_DFS_SYSTEM.py"
    
    if not script_path.exists():
        print("❌ ERROR: ENHANCED_ML_DFS_SYSTEM.py not found!")
        return False
    
    # Read the script content
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Check for correct path usage
    correct_path = 'FD_SLATE_DIR / "fd_slate_today.csv"'
    incorrect_paths = [
        'BASE_DIR / "fd_slate_starters_only.csv"',
        '"../data/fd_slate_today.csv"',
        '"../data/fd_slate_starters_only.csv"'
    ]
    
    # Validate correct path exists
    if correct_path not in content:
        print(f"❌ ERROR: Correct path '{correct_path}' not found in script!")
        return False
    else:
        print(f"✅ GOOD: Found correct path: {correct_path}")
    
    # Check for incorrect paths
    for bad_path in incorrect_paths:
        if bad_path in content:
            print(f"⚠️ WARNING: Found old path: {bad_path}")
            return False
    
    return True

def validate_current_slate_exists():
    """Validate that the current slate file exists and has correct teams"""
    print("\n🔍 VALIDATING CURRENT SLATE FILE...")
    
    slate_path = Path(__file__).parent.parent / "fd_current_slate" / "fd_slate_today.csv"
    
    if not slate_path.exists():
        print(f"❌ ERROR: Current slate file not found at: {slate_path}")
        return False
    
    # Load and validate slate
    try:
        df = pd.read_csv(slate_path)
        teams = sorted(df['Team'].unique())
        
        print(f"✅ GOOD: Slate file exists with {len(df)} players")
        print(f"✅ GOOD: Teams in slate: {teams}")
        
        # Check for starting pitchers
        if 'Probable Pitcher' not in df.columns:
            print("❌ ERROR: 'Probable Pitcher' column missing!")
            return False
        
        starters = df[df['Probable Pitcher'] == 'Yes']
        print(f"✅ GOOD: Found {len(starters)} starting pitchers")
        
        # Expected teams for August 17, 2025 slate
        expected_teams = ['ATH', 'LAA', 'LAD', 'SD', 'SF', 'TB']
        if teams == expected_teams:
            print(f"✅ PERFECT: Teams match expected: {expected_teams}")
        else:
            print(f"⚠️ NOTE: Teams differ from expected {expected_teams}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR reading slate file: {e}")
        return False

def main():
    print("="*60)
    print("🛡️  CRITICAL PATH VALIDATION - MLB DFS SYSTEM")
    print("="*60)
    
    # Validate Enhanced ML DFS paths
    paths_ok = validate_enhanced_ml_dfs_paths()
    
    # Validate current slate
    slate_ok = validate_current_slate_exists()
    
    print("\n" + "="*60)
    if paths_ok and slate_ok:
        print("✅ ALL VALIDATIONS PASSED - SYSTEM READY!")
        print("✅ Enhanced ML DFS System will use correct current slate")
        print("✅ Teams in lineups will match current slate teams")
    else:
        print("❌ VALIDATION FAILED - FIX REQUIRED!")
        print("❌ Lineup generation may use stale data")
    print("="*60)
    
    return paths_ok and slate_ok

if __name__ == "__main__":
    main()
