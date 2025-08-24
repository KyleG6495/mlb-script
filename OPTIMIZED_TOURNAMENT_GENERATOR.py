#!/usr/bin/env python3
"""
START: OPTIMIZED TOURNAMENT LINEUP GENERATOR
======================================
Multiple lineup combinations to get over 153 FPPG threshold
Testing different pitcher/hitter combinations from today's slate
"""

import pandas as pd
import numpy as np
import logging
from itertools import combinations

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_slate_data():
    """Load and prepare slate data"""
    slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    healthy = slate[slate['Injury Indicator'].isna()].copy()
    
    # Top pitchers
    pitchers = healthy[healthy['Position'] == 'P'].sort_values('FPPG', ascending=False).head(8)
    
    # Top hitters by different criteria
    hitters = healthy[healthy['Position'] != 'P']
    
    # Star hitters ($3500+)
    stars = hitters[hitters['Salary'] >= 3500].sort_values('FPPG', ascending=False).head(15)
    
    # Mid-tier hitters ($2500-$3499)
    mid_tier = hitters[(hitters['Salary'] >= 2500) & (hitters['Salary'] < 3500)].sort_values('FPPG', ascending=False).head(15)
    
    # Value plays ($2000-$2499)
    hitters['value'] = hitters['FPPG'] / (hitters['Salary'] / 1000)
    value = hitters[hitters['Salary'] <= 2499].sort_values('value', ascending=False).head(15)
    
    return pitchers, stars, mid_tier, value

def build_lineup_combination(pitcher, star_count, total_budget=35000):
    """Build a lineup with specified pitcher and number of stars"""
    pitchers, stars, mid_tier, value = load_slate_data()
    
    total_salary = int(pitcher['Salary'])
    total_fppg = float(pitcher['FPPG'])
    
    selected_hitters = []
    
    # Select stars first
    stars_selected = 0
    for _, star in stars.iterrows():
        if stars_selected >= star_count:
            break
        if total_salary + star['Salary'] <= total_budget - (8 - stars_selected - 1) * 2000:  # Leave room for others
            selected_hitters.append(star.to_dict())
            total_salary += int(star['Salary'])
            total_fppg += float(star['FPPG'])
            stars_selected += 1
            
        if len(selected_hitters) >= 4:  # Max 4 stars to leave room for value
            break
    
    # Fill remaining spots with best available value plays
    for _, player in value.iterrows():
        if len(selected_hitters) >= 8:
            break
        if total_salary + player['Salary'] <= total_budget:
            # Check if already selected
            if not any(p['Id'] == player['Id'] for p in selected_hitters):
                selected_hitters.append(player.to_dict())
                total_salary += int(player['Salary'])
                total_fppg += float(player['FPPG'])
    
    # If still need players, add from mid-tier
    if len(selected_hitters) < 8:
        for _, player in mid_tier.iterrows():
            if len(selected_hitters) >= 8:
                break
            if total_salary + player['Salary'] <= total_budget:
                # Check if already selected
                if not any(p['Id'] == player['Id'] for p in selected_hitters):
                    selected_hitters.append(player.to_dict())
                    total_salary += int(player['Salary'])
                    total_fppg += float(player['FPPG'])
    
    return {
        'pitcher': pitcher.to_dict(),
        'hitters': selected_hitters,
        'total_salary': int(total_salary),
        'total_fppg': float(total_fppg),
        'remaining': int(total_budget - total_salary),
        'star_count': stars_selected
    }

def find_optimal_lineups():
    """Find multiple optimal lineup combinations"""
    logger.info("START: FINDING OPTIMAL TOURNAMENT LINEUPS")
    logger.info("="*60)
    
    pitchers, stars, mid_tier, value = load_slate_data()
    
    # Test different combinations
    combinations_to_test = [
        # (pitcher_index, star_count, description)
        (0, 4, "Max stars with ace pitcher"),
        (0, 3, "Balanced stars with ace"),
        (1, 4, "Max stars with #2 pitcher"),
        (1, 3, "Balanced with #2 pitcher"),
        (2, 5, "Max stars with cheaper ace"),
        (3, 4, "Mid-price pitcher + stars"),
        (4, 3, "Value pitcher + balanced stars"),
    ]
    
    best_lineups = []
    
    for pitcher_idx, star_count, description in combinations_to_test:
        if pitcher_idx < len(pitchers):
            pitcher = pitchers.iloc[pitcher_idx]
            lineup = build_lineup_combination(pitcher, star_count)
            
            if len(lineup['hitters']) == 8:  # Valid lineup
                lineup['description'] = description
                best_lineups.append(lineup)
                
                logger.info(f"\nTARGET: {description}:")
                logger.info(f"   P: {pitcher['Nickname']} - ${pitcher['Salary']:,} | {pitcher['FPPG']:.1f} FPPG")
                logger.info(f"   Stars: {lineup['star_count']}, Total: ${lineup['total_salary']:,}")
                logger.info(f"   Projection: {lineup['total_fppg']:.1f} FPPG")
                
                if lineup['total_fppg'] >= 153:
                    logger.info(f"   LINEUP: TOURNAMENT COMPETITIVE! (+{lineup['total_fppg'] - 153:.1f})")
                else:
                    logger.info(f"   WARNING:  Need +{153 - lineup['total_fppg']:.1f} FPPG")
    
    # Sort by projection
    best_lineups.sort(key=lambda x: x['total_fppg'], reverse=True)
    
    return best_lineups

def display_top_lineups(best_lineups, top_n=3):
    """Display the top N lineups in detail"""
    logger.info(f"\nLINEUP: TOP {top_n} OPTIMIZED LINEUPS")
    logger.info("="*80)
    
    for i, lineup in enumerate(best_lineups[:top_n], 1):
        logger.info(f"\n LINEUP #{i}: {lineup['description']}")
        logger.info(f"DATA: Projection: {lineup['total_fppg']:.1f} FPPG | Salary: ${lineup['total_salary']:,}")
        logger.info("-" * 60)
        
        # Display pitcher
        p = lineup['pitcher']
        logger.info(f"P   | {p['Nickname']:20} | {p['Team']:3} | {p['Game']:8} | ${p['Salary']:5,} | {p['FPPG']:5.1f}")
        
        # Display hitters
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
        for j, hitter in enumerate(lineup['hitters'][:8]):
            pos = positions[j] if j < len(positions) else f'H{j+1}'
            star_indicator = "" if hitter['Salary'] >= 3500 else "" if hitter['Salary'] <= 2500 else "DATA:"
            logger.info(f"{pos:3} | {hitter['Nickname']:20} | {hitter['Team']:3} | {hitter['Game']:8} | ${hitter['Salary']:5,} | {hitter['FPPG']:5.1f} {star_indicator}")
        
        # Tournament rating
        if lineup['total_fppg'] >= 180:
            rating = " ELITE"
        elif lineup['total_fppg'] >= 153:
            rating = "LINEUP: COMPETITIVE"
        elif lineup['total_fppg'] >= 145:
            rating = "SUCCESS: VIABLE"
        else:
            rating = "WARNING: NEEDS WORK"
        
        logger.info(f"TARGET: Rating: {rating}")
        logger.info(f"PROGRESS: vs Disaster: +{((lineup['total_fppg'] - 31.7) / 31.7 * 100):.0f}%")
    
    return best_lineups[:top_n]

def create_fanduel_submission(lineup):
    """Create FanDuel submission format for best lineup"""
    logger.info("\n CREATING FANDUEL SUBMISSION")
    logger.info("="*50)
    
    # Create submission data
    submission_data = []
    
    # Add pitcher
    p = lineup['pitcher']
    submission_data.append({
        'Position': 'P',
        'Name': p['Nickname'],
        'Team': p['Team'],
        'Salary': p['Salary'],
        'FPPG': p['FPPG']
    })
    
    # Add hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    for i, hitter in enumerate(lineup['hitters'][:8]):
        submission_data.append({
            'Position': positions[i],
            'Name': hitter['Nickname'], 
            'Team': hitter['Team'],
            'Salary': hitter['Salary'],
            'FPPG': hitter['FPPG']
        })
    
    # Save to CSV
    df = pd.DataFrame(submission_data)
    filename = f"../data/OPTIMIZED_TOURNAMENT_LINEUP_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    logger.info(f"SUCCESS: Submission file saved: {filename}")
    logger.info("INFO: Ready for FanDuel upload!")
    
    return filename

def main():
    """Main execution"""
    logger.info("START: OPTIMIZED TOURNAMENT LINEUP GENERATOR")
    logger.info("Testing multiple combinations to beat 153 FPPG threshold")
    logger.info("="*80)
    
    try:
        # Find optimal lineups
        best_lineups = find_optimal_lineups()
        
        if not best_lineups:
            logger.error("ERROR: No valid lineups generated!")
            return
        
        # Display top lineups
        top_lineups = display_top_lineups(best_lineups, top_n=5)
        
        # Create submission for best lineup
        if top_lineups:
            best_lineup = top_lineups[0]
            submission_file = create_fanduel_submission(best_lineup)
            
            logger.info("\n" + "="*80)
            logger.info("COMPLETE: OPTIMIZATION COMPLETE!")
            logger.info(f"LINEUP: Best Projection: {best_lineup['total_fppg']:.1f} FPPG")
            logger.info(f"TARGET: Tournament Ready: {best_lineup['total_fppg'] >= 153}")
            logger.info(f" Submission File: {submission_file.split('/')[-1]}")
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
