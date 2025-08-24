#!/usr/bin/env python3
"""
BATTING ORDER CHECKER
====================
Quick script to check if batting orders have been posted in the FanDuel slate.
"""

import pandas as pd
import sys
from pathlib import Path

def check_batting_orders():
    """Check if batting orders are available in the slate"""
    slate_file = Path("../fd_current_slate/fd_slate_today.csv")
    
    if not slate_file.exists():
        print("ERROR: fd_slate_today.csv not found")
        return False
    
    try:
        df = pd.read_csv(slate_file)
        
        # Check non-pitcher players
        non_pitchers = df[df['Position'] != 'P']
        
        # Count players with valid batting orders
        valid_batting_orders = non_pitchers[
            ~non_pitchers['Batting Order'].isin(['0', '0.0', 'nan', '', None]) &
            non_pitchers['Batting Order'].notna()
        ]
        
        total_non_pitchers = len(non_pitchers)
        valid_count = len(valid_batting_orders)
        
        print(f"DATA: Batting Order Status:")
        print(f"   Total non-pitchers: {total_non_pitchers}")
        print(f"   With batting orders: {valid_count}")
        print(f"   Percentage available: {(valid_count/total_non_pitchers*100):.1f}%")
        
        if valid_count >= 50:  # Need at least 50 players with batting orders
            print("SUCCESS: Sufficient batting orders available for ML DFS optimization")
            return True
        else:
            print("WARNING: Insufficient batting orders - use quintuple backup system")
            return False
            
    except Exception as e:
        print(f"ERROR: Error checking batting orders: {e}")
        return False

if __name__ == "__main__":
    available = check_batting_orders()
    sys.exit(0 if available else 1)
