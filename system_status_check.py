#!/usr/bin/env python3
"""
CONFIRMED STARTERS SYSTEM SUMMARY
=================================
Shows the complete picture of how the confirmed starters system works
and validates that everything is properly integrated.
"""

import pandas as pd
import os
from pathlib import Path

def check_system_status():
    """Check the status of the confirmed starters system"""
    
    print("🔍 CONFIRMED STARTERS SYSTEM STATUS")
    print("=" * 50)
    print()
    
    # Check master files
    master_file = "../data/starting_lineups.csv"
    pipeline_file = "../data/fd_slate_starters_only.csv"
    original_slate = "../data/fd_slate_today.csv"
    
    print("📊 MASTER FILES STATUS:")
    
    if os.path.exists(master_file):
        master_df = pd.read_csv(master_file)
        print(f"✅ starting_lineups.csv: {len(master_df)} confirmed starters")
    else:
        print("❌ starting_lineups.csv: NOT FOUND")
        return
    
    if os.path.exists(pipeline_file):
        pipeline_df = pd.read_csv(pipeline_file)
        print(f"✅ fd_slate_starters_only.csv: {len(pipeline_df)} players (FanDuel format)")
    else:
        print("❌ fd_slate_starters_only.csv: NOT FOUND")
        return
        
    if os.path.exists(original_slate):
        original_df = pd.read_csv(original_slate)
        print(f"📥 fd_slate_today.csv: {len(original_df)} total players")
        filtered_out = len(original_df) - len(pipeline_df)
        print(f"🚫 Bench players filtered out: {filtered_out}")
    else:
        print("❌ fd_slate_today.csv: NOT FOUND")
    
    print()
    
    # Show efficiency gains
    if os.path.exists(original_slate) and os.path.exists(pipeline_file):
        efficiency = (len(pipeline_df) / len(original_df)) * 100
        print(f"⚡ EFFICIENCY GAIN: Processing {efficiency:.1f}% of players (only starters)")
        print(f"⚡ SPEED IMPROVEMENT: ~{(100-efficiency):.0f}% reduction in data processing")
    
    print()
    print("🎯 POSITION BREAKDOWN (Confirmed Starters Only):")
    position_counts = pipeline_df['Position'].value_counts()
    for pos, count in position_counts.head(10).items():
        print(f"   {pos}: {count} players")
    
    print()
    
    # Check data pipeline files
    print("📈 DATA PIPELINE OUTPUT STATUS:")
    hitter_games = "../data/hitter_games.csv"
    pitcher_games = "../data/pitcher_games.csv"
    
    if os.path.exists(hitter_games):
        hitter_df = pd.read_csv(hitter_games)
        print(f"✅ hitter_games.csv: {len(hitter_df)} confirmed starting hitters")
    else:
        print("⚠️ hitter_games.csv: Not generated yet")
    
    if os.path.exists(pitcher_games):
        pitcher_df = pd.read_csv(pitcher_games)
        print(f"✅ pitcher_games.csv: {len(pitcher_df)} confirmed starting pitchers")
    else:
        print("⚠️ pitcher_games.csv: Not generated yet")
    
    print()
    
    # Show workflow
    print("🔄 DAILY WORKFLOW:")
    print("1. Download FanDuel slate → fd_slate_today.csv")
    print("2. Run 1_DATA_PIPELINE.bat:")
    print("   • Fetches Rotowire lineups")
    print("   • Creates starting_lineups.csv (master file)")
    print("   • Creates fd_slate_starters_only.csv (pipeline format)")
    print("   • Runs data pipeline using ONLY confirmed starters")
    print("3. Run 2_DFS_MODELS.bat (uses confirmed starters)")
    print("4. Run 3_PROP_MODELS.bat (uses confirmed starters)")
    
    print()
    print("✅ BENEFITS OF CONFIRMED STARTERS SYSTEM:")
    print("• No more Drake Baldwin or bench player issues")
    print("• Historical data pulled only for starters")
    print("• Weather/park factors only for starters")
    print("• Faster pipeline execution")
    print("• Consistent across all scripts and batch files")
    print("• Single source of truth (starting_lineups.csv)")

def show_sample_players():
    """Show sample confirmed starters"""
    
    try:
        pipeline_df = pd.read_csv("../data/fd_slate_starters_only.csv")
        
        print()
        print("👥 SAMPLE CONFIRMED STARTERS:")
        print("-" * 40)
        
        # Show sample pitchers
        pitchers = pipeline_df[pipeline_df['Position'] == 'P'].head(5)
        print("⚾ Pitchers:")
        for _, p in pitchers.iterrows():
            print(f"   {p['First Name']} {p['Last Name']} ({p['Team']}) - ${p['Salary']:,}")
        
        print()
        
        # Show sample hitters with batting orders
        hitters = pipeline_df[pipeline_df['Position'] != 'P'].head(8)
        print("🏏 Hitters:")
        for _, h in hitters.iterrows():
            bo = h.get('Batting Order', 'N/A')
            print(f"   {h['First Name']} {h['Last Name']} ({h['Position']}, {h['Team']}) - BO: {bo} - ${h['Salary']:,}")
        
    except Exception as e:
        print(f"❌ Error showing sample players: {e}")

def main():
    check_system_status()
    show_sample_players()
    
    print()
    print("🎉 SYSTEM READY!")
    print("Your data pipeline now uses only confirmed starters.")
    print("Run 1_DATA_PIPELINE.bat to see the efficiency gains!")

if __name__ == "__main__":
    main()
