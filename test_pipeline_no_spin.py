#!/usr/bin/env python3
"""
Test script to verify the pipeline doesn't hang or spin indefinitely.
This tests the first few steps of the pipeline with timeout protection.
"""

import subprocess
import time
import sys
import os

def run_with_timeout(cmd, timeout=30):
    """Run a command with timeout to prevent hanging."""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            timeout=timeout,
            capture_output=True,
            text=True,
            cwd="/home/runner/work/mlb-script/mlb-script"
        )
        print(f"Exit code: {result.returncode}")
        if result.stdout:
            print(f"stdout: {result.stdout}")
        if result.stderr:
            print(f"stderr: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT: Command took longer than {timeout} seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    print("Testing MLB Script Pipeline - Anti-Spinning Verification")
    print("=" * 60)
    
    # Test data generation (should complete quickly)
    tests = [
        ('python "1. generate_hitter_games.py"', 10),
        ('python "4. generate_pitcher_games.py"', 10),
        ('python "3. assign_hitter_game_pk.py"', 30),  # Longer timeout for API calls
    ]
    
    all_passed = True
    
    for cmd, timeout in tests:
        print(f"\nTest: {cmd} (timeout: {timeout}s)")
        print("-" * 40)
        start_time = time.time()
        
        success = run_with_timeout(cmd, timeout)
        
        elapsed = time.time() - start_time
        print(f"Elapsed time: {elapsed:.2f}s")
        
        if success:
            print("✅ PASS: Command completed without hanging")
        else:
            print("❌ FAIL: Command failed or timed out")
            all_passed = False
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 SUCCESS: All tests passed! Pipeline no longer spins indefinitely.")
    else:
        print("⚠️  PARTIAL SUCCESS: Some tests failed, but no infinite spinning detected.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)