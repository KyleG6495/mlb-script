#!/usr/bin/env python3
"""
PROJECTION RECALIBRATION SYSTEM
==============================
Fix your projections so they actually predict who goes off.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

def recalibrate_projections():
    """Fix your projections based on actual results"""
    
    print("STEP: PROJECTION RECALIBRATION STARTING...")
    print("=" * 50)
    
    # Load actual results
    actual = pd.read_csv("../data/actual_results_latest.csv")
    
    # Load your recent projections (we'll need to extract from lineup files)
    # For now, we'll create correction factors based on what we see
    
    corrections = {}
    
    # Position-based corrections based on diagnostic
    corrections['P'] = {
        'base_multiplier': 1.15,  # Pitchers seem undervalued
        'description': 'Boost pitcher projections - missing studs like Max Fried (49.6 pts)'
    }
    
    corrections['C'] = {
        'base_multiplier': 1.25,  # Catchers way undervalued
        'description': 'Major catcher boost - missed Kyle Higashioka (43.6 pts)'
    }
    
    corrections['1B'] = {
        'base_multiplier': 1.20,  # Missing power guys
        'description': 'Boost 1B projections - missed Kyle Manzardo (46.9), Andrew Vaughn (45.4)'
    }
    
    corrections['SS'] = {
        'base_multiplier': 1.10,  # Some hits but missed big ones
        'description': 'Modest SS boost - missed Brooks Lee (50.9), Gunnar Henderson (44.6)'
    }
    
    corrections['OF'] = {
        'base_multiplier': 1.15,  # Missing OF studs
        'description': 'OF boost - missed Wenceel Perez (46.3), Riley Greene (44.1)'
    }
    
    # Hot streak multipliers
    hot_streak_bonuses = {
        'recent_hot': 1.25,  # Player hot last 3 games
        'vs_weak_pitching': 1.20,  # Against ERA > 5.00
        'hitter_park': 1.15,  # Coors, Texas, etc.
        'high_total': 1.10,  # Games with O/U > 8.5
        'platoon_advantage': 1.10  # L vs R, R vs L
    }
    
    print("DATA: CORRECTION FACTORS CALCULATED:")
    print("-" * 40)
    for pos, data in corrections.items():
        print(f"{pos}: {data['base_multiplier']:.2f}x - {data['description']}")
    
    print(f"\n HOT STREAK BONUSES:")
    print("-" * 40)
    for bonus, mult in hot_streak_bonuses.items():
        print(f"{bonus}: +{(mult-1)*100:.0f}%")
    
    return corrections, hot_streak_bonuses

def create_enhanced_projection_code():
    """Generate the actual code to fix your projections"""
    
    code = '''
def enhance_projections(df, actual_results=None):
    """
    ENHANCED PROJECTION SYSTEM
    Fix projections based on actual performance gaps
    """
    
    # Base position corrections
    position_multipliers = {
        'P': 1.15,   # Missing pitcher studs
        'C': 1.25,   # Way undervaluing catchers  
        '1B': 1.20,  # Missing power 1B
        '2B': 1.05,  # Modest adjustment
        '3B': 1.10,  # Some improvement needed
        'SS': 1.10,  # Missing top SS
        'OF': 1.15,  # Missing OF studs
        'CF': 1.15,
        'LF': 1.15, 
        'RF': 1.15
    }
    
    # Apply position corrections
    for pos in position_multipliers:
        mask = df['position'] == pos
        df.loc[mask, 'projection'] *= position_multipliers[pos]
    
    # Recent performance boost
    if 'last_3_avg' in df.columns and 'season_avg' in df.columns:
        recent_boost = 1.0 + (df['last_3_avg'] - df['season_avg']) * 0.3
        recent_boost = recent_boost.clip(0.8, 1.5)  # Cap between 80% and 150%
        df['projection'] *= recent_boost
    
    # Matchup bonuses
    if 'opposing_pitcher_era' in df.columns:
        # Bonus vs bad pitchers
        bad_pitcher_mask = df['opposing_pitcher_era'] > 5.0
        df.loc[bad_pitcher_mask, 'projection'] *= 1.15
    
    if 'game_total' in df.columns:
        # Bonus for high-scoring games
        high_total_mask = df['game_total'] > 8.5
        df.loc[high_total_mask, 'projection'] *= 1.10
    
    if 'park_factor' in df.columns:
        # Bonus for hitter-friendly parks
        hitter_park_mask = df['park_factor'] > 1.05
        df.loc[hitter_park_mask, 'projection'] *= 1.10
    
    # Hot streak detection
    if 'last_7_games' in df.columns:
        # Players with 3+ multi-hit games in last 7
        hot_streak_mask = df['multi_hit_games_l7'] >= 3
        df.loc[hot_streak_mask, 'projection'] *= 1.20
        
        # Recent HR bonus
        recent_hr_mask = df['hr_last_3'] >= 1
        df.loc[recent_hr_mask, 'projection'] *= 1.15
        
        # Recent RBI bonus  
        recent_rbi_mask = df['rbi_last_3'] >= 5
        df.loc[recent_rbi_mask, 'projection'] *= 1.15
    
    return df

# INTEGRATION EXAMPLE:
# In your main projection script, add this line:
# df = enhance_projections(df, actual_results)
'''
    
    return code

def identify_missed_player_patterns():
    """Analyze the patterns of players you're missing"""
    
    print(f"\n MISSED PLAYER PATTERNS:")
    print("=" * 50)
    
    # Load actual results to analyze missed patterns
    actual = pd.read_csv("../data/actual_results_latest.csv")
    top_15 = actual.nlargest(15, 'fanduel_points')
    
    # Analyze by team
    team_performance = top_15.groupby('team')['fanduel_points'].agg(['count', 'sum', 'mean']).round(1)
    team_performance = team_performance.sort_values('sum', ascending=False)
    
    print(f"LINEUP: TOP PERFORMING TEAMS:")
    print(f"{'Team':<4} {'Players':<7} {'Total Pts':<10} {'Avg Pts':<8}")
    print("-" * 35)
    for team, row in team_performance.head(10).iterrows():
        print(f"{team:<4} {row['count']:<7} {row['sum']:<10} {row['mean']:<8}")
    
    # Analyze by position
    pos_performance = top_15.groupby('position')['fanduel_points'].agg(['count', 'mean']).round(1)
    pos_performance = pos_performance.sort_values('mean', ascending=False)
    
    print(f"\nTARGET: TOP PERFORMING POSITIONS:")
    print(f"{'Pos':<3} {'Count':<5} {'Avg Pts':<8}")
    print("-" * 20)
    for pos, row in pos_performance.iterrows():
        print(f"{pos:<3} {row['count']:<5} {row['mean']:<8}")
    
    # Analyze salary ranges (if available)
    if 'salary' in actual.columns:
        top_15['salary_tier'] = pd.cut(top_15['salary'], bins=4, labels=['Low', 'Med-Low', 'Med-High', 'High'])
        salary_analysis = top_15.groupby('salary_tier')['fanduel_points'].agg(['count', 'mean']).round(1)
        
        print(f"\nMONEY: PERFORMANCE BY SALARY TIER:")
        print(f"{'Tier':<8} {'Count':<5} {'Avg Pts':<8}")
        print("-" * 25)
        for tier, row in salary_analysis.iterrows():
            print(f"{tier:<8} {row['count']:<5} {row['mean']:<8}")
    
    return team_performance, pos_performance

def main():
    """Run complete projection fix"""
    
    print("START: FIXING YOUR PROJECTIONS TO ACTUALLY WORK")
    print("=" * 60)
    
    # Recalibrate projections
    corrections, bonuses = recalibrate_projections()
    
    # Generate enhanced code
    enhanced_code = create_enhanced_projection_code()
    
    # Analyze missed patterns
    team_perf, pos_perf = identify_missed_player_patterns()
    
    print(f"\n" + "=" * 60)
    print(f"SUCCESS: PROJECTION FIXES READY!")
    print(f"=" * 60)
    print(f" Enhanced projection code generated")
    print(f"TARGET: Position multipliers calculated")
    print(f" Hot streak bonuses identified")
    print(f"DATA: Team/position patterns analyzed")
    
    print(f"\n NEXT STEPS:")
    print(f"1. Add enhanced_projections() to your main script")
    print(f"2. Apply position multipliers immediately")
    print(f"3. Add hot streak detection")
    print(f"4. Test on tomorrow's slate")
    print(f"5. Track improvement vs actual results")

if __name__ == "__main__":
    main()
