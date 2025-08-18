#!/usr/bin/env python3
"""
TESTING VERSION OF DASHBOARD - Uses yesterday's date (20250817)
This allows us to test all fixes with existing data before moving to fresh data
"""
import sys
import os

# Add the current directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the original dashboard
from WORKING_DASHBOARD import WorkingDashboard

# Monkey patch the date to use yesterday for testing
import datetime
original_now = datetime.datetime.now

def test_datetime_now():
    """Return yesterday's date for file searching"""
    return datetime.datetime(2025, 8, 17, 17, 9, 27)  # August 17th, 5:09 PM

# Apply the patch
datetime.datetime.now = test_datetime_now

print("🧪 TESTING DASHBOARD WITH YESTERDAY'S DATA (20250817)")
print("=" * 60)
print("📅 All file searches will use August 17th date")
print("📊 This tests stack analysis and FanDuel CSV with existing data")
print("🔧 Once working, we'll switch to fresh data")
print()

if __name__ == "__main__":
    try:
        app = WorkingDashboard()
        app.run()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard closed")
    finally:
        # Restore original datetime
        datetime.datetime.now = original_now
        print("📅 DateTime restored to normal")
