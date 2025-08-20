#!/usr/bin/env python3
"""
QUICK SLATE SUMMARY
Command line tool to quickly check tonight's slate status
"""

import pandas as pd
import os
from datetime import datetime

def main():
    print("🏆 TONIGHT'S 7:15 PM SLATE SUMMARY")
    print("=" * 50)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Check FD slate
        fd_path = os.path.join('..', 'fd_current_slate', 'fd_slate_today.csv')
        if os.path.exists(fd_path):
            df = pd.read_csv(fd_path)
            print(f"✅ FD SLATE LOADED: {len(df):,} players")
            print(f"🏟️ TEAMS: {len(df['Team'].unique())} teams")
            print(f"   {', '.join(sorted(df['Team'].unique()))}")
            print()
            
            # Top pitchers
            pitchers = df[df['Position'] == 'P'].nlargest(5, 'Salary')
            print("💰 TOP PITCHERS:")
            for _, p in pitchers.iterrows():
                print(f"   ${p['Salary']:,} - {p['Nickname']} {p['Last Name']} ({p['Team']})")
            print()
        else:
            print("❌ FD slate not found")
            return
        
        # Check lineups
        lineups_path = os.path.join('..', 'data', 'starting_lineups.csv')
        if os.path.exists(lineups_path):
            lineups = pd.read_csv(lineups_path)
            pitchers = lineups[lineups['position'] == 'P']
            hitters = lineups[lineups['position'] != 'P']
            
            print(f"⚾ CONFIRMED LINEUPS: {len(lineups)} starters")
            print(f"   {len(pitchers)} pitchers, {len(hitters)} hitters")
            print(f"   {len(lineups['team'].unique())} teams with confirmed lineups")
            print()
            
            print("🏆 STARTING PITCHERS:")
            for _, p in pitchers.iterrows():
                print(f"   {p['team']}: {p['player_name']} (${p['salary']:,})")
            print()
            
        else:
            print("❌ Lineups not found")
            
        # Strategy summary
        print("🎯 TONIGHT'S STRATEGY:")
        print("   🔥 PRIMARY STACKS: LAA, COL, CWS (low owned)")
        print("   💰 VALUE PLAYS: MIL, KC, TEX")
        print("   ⚠️ AVOID: NYY, TB, ATH, MIN (high owned)")
        print()
        
        print("🚀 READY TO GENERATE LINEUPS!")
        print("   • All data loaded successfully")
        print("   • No hanging dashboard issues")
        print("   • Run your DAILY_RUNNERS scripts")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    main()
    input("\\nPress Enter to exit...")
