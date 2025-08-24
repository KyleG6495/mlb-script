#!/usr/bin/env python3
"""
Quick backtest of the filtered lineup
"""

import pandas as pd
from pathlib import Path

# Filtered lineup players
filtered_players = [
    "Framber Valdez",
    "Juan Yepez", 
    "Nick Yorke",
    "Colson Montgomery",
    "Charles Leblanc",
    "Brewer Hicklen",
    "Jonny DeLuca",
    "Rhylan Thomas",
    "Diego A. Castillo"
]

# Load actual results
data_dir = Path(__file__).parent.parent / "data"
actual_file = data_dir / "actual_results_latest.csv"

if actual_file.exists():
    actual_df = pd.read_csv(actual_file)
    
    total_actual = 0
    print("🎯 FILTERED LINEUP BACKTEST:")
    print("="*50)
    
    for player_name in filtered_players:
        # Find player in actual results
        player_row = actual_df[actual_df['name'].str.contains(player_name, case=False, na=False)]
        
        if not player_row.empty:
            actual_fppg = player_row.iloc[0].get('fanduel_points', 0)
            total_actual += actual_fppg
            print(f"✅ {player_name:20}: {actual_fppg:5.1f} FPPG")
        else:
            print(f"❌ {player_name:20}: 0.0 FPPG (not found)")
    
    print("="*50)
    print(f"🏆 TOTAL ACTUAL FPPG: {total_actual:.1f}")
    print(f"📊 Projected: 119.4 FPPG")
    print(f"🎪 Accuracy: {(total_actual/119.4)*100:.1f}%")
    
    if total_actual > 100:
        print("🔥 EXCELLENT performance!")
    elif total_actual > 60:
        print("✅ Good performance!")
    else:
        print("⚠️ Needs improvement")

else:
    print("❌ No actual results file found")
