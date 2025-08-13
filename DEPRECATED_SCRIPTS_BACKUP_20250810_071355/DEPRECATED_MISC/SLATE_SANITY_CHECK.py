#!/usr/bin/env python3
"""
SLATE SANITY CHECK
=================
Identify the actual viable players after filtering out disasters.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_viable_players():
    """Find players who can actually play and score points"""
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    slate_file = slate_dir / "fd_slate_today.csv"
    
    print("🔍 SLATE SANITY CHECK")
    print("="*50)
    
    df = pd.read_csv(slate_file)
    print(f"📊 Total players in slate: {len(df)}")
    
    # Filter out obvious disasters
    print(f"\n🏥 INJURY ANALYSIS:")
    injured = df[df['Injury Indicator'].notna()]
    print(f"  💥 Injured players: {len(injured)}")
    if len(injured) > 0:
        print(f"  💰 Total salary of injured: ${injured['Salary'].sum():,}")
        top_injured = injured.nlargest(10, 'Salary')[['First Name', 'Last Name', 'Position', 'Salary', 'Injury Indicator', 'Injury Details']]
        print(f"  🚨 Top expensive injured players:")
        for _, player in top_injured.iterrows():
            name = f"{player['First Name']} {player['Last Name']}"
            print(f"    💥 {name:20} ({player['Position']:2}) ${player['Salary']:5,} - {player['Injury Indicator']} ({player['Injury Details']})")
    
    # Filter to healthy players
    healthy = df[df['Injury Indicator'].isna()]
    print(f"\n✅ HEALTHY PLAYERS:")
    print(f"  🏃 Healthy players: {len(healthy)}")
    print(f"  💰 Available salary pool: ${healthy['Salary'].sum():,}")
    
    # Pitcher analysis
    pitchers = healthy[healthy['Position'] == 'P']
    probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
    print(f"\n⚾ PITCHER ANALYSIS:")
    print(f"  🎯 Total healthy pitchers: {len(pitchers)}")
    print(f"  ✅ Probable starters: {len(probable_pitchers)}")
    print(f"  ❌ Non-probable pitchers: {len(pitchers) - len(probable_pitchers)}")
    
    if len(probable_pitchers) > 0:
        print(f"  💰 Probable pitcher salary range: ${probable_pitchers['Salary'].min():,} - ${probable_pitchers['Salary'].max():,}")
        print(f"  📈 Probable pitcher FPPG range: {probable_pitchers['FPPG'].min():.1f} - {probable_pitchers['FPPG'].max():.1f}")
        
        print(f"\n🎯 TOP 10 PROBABLE PITCHERS:")
        top_probable = probable_pitchers.nlargest(10, 'FPPG')[['First Name', 'Last Name', 'Salary', 'FPPG', 'Team', 'Opponent']]
        for _, p in top_probable.iterrows():
            name = f"{p['First Name']} {p['Last Name']}"
            matchup = f"{p['Team']} vs {p['Opponent']}"
            print(f"    ⭐ {name:20} ${p['Salary']:5,} | {p['FPPG']:5.1f} FPPG | {matchup}")
    
    # Hitter analysis
    hitters = healthy[healthy['Position'] != 'P']
    print(f"\n🏏 HITTER ANALYSIS:")
    print(f"  👥 Total healthy hitters: {len(hitters)}")
    print(f"  💰 Hitter salary range: ${hitters['Salary'].min():,} - ${hitters['Salary'].max():,}")
    print(f"  📈 Hitter FPPG range: {hitters['FPPG'].min():.1f} - {hitters['FPPG'].max():.1f}")
    
    # Check for batting order availability
    hitters_with_order = hitters[hitters['Batting Order'].notna()]
    print(f"  📋 Hitters with batting order: {len(hitters_with_order)}")
    print(f"  ❓ Hitters without batting order: {len(hitters) - len(hitters_with_order)}")
    
    print(f"\n🎯 TOP 15 VALUE HITTERS:")
    hitters['value'] = hitters['FPPG'] / (hitters['Salary'] / 1000)
    top_value = hitters.nlargest(15, 'value')[['First Name', 'Last Name', 'Roster Position', 'Salary', 'FPPG', 'value', 'Team', 'Opponent']]
    for _, h in top_value.iterrows():
        name = f"{h['First Name']} {h['Last Name']}"
        pos = h['Roster Position']
        matchup = f"{h['Team']} vs {h['Opponent']}"
        print(f"    💎 {name:20} ({pos:4}) ${h['Salary']:4,} | {h['FPPG']:5.1f} FPPG | {h['value']:4.1f} val | {matchup}")
    
    print(f"\n🎯 TOP 15 CEILING HITTERS:")
    top_ceiling = hitters.nlargest(15, 'FPPG')[['First Name', 'Last Name', 'Roster Position', 'Salary', 'FPPG', 'value', 'Team', 'Opponent']]
    for _, h in top_ceiling.iterrows():
        name = f"{h['First Name']} {h['Last Name']}"
        pos = h['Roster Position']
        matchup = f"{h['Team']} vs {h['Opponent']}"
        print(f"    🚀 {name:20} ({pos:4}) ${h['Salary']:4,} | {h['FPPG']:5.1f} FPPG | {h['value']:4.1f} val | {matchup}")
    
    # Position analysis
    print(f"\n📊 POSITION AVAILABILITY:")
    for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']:
        if pos == 'P':
            pos_players = probable_pitchers
        else:
            pos_players = hitters[hitters['Roster Position'].str.contains(pos, na=False)]
        
        if len(pos_players) > 0:
            avg_salary = pos_players['Salary'].mean()
            avg_fppg = pos_players['FPPG'].mean()
            print(f"  {pos:2}: {len(pos_players):3} players | Avg: ${avg_salary:5,.0f} | {avg_fppg:5.1f} FPPG")
        else:
            print(f"  {pos:2}: {len(pos_players):3} players | ❌ PROBLEM!")
    
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"  1. ✅ Use ONLY healthy players (remove {len(injured)} injured)")
    print(f"  2. ⚾ Use ONLY probable pitchers ({len(probable_pitchers)} available)")
    print(f"  3. 🎯 Focus on value plays (4.0+ value score)")
    print(f"  4. 🚀 Mix in ceiling plays (15+ FPPG)")
    print(f"  5. 📋 Wait for batting orders if not available")
    
    return {
        'total_players': len(df),
        'injured_players': len(injured),
        'healthy_players': len(healthy),
        'probable_pitchers': len(probable_pitchers),
        'healthy_hitters': len(hitters)
    }

if __name__ == "__main__":
    stats = analyze_viable_players()
    print(f"\n📊 SUMMARY: {stats['healthy_players']} viable players out of {stats['total_players']} total")
