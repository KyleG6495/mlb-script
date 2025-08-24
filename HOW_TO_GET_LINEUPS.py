#!/usr/bin/env python3
"""
🎯 HOW TO GET YOUR LINEUPS FOR CONTEST ENTRY

This guide shows you exactly how to get the actual CSV files for FanDuel upload.
"""

print("🎯 HOW TO GET YOUR CONTEST-READY LINEUPS")
print("=" * 60)
print()

print("📋 METHOD 1: Use the Dashboard (Recommended)")
print("1. Run: python COMPLETE_ELITE_DFS_DASHBOARD.py")
print("2. Go to the '🎯 Lineup Selector' tab")
print("3. Click: '🎯 Select Optimal Lineups' (wait for analysis)")
print("4. Click: '📁 Export CSV Files' (creates actual files)")
print("5. Check the 'Debug' tab for export confirmation")
print("6. Files saved in: fd_current_slate/ folder")
print()

print("📋 METHOD 2: Command Line")
print("1. Run: python ELITE_LINEUP_SELECTOR.py")
print("2. Run: python EXPORT_SELECTED_LINEUPS.py") 
print("3. Files created in: fd_current_slate/ folder")
print()

print("📁 YOUR EXPORTED FILES WILL BE NAMED:")
print("• RECOMMENDED_cash_games_[LineupID]_[timestamp].csv")
print("• RECOMMENDED_small_tournaments_[LineupID]_[timestamp].csv") 
print("• RECOMMENDED_large_tournaments_[LineupID]_[timestamp].csv")
print()

print("🎯 CONTEST STRATEGY:")
print("💰 Cash Games: Use the cash_games file (high floor, safe)")
print("🎯 Small Tournaments: Use small_tournaments file (balanced)")
print("🚀 Large Tournaments: Use large_tournaments file (max ceiling)")
print()

print("📤 TO UPLOAD TO FANDUEL:")
print("1. Go to FanDuel contest entry page")
print("2. Click 'Upload Lineups'")
print("3. Select the appropriate RECOMMENDED_*.csv file")
print("4. Upload and enter contest!")
print()

print("✅ You now have scientifically optimized lineups for each contest type! 🚀")
