#!/usr/bin/env python3
"""
LINEUP: PROPER TOURNAMENT LINEUP BUILDER
==================================
Building competitive lineups with the ACTUAL star players available today
Using all 12 games and top healthy players
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_todays_slate():
    """Analyze what's actually available today"""
    logger.info(" ANALYZING TODAY'S SLATE")
    logger.info("="*50)
    
    slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # Get games
    games = slate['Game'].unique()
    logger.info(f" Games today: {len(games)}")
    for game in games:
        logger.info(f"   {game}")
    
    # Filter healthy players
    healthy = slate[slate['Injury Indicator'].isna()].copy()
    logger.info(f"\nSUCCESS: Healthy players: {len(healthy)}/{len(slate)}")
    
    # Top pitchers (all healthy, not just probable)
    healthy_pitchers = healthy[healthy['Position'] == 'P'].sort_values('FPPG', ascending=False)
    logger.info(f"\n TOP 10 HEALTHY PITCHERS:")
    for i, (_, p) in enumerate(healthy_pitchers.head(10).iterrows(), 1):
        logger.info(f"   {i:2d}. {p['Nickname']:20} ${p['Salary']:5,} | {p['FPPG']:5.1f} FPPG | {p['Game']}")
    
    # Top hitters by salary (stars)
    healthy_hitters = healthy[healthy['Position'] != 'P']
    top_hitters = healthy_hitters[healthy_hitters['Salary'] >= 3500].sort_values('FPPG', ascending=False)
    logger.info(f"\n TOP 10 STAR HITTERS ($3500+):")
    for i, (_, h) in enumerate(top_hitters.head(10).iterrows(), 1):
        logger.info(f"   {i:2d}. {h['Nickname']:20} ${h['Salary']:5,} | {h['FPPG']:5.1f} FPPG | {h['Game']}")
    
    # Value plays
    value_hitters = healthy_hitters.copy()
    value_hitters['value'] = value_hitters['FPPG'] / (value_hitters['Salary'] / 1000)
    top_value = value_hitters[value_hitters['Salary'] <= 3000].sort_values('value', ascending=False)
    logger.info(f"\n TOP 10 VALUE PLAYS ($3000 or less):")
    for i, (_, v) in enumerate(top_value.head(10).iterrows(), 1):
        logger.info(f"   {i:2d}. {v['Nickname']:20} ${v['Salary']:5,} | {v['FPPG']:5.1f} FPPG | {v['value']:4.1f} val | {v['Game']}")
    
    return slate, healthy, healthy_pitchers, top_hitters, top_value

def build_competitive_lineup(healthy, healthy_pitchers, top_hitters, top_value):
    """Build a truly competitive tournament lineup"""
    logger.info("\nLINEUP: BUILDING COMPETITIVE TOURNAMENT LINEUP")
    logger.info("="*60)
    
    lineup = {}
    total_salary = 0
    total_fppg = 0
    
    # Select elite pitcher (top 3)
    top_pitcher = healthy_pitchers.iloc[0]  # Best available
    lineup['P'] = {
        'name': top_pitcher['Nickname'],
        'team': top_pitcher['Team'],
        'game': top_pitcher['Game'],
        'salary': int(top_pitcher['Salary']),
        'fppg': float(top_pitcher['FPPG']),
        'position': 'P'
    }
    total_salary += top_pitcher['Salary']
    total_fppg += top_pitcher['FPPG']
    
    logger.info(f"TARGET: Selected Ace: {top_pitcher['Nickname']} - ${top_pitcher['Salary']:,} | {top_pitcher['FPPG']:.1f} FPPG")
    
    # Remaining salary for 8 hitters
    remaining = 35000 - total_salary
    logger.info(f"MONEY: Remaining for hitters: ${remaining:,}")
    
    # Strategy: Mix stars and value
    # Take 3-4 stars, 4-5 value plays
    
    selected_hitters = []
    used_teams = {top_pitcher['Team']}  # Track for stacking potential
    
    # Select 3 star hitters
    for i, (_, hitter) in enumerate(top_hitters.iterrows()):
        if len(selected_hitters) >= 3:
            break
        if total_salary + hitter['Salary'] <= 33000:  # Leave room for value plays
            selected_hitters.append(hitter)
            total_salary += hitter['Salary']
            total_fppg += hitter['FPPG']
            used_teams.add(hitter['Team'])
            logger.info(f" Selected Star {len(selected_hitters)}: {hitter['Nickname']} - ${hitter['Salary']:,} | {hitter['FPPG']:.1f} FPPG")
    
    # Fill remaining spots with value plays
    remaining_spots = 8 - len(selected_hitters)
    remaining_salary = 35000 - total_salary
    avg_remaining = remaining_salary / remaining_spots
    
    logger.info(f" Need {remaining_spots} value plays, avg ${avg_remaining:,.0f} each")
    
    for _, value_hitter in top_value.iterrows():
        if len(selected_hitters) >= 8:
            break
        if total_salary + value_hitter['Salary'] <= 35000:
            if value_hitter['Salary'] <= avg_remaining * 1.2:  # Stay close to budget
                selected_hitters.append(value_hitter)
                total_salary += value_hitter['Salary']
                total_fppg += value_hitter['FPPG']
                logger.info(f" Selected Value {len(selected_hitters)}: {value_hitter['Nickname']} - ${value_hitter['Salary']:,} | {value_hitter['FPPG']:.1f} FPPG")
    
    # Add hitters to lineup
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    for i, hitter in enumerate(selected_hitters[:8]):
        pos = positions[i]
        lineup[pos] = {
            'name': hitter['Nickname'],
            'team': hitter['Team'],
            'game': hitter['Game'],
            'salary': int(hitter['Salary']),
            'fppg': float(hitter['FPPG']),
            'position': pos
        }
    
    lineup['TOTAL_SALARY'] = int(total_salary)
    lineup['TOTAL_FPPG'] = float(total_fppg)
    lineup['SALARY_REMAINING'] = int(35000 - total_salary)
    
    return lineup

def display_competitive_lineup(lineup):
    """Display the competitive lineup"""
    logger.info("\nLINEUP: COMPETITIVE TOURNAMENT LINEUP")
    logger.info("="*70)
    
    positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
    
    for pos in positions:
        if pos in lineup:
            player = lineup[pos]
            logger.info(f"{pos:3} | {player['name']:20} | {player['team']:3} | {player['game']:8} | ${player['salary']:5,} | {player['fppg']:5.1f} FPPG")
    
    logger.info("-" * 70)
    logger.info(f"MONEY: Total Salary: ${lineup['TOTAL_SALARY']:,} / $35,000")
    logger.info(f"DATA: Total Projection: {lineup['TOTAL_FPPG']:.1f} FPPG")
    logger.info(f" Salary Remaining: ${lineup['SALARY_REMAINING']:,}")
    
    # Tournament viability
    if lineup['TOTAL_FPPG'] >= 180:
        rating = " ELITE TOURNAMENT LINEUP"
    elif lineup['TOTAL_FPPG'] >= 153:
        rating = "LINEUP: TOURNAMENT COMPETITIVE"
    elif lineup['TOTAL_FPPG'] >= 140:
        rating = "SUCCESS: TOURNAMENT VIABLE"
    else:
        rating = "WARNING: NEEDS IMPROVEMENT"
    
    logger.info(f"\nTARGET: Tournament Rating: {rating}")
    logger.info(f"START: vs Disaster (31.7): +{((lineup['TOTAL_FPPG'] - 31.7) / 31.7 * 100):.0f}%")
    logger.info(f"TARGET: vs Winner Threshold (153): {'+' if lineup['TOTAL_FPPG'] >= 153 else ''}{lineup['TOTAL_FPPG'] - 153:.1f} FPPG")
    
    return lineup

def main():
    """Main execution"""
    logger.info("LINEUP: PROPER TOURNAMENT LINEUP BUILDER")
    logger.info("Using ALL available star players from 12 games today")
    logger.info("="*70)
    
    try:
        # Analyze slate
        slate, healthy, healthy_pitchers, top_hitters, top_value = analyze_todays_slate()
        
        # Build competitive lineup
        lineup = build_competitive_lineup(healthy, healthy_pitchers, top_hitters, top_value)
        
        # Display results
        display_competitive_lineup(lineup)
        
        logger.info("\n" + "="*70)
        logger.info("COMPLETE: COMPETITIVE LINEUP COMPLETE!")
        logger.info(f"DATA: Using stars from {len(set([p['game'] for p in lineup.values() if isinstance(p, dict) and 'game' in p]))} different games")
        logger.info("START: This should be MUCH more competitive than 31.7 FPPG!")
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
