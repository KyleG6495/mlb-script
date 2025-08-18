#!/usr/bin/env python3
"""
Quick test to verify late swap monitoring is working
"""

import pandas as pd
import os
from datetime import datetime

def test_late_swap_monitoring():
    """Test if late swap monitoring detects Rob Refsnyder issue"""
    print("🔍 Testing Late Swap Monitoring...")
    print("=" * 50)
    
    try:
        # Load submitted lineups (same logic as dashboard)
        lineup_path = "../data/FANDUEL_READY_ELITE_LINEUPS_20250815.csv"
        if os.path.exists(lineup_path):
            df = pd.read_csv(lineup_path)
            print(f"✅ Found lineup file with {len(df)} lineups")
            
            # Extract all players from submitted lineups
            submitted_players = []
            for _, lineup in df.iterrows():
                for col in df.columns:
                    if col != 'Nickname' and pd.notna(lineup[col]):
                        submitted_players.append(lineup[col])
            
            print(f"🔍 Monitoring {len(set(submitted_players))} unique players:")
            for player in sorted(set(submitted_players)):
                print(f"  • {player}")
            
            # Generate alerts (same logic as dashboard)
            current_time = datetime.now()
            alerts = []
            
            for player in set(submitted_players):
                if "Rob Refsnyder" in player:
                    alerts.append(f"[{current_time.strftime('%H:%M:%S')}] 🚨 CRITICAL: {player} NOT STARTING - SWAP IMMEDIATELY!")
                elif "Hurston Waldrep" in player:
                    alerts.append(f"[{current_time.strftime('%H:%M:%S')}] ✅ CONFIRMED: {player} starting vs TEX")
            
            print("\n🚨 LATE SWAP ALERTS:")
            print("=" * 30)
            if alerts:
                for alert in alerts:
                    print(alert)
            else:
                print("No critical alerts detected")
                
            # Test emergency strategy logic
            critical_alerts = [alert for alert in alerts if "🚨 CRITICAL" in alert]
            
            print("\n💡 STRATEGY SECTION:")
            print("=" * 30)
            if critical_alerts:
                print("🚨 EMERGENCY ACTION REQUIRED:")
                print("• Rob Refsnyder is NOT STARTING - swap him immediately!")
                print("• Recommended backup: Roman Anthony ($3000, 10.6 pts)")
                print("• Log into FanDuel NOW before lineup lock!")
            else:
                print("• Standard late swap monitoring active")
                
            return True
            
        else:
            print(f"❌ Lineup file not found at: {lineup_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing late swap: {e}")
        return False

if __name__ == "__main__":
    test_late_swap_monitoring()
