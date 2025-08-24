#!/usr/bin/env python3
"""
 REAL SLATE TOURNAMENT LINEUP BUILDER
====================================
Building tournament lineups with ACTUAL players available today
(NOT fake Shane Bieber who isn't even playing!)

Based on real slate analysis:
- 23 probable pitchers available (no Shane Bieber!)
- Max Fried ($9,400, 35.1 FPPG) is the top pitcher
- Brewer Hicklen ($2,000, 21.4 FPPG) is the top value play
- 278 injured players must be avoided
"""

import pandas as pd
import numpy as np
from itertools import combinations
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_real_slate_data():
    """Load the actual FanDuel slate data"""
    logger.info(" LOADING REAL SLATE DATA")
    logger.info("="*50)
    
    slate_file = "../fd_current_slate/fd_slate_today.csv"
    slate = pd.read_csv(slate_file)
    
    logger.info(f"DATA: Total players in slate: {len(slate)}")
    
    # Filter out injured players
    healthy_slate = slate[slate['Injury Indicator'].isna()].copy()
    logger.info(f"SUCCESS: Healthy players: {len(healthy_slate)}")
    
    # Get probable pitchers only
    probable_pitchers = healthy_slate[
        (healthy_slate['Position'] == 'P') & 
        (healthy_slate['Probable Pitcher'] == 'Yes')
    ].copy()
    
    if len(probable_pitchers) == 0:
        # Fallback: use all healthy pitchers if no probable pitcher data
        probable_pitchers = healthy_slate[healthy_slate['Position'] == 'P'].copy()
        logger.warning("WARNING: No probable pitcher data found, using all healthy pitchers")
    
    logger.info(f"BASEBALL: Probable pitchers available: {len(probable_pitchers)}")
    
    # Get healthy hitters
    healthy_hitters = healthy_slate[healthy_slate['Position'] != 'P'].copy()
    logger.info(f" Healthy hitters available: {len(healthy_hitters)}")
    
    return slate, healthy_slate, probable_pitchers, healthy_hitters

def create_real_tournament_lineup():
    """Create a tournament lineup with REAL available players"""
    logger.info("LINEUP: CREATING REAL TOURNAMENT LINEUP")
    logger.info("="*50)
    
    slate, healthy_slate, probable_pitchers, healthy_hitters = load_real_slate_data()
    
    # Sort pitchers by FPPG
    top_pitchers = probable_pitchers.sort_values('FPPG', ascending=False).head(5)
    logger.info("TARGET: TOP 5 AVAILABLE PITCHERS:")
    for i, (_, pitcher) in enumerate(top_pitchers.iterrows(), 1):
        logger.info(f"   {i}. {pitcher['Nickname']} - ${pitcher['Salary']:,} | {pitcher['FPPG']:.1f} FPPG")
    
    # Sort hitters by FPPG for ceiling plays
    top_hitters = healthy_hitters.sort_values('FPPG', ascending=False).head(10)
    logger.info("\nSTART: TOP 10 AVAILABLE HITTERS:")
    for i, (_, hitter) in enumerate(top_hitters.iterrows(), 1):
        logger.info(f"   {i}. {hitter['Nickname']} - ${hitter['Salary']:,} | {hitter['FPPG']:.1f} FPPG")
    
    # Create tournament lineup with actual players
    lineup = {}
    total_salary = 0
    total_fppg = 0
    
    # Select top pitcher
    top_pitcher = top_pitchers.iloc[0]
    lineup['P'] = {
        'name': top_pitcher['Nickname'],
        'team': top_pitcher['Team'],
        'salary': top_pitcher['Salary'],
        'fppg': top_pitcher['FPPG'],
        'position': 'P'
    }
    total_salary += top_pitcher['Salary']
    total_fppg += top_pitcher['FPPG']
    
    logger.info(f"\nTARGET: SELECTED PITCHER: {top_pitcher['Nickname']} - ${top_pitcher['Salary']:,} | {top_pitcher['FPPG']:.1f} FPPG")
    
    # Remaining salary for hitters
    remaining_salary = 35000 - total_salary
    logger.info(f"MONEY: Remaining salary for 8 hitters: ${remaining_salary:,}")
    
    # Find best value hitters for remaining positions
    # Sort by value (FPPG per $1K)
    healthy_hitters['value'] = healthy_hitters['FPPG'] / (healthy_hitters['Salary'] / 1000)
    value_hitters = healthy_hitters.sort_values('value', ascending=False).head(15)
    
    logger.info("\n TOP VALUE HITTERS:")
    for i, (_, hitter) in enumerate(value_hitters.iterrows(), 1):
        if i <= 8:  # Show top 8
            logger.info(f"   {i}. {hitter['Nickname']} - ${hitter['Salary']:,} | {hitter['FPPG']:.1f} FPPG | {hitter['value']:.1f} val")
    
    # Select 8 best value hitters that fit salary
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    selected_hitters = []
    used_salary = total_salary
    
    for i, (_, hitter) in enumerate(value_hitters.iterrows()):
        if len(selected_hitters) >= 8:
            break
        if used_salary + hitter['Salary'] <= 35000:
            selected_hitters.append(hitter)
            used_salary += hitter['Salary']
    
    # Build final lineup
    for i, hitter in enumerate(selected_hitters[:8]):
        pos = positions[i]
        lineup[pos] = {
            'name': hitter['Nickname'],
            'team': hitter['Team'],
            'salary': hitter['Salary'],
            'fppg': hitter['FPPG'],
            'position': pos
        }
        total_fppg += hitter['FPPG']
    
    lineup['TOTAL_SALARY'] = used_salary
    lineup['TOTAL_FPPG'] = total_fppg
    lineup['SALARY_REMAINING'] = 35000 - used_salary
    
    return lineup

def display_real_lineup(lineup):
    """Display the real tournament lineup"""
    logger.info("LINEUP: REAL TOURNAMENT LINEUP (ACTUAL PLAYERS)")
    logger.info("="*60)
    
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    
    for pos in positions:
        if pos in lineup:
            player = lineup[pos]
            logger.info(f"{pos:3} | {player['name']:20} | {player['team']:3} | ${player['salary']:4,} | {player['fppg']:5.1f} FPPG")
    
    logger.info("-" * 60)
    logger.info(f"MONEY: Total Salary: ${lineup['TOTAL_SALARY']:,} / $35,000")
    logger.info(f"DATA: Total Projection: {lineup['TOTAL_FPPG']:.1f} FPPG")
    logger.info(f" Salary Remaining: ${lineup['SALARY_REMAINING']:,}")
    
    # Tournament viability assessment
    if lineup['TOTAL_FPPG'] >= 153:
        rating = "LINEUP: TOURNAMENT COMPETITIVE"
    elif lineup['TOTAL_FPPG'] >= 140:
        rating = "SUCCESS: TOURNAMENT VIABLE"
    elif lineup['TOTAL_FPPG'] >= 120:
        rating = "WARNING: NEEDS IMPROVEMENT"
    else:
        rating = "ERROR: NOT COMPETITIVE"
    
    logger.info(f"TARGET: Tournament Rating: {rating}")
    
    return lineup

def save_real_lineup(lineup):
    """Save the real lineup to file"""
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/REAL_TOURNAMENT_LINEUP_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(lineup, f, indent=2)
    
    logger.info(f" Real lineup saved: {filename}")
    
    # Also create CSV format for FanDuel submission
    csv_filename = f"../data/REAL_TOURNAMENT_LINEUP_{timestamp}.csv"
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    
    csv_data = []
    for pos in positions:
        if pos in lineup:
            player = lineup[pos]
            csv_data.append({
                'Position': pos,
                'Name': player['name'],
                'Team': player['team'],
                'Salary': player['salary'],
                'FPPG': player['fppg']
            })
    
    df = pd.DataFrame(csv_data)
    df.to_csv(csv_filename, index=False)
    logger.info(f" CSV format saved: {csv_filename}")
    
    return filename, csv_filename

def main():
    """Main execution"""
    logger.info(" REAL SLATE TOURNAMENT LINEUP BUILDER")
    logger.info("Building with ACTUAL players available today")
    logger.info("="*70)
    
    try:
        # Create real lineup
        lineup = create_real_tournament_lineup()
        
        # Display results
        display_real_lineup(lineup)
        
        # Save lineup
        json_file, csv_file = save_real_lineup(lineup)
        
        logger.info("="*70)
        logger.info("COMPLETE: REAL TOURNAMENT LINEUP COMPLETE!")
        logger.info(f"DATA: Projection: {lineup['TOTAL_FPPG']:.1f} FPPG (vs 31.7 disaster)")
        logger.info(f" Improvement: {((lineup['TOTAL_FPPG'] - 31.7) / 31.7 * 100):.0f}% vs disaster")
        logger.info(f"TARGET: Tournament Ready: {lineup['TOTAL_FPPG'] >= 153}")
        logger.info(" Files saved for FanDuel submission!")
        
    except Exception as e:
        logger.error(f"ERROR: Error creating real lineup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
