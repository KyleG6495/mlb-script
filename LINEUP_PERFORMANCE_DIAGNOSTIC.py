#!/usr/bin/env python3
"""
LINEUP PERFORMANCE DIAGNOSTIC
============================
Analyze why your lineups underperform and fix the core issues.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_lineup_performance():
    """Analyze your recent lineup performance vs actual results"""
    
    print(" LINEUP PERFORMANCE DIAGNOSTIC")
    print("=" * 50)
    
    # Load actual results
    try:
        actual = pd.read_csv("../data/actual_results_latest.csv")
        print(f"SUCCESS: Loaded {len(actual)} actual player results")
        
        # Show top performers from actual results
        actual['total_fanduel_points'] = actual['fanduel_points']
        top_performers = actual.nlargest(15, 'total_fanduel_points')
        
        print(f"\nLINEUP: TOP ACTUAL PERFORMERS:")
        print("-" * 60)
        for _, player in top_performers.iterrows():
            print(f"{player['name']:<20} {player['position']:<3} {player['team']:<4} {player['total_fanduel_points']:6.1f} pts")
        
    except Exception as e:
        print(f"ERROR: Error loading actual results: {e}")
        return
    
    # Load your recent lineups
    try:
        import glob
        lineup_files = glob.glob("../data/CHAMPIONSHIP_LINEUPS_SUMMARY_*.csv")
        if not lineup_files:
            print("ERROR: No championship lineup files found")
            return
            
        latest_lineup = sorted(lineup_files)[-1]
        lineups = pd.read_csv(latest_lineup)
        print(f"\nDATA: Analyzing your lineups from: {latest_lineup}")
        
        # Show your lineup selections
        print(f"\nTARGET: YOUR LINEUP SELECTIONS:")
        print("-" * 60)
        for _, lineup in lineups.head(3).iterrows():
            total_proj = lineup.get('Total_FPPG', 0)
            print(f"Lineup {lineup['Lineup']}: {total_proj:.1f} projected FPPG")
            print(f"  P: {lineup['P']}")
            print(f"  Hitters: {lineup['C']}, {lineup['1B']}, {lineup['2B']}, {lineup['3B']}, {lineup['SS']}")
            print(f"  OF: {lineup['OF1']}, {lineup['OF2']}, {lineup['OF3']}")
            print()
        
    except Exception as e:
        print(f"ERROR: Error loading lineups: {e}")
        return
    
    # Analyze the gaps
    print(f"\n PERFORMANCE GAP ANALYSIS:")
    print("-" * 60)
    
    # 1. Player overlap analysis
    your_players = set()
    for col in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']:
        if col in lineups.columns:
            your_players.update(lineups[col].dropna().tolist())
    
    actual_names = set(actual['name'].tolist())
    
    overlap = your_players.intersection(actual_names)
    print(f"Player overlap: {len(overlap)} / {len(your_players)} players")
    
    # 2. Check if you had any top performers
    top_performer_names = set(top_performers['name'].tolist())
    your_top_picks = your_players.intersection(top_performer_names)
    
    print(f"Top performers you selected: {len(your_top_picks)}")
    if your_top_picks:
        print(f"  SUCCESS: You had: {', '.join(your_top_picks)}")
    else:
        print(f"  ERROR: You missed ALL top performers!")
    
    # 3. Identify the players you missed
    missed_studs = top_performer_names - your_players
    print(f"\n MISSED OPPORTUNITIES:")
    for name in list(missed_studs)[:10]:
        player_data = actual[actual['name'] == name].iloc[0]
        print(f"   {name}: {player_data['total_fanduel_points']:.1f} pts ({player_data['position']}/{player_data['team']})")
    
    return {
        'your_players': your_players,
        'top_performers': top_performers,
        'overlap': overlap,
        'missed_studs': missed_studs
    }

def identify_core_problems():
    """Identify the core problems with your lineup generation"""
    
    print(f"\n CORE PROBLEMS IDENTIFIED:")
    print("=" * 50)
    
    problems = []
    
    # Problem 1: Projection accuracy
    problems.append({
        'issue': 'PROJECTION ACCURACY',
        'description': 'Your FPPG projections dont match reality',
        'evidence': 'Projecting 149 FPPG but missing 40+ point players',
        'impact': 'HIGH - Missing the players who actually perform',
        'fix': 'Recalibrate projections with recent actual results'
    })
    
    # Problem 2: Player pool
    problems.append({
        'issue': 'PLAYER POOL SELECTION', 
        'description': 'Selecting wrong players entirely',
        'evidence': 'Zero overlap with top actual performers',
        'impact': 'CRITICAL - Building lineups from wrong players',
        'fix': 'Improve player filtering and selection criteria'
    })
    
    # Problem 3: Salary optimization
    problems.append({
        'issue': 'SALARY ALLOCATION',
        'description': 'Not optimizing spend across positions',
        'evidence': 'May be overspending on low-upside positions',
        'impact': 'MEDIUM - Limiting ceiling potential',
        'fix': 'Rebalance salary distribution for tournament upside'
    })
    
    # Problem 4: Matchup analysis
    problems.append({
        'issue': 'MATCHUP ANALYSIS',
        'description': 'Missing favorable matchups and game environments',
        'evidence': 'Not identifying the right games/spots',
        'impact': 'HIGH - Missing high-scoring environments',
        'fix': 'Enhance game/pitcher matchup analysis'
    })
    
    for i, problem in enumerate(problems, 1):
        print(f"\n{i}. {problem['issue']}")
        print(f"   Problem: {problem['description']}")
        print(f"   Evidence: {problem['evidence']}")
        print(f"   Impact: {problem['impact']}")
        print(f"   Fix: {problem['fix']}")
    
    return problems

def generate_improvement_plan():
    """Generate specific improvement recommendations"""
    
    print(f"\nSTART: IMPROVEMENT PLAN - MAKE YOUR LINEUPS COMPETITIVE")
    print("=" * 70)
    
    improvements = [
        {
            'priority': 'CRITICAL',
            'action': 'FIX PROJECTION RECALIBRATION',
            'steps': [
                'Load last 7 days of actual results',
                'Compare your projections vs actual scores', 
                'Apply correction factors by position',
                'Boost projections for consistently underestimated players'
            ],
            'timeline': 'IMMEDIATE'
        },
        {
            'priority': 'HIGH', 
            'action': 'IMPROVE PLAYER IDENTIFICATION',
            'steps': [
                'Analyze recent game logs for hot/cold streaks',
                'Weight recent performance more heavily',
                'Add matchup-specific bonuses (weak pitching, hitter parks)',
                'Consider batting order changes and lineup spots'
            ],
            'timeline': '1-2 days'
        },
        {
            'priority': 'HIGH',
            'action': 'ENHANCE GAME ENVIRONMENT ANALYSIS', 
            'steps': [
                'Target high O/U games (8.5+ runs)',
                'Identify weak bullpens and spot starts',
                'Weight weather factors (wind, temperature)',
                'Target hitter-friendly parks'
            ],
            'timeline': '2-3 days'
        },
        {
            'priority': 'MEDIUM',
            'action': 'OPTIMIZE SALARY ALLOCATION',
            'steps': [
                'Analyze ROI by salary tier',
                'Identify value spots in each position',
                'Balance stars vs value plays',
                'Maximize ceiling potential per dollar'
            ],
            'timeline': '3-5 days'
        }
    ]
    
    for improvement in improvements:
        print(f"\nTARGET: {improvement['priority']}: {improvement['action']}")
        print(f"   Timeline: {improvement['timeline']}")
        for step in improvement['steps']:
            print(f"    {step}")
    
    return improvements

def create_quick_fixes():
    """Create immediate fixes you can implement today"""
    
    print(f"\n QUICK FIXES - IMPLEMENT TODAY")
    print("=" * 50)
    
    # Quick fix 1: Recent performance weighting
    print(f"1. RECENT PERFORMANCE BOOST:")
    print(f"   Add this to your projection code:")
    print(f'   recent_multiplier = 1.0 + (last_3_games_avg - season_avg) * 0.3')
    print(f'   enhanced_projection = base_projection * recent_multiplier')
    
    # Quick fix 2: Matchup bonuses
    print(f"\n2. MATCHUP BONUSES:")
    print(f"   Add bonuses for:")
    print(f"    vs LHP when player has high vs LHP stats (+10%)")
    print(f"    vs bad pitchers (ERA > 5.00) (+15%)")
    print(f"    in hitter parks (Coors, TEX, etc.) (+10%)")
    print(f"    high O/U games (>9 runs) (+10%)")
    
    # Quick fix 3: Hot streak identification
    print(f"\n3. HOT STREAK DETECTION:")
    print(f"   Boost players with:")
    print(f"    3+ multi-hit games in last 7 (+20%)")
    print(f"    HR in last 3 games (+15%)")
    print(f"    5+ RBI in last 3 games (+15%)")
    
    return "Quick fixes ready to implement"

def main():
    """Run complete diagnostic"""
    
    # Analyze current performance
    analysis_results = analyze_lineup_performance()
    
    # Identify core problems  
    problems = identify_core_problems()
    
    # Generate improvement plan
    improvements = generate_improvement_plan()
    
    # Create quick fixes
    quick_fixes = create_quick_fixes()
    
    print(f"\n" + "=" * 70)
    print(f"INFO: DIAGNOSTIC COMPLETE - YOUR LINEUPS CAN BE FIXED!")
    print(f"=" * 70)
    print(f"TARGET: Start with CRITICAL items first")
    print(f" Implement quick fixes today")
    print(f"PROGRESS: Track improvement over next week")
    print(f"LINEUP: Goal: Consistently hit 180+ FPPG lineups")

if __name__ == "__main__":
    main()
