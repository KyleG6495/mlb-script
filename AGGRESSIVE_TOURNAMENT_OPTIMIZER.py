import pandas as pd
import numpy as np
import logging
from datetime import datetime
from itertools import combinations

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("START: AGGRESSIVE TOURNAMENT OPTIMIZER")
print("Testing unconventional combinations to beat 153 FPPG")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000
TARGET_FPPG = 153.0

def analyze_extreme_combinations():
    """Test extreme strategies to find 153+ FPPG combinations"""
    
    # Separate by position
    pitchers = df[df['Position'] == 'P'].copy()
    hitters = df[df['Position'] != 'P'].copy()
    
    # Add value metrics
    pitchers['value'] = pitchers['FPPG'] / (pitchers['Salary'] / 1000)
    hitters['value'] = hitters['FPPG'] / (hitters['Salary'] / 1000)
    
    # Sort by different criteria
    pitchers_by_fppg = pitchers.sort_values('FPPG', ascending=False)
    pitchers_by_value = pitchers.sort_values('value', ascending=False)
    hitters_by_fppg = hitters.sort_values('FPPG', ascending=False)
    hitters_by_value = hitters.sort_values('value', ascending=False)
    
    logging.info(" ANALYZING EXTREME STRATEGIES")
    
    best_lineups = []
    
    # Strategy 1: Absolute highest FPPG players regardless of value
    logging.info("\nTARGET: Strategy 1: Maximum FPPG approach")
    lineup1 = build_max_fppg_lineup(pitchers_by_fppg, hitters_by_fppg)
    if lineup1:
        best_lineups.append(("Max FPPG Strategy", lineup1))
    
    # Strategy 2: Ultra-high value plays with one superstar
    logging.info("\nTARGET: Strategy 2: Value bomb + one superstar")
    lineup2 = build_value_bomb_lineup(pitchers_by_value, hitters_by_value, hitters_by_fppg)
    if lineup2:
        best_lineups.append(("Value Bomb Strategy", lineup2))
    
    # Strategy 3: Balanced high-end approach
    logging.info("\nTARGET: Strategy 3: Balanced premium approach")
    lineup3 = build_balanced_premium_lineup(pitchers, hitters)
    if lineup3:
        best_lineups.append(("Balanced Premium", lineup3))
    
    # Strategy 4: Contrarian high upside
    logging.info("\nTARGET: Strategy 4: Contrarian high ceiling")
    lineup4 = build_contrarian_lineup(pitchers, hitters)
    if lineup4:
        best_lineups.append(("Contrarian High Ceiling", lineup4))
    
    return best_lineups

def build_max_fppg_lineup(pitchers, hitters):
    """Build lineup with absolute highest FPPG players"""
    
    # Get positions
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Try different pitcher options
    for pitcher in pitchers.head(5).itertuples():
        remaining_salary = SALARY_CAP - pitcher.Salary
        
        # Get highest FPPG hitters for each position
        lineup_hitters = []
        total_salary = pitcher.Salary
        total_fppg = pitcher.FPPG
        
        for pos in positions:
            if pos == 'OF':
                eligible = hitters[hitters['Position'].isin(['OF'])].copy()
            else:
                eligible = hitters[hitters['Position'] == pos].copy()
            
            # Remove already selected players
            for selected in lineup_hitters:
                eligible = eligible[eligible['Id'] != selected['Id']]
            
            # Sort by FPPG and try to fit in budget
            eligible = eligible.sort_values('FPPG', ascending=False)
            
            selected = None
            for player in eligible.itertuples():
                if total_salary + player.Salary <= SALARY_CAP:
                    selected = player
                    break
            
            if selected:
                lineup_hitters.append(selected._asdict())
                total_salary += selected.Salary
                total_fppg += selected.FPPG
            else:
                return None
        
        if len(lineup_hitters) == 8 and total_fppg >= TARGET_FPPG:
            logging.info(f"   SUCCESS: FOUND 153+ LINEUP: {total_fppg:.1f} FPPG")
            return {
                'pitcher': pitcher,
                'hitters': lineup_hitters,
                'total_fppg': total_fppg,
                'total_salary': total_salary
            }
        elif len(lineup_hitters) == 8:
            logging.info(f"   P: {pitcher.Nickname} | Total: {total_fppg:.1f} FPPG | Need: +{TARGET_FPPG - total_fppg:.1f}")
    
    return None

def build_value_bomb_lineup(pitchers_by_value, hitters_by_value, hitters_by_fppg):
    """Use extreme value plays with one elite hitter"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Try value pitchers
    for pitcher in pitchers_by_value.head(10).itertuples():
        if pitcher.Salary > 9500:  # Skip expensive pitchers for this strategy
            continue
            
        remaining_salary = SALARY_CAP - pitcher.Salary
        
        # Get one elite hitter
        elite_hitter = None
        for hitter in hitters_by_fppg.head(10).itertuples():
            if hitter.Salary <= remaining_salary - 14000:  # Leave room for other players
                elite_hitter = hitter
                break
        
        if not elite_hitter:
            continue
        
        # Fill rest with value plays
        lineup_hitters = [elite_hitter._asdict()]
        total_salary = pitcher.Salary + elite_hitter.Salary
        total_fppg = pitcher.FPPG + elite_hitter.FPPG
        
        remaining_positions = positions.copy()
        remaining_positions.remove(elite_hitter.Position if elite_hitter.Position != 'OF' else 'OF')
        
        for pos in remaining_positions:
            if pos == 'OF':
                eligible = hitters_by_value[hitters_by_value['Position'].isin(['OF'])].copy()
            else:
                eligible = hitters_by_value[hitters_by_value['Position'] == pos].copy()
            
            # Remove already selected
            for selected in lineup_hitters:
                eligible = eligible[eligible['Id'] != selected['Id']]
            
            # Find best value that fits
            selected = None
            for player in eligible.itertuples():
                if total_salary + player.Salary <= SALARY_CAP:
                    selected = player
                    break
            
            if selected:
                lineup_hitters.append(selected._asdict())
                total_salary += selected.Salary
                total_fppg += selected.FPPG
            else:
                break
        
        if len(lineup_hitters) == 8 and total_fppg >= TARGET_FPPG:
            logging.info(f"   SUCCESS: FOUND 153+ LINEUP: {total_fppg:.1f} FPPG")
            return {
                'pitcher': pitcher,
                'hitters': lineup_hitters,
                'total_fppg': total_fppg,
                'total_salary': total_salary
            }
        elif len(lineup_hitters) == 8:
            logging.info(f"   P: {pitcher.Nickname} + Elite | Total: {total_fppg:.1f} FPPG | Need: +{TARGET_FPPG - total_fppg:.1f}")
    
    return None

def build_balanced_premium_lineup(pitchers, hitters):
    """Build with balanced premium approach"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Try mid-tier pitchers with multiple stars
    mid_pitchers = pitchers[(pitchers['Salary'] >= 8000) & (pitchers['Salary'] <= 9500)].sort_values('FPPG', ascending=False)
    
    for pitcher in mid_pitchers.head(5).itertuples():
        remaining_salary = SALARY_CAP - pitcher.Salary
        
        # Try to get 4-5 star players
        star_budget = remaining_salary * 0.7  # 70% for stars
        value_budget = remaining_salary * 0.3  # 30% for value
        
        # Get stars first
        stars = hitters[hitters['Salary'] >= 4000].sort_values('FPPG', ascending=False)
        lineup_hitters = []
        total_salary = pitcher.Salary
        total_fppg = pitcher.FPPG
        star_count = 0
        
        # Fill positions strategically
        for pos in positions:
            if pos == 'OF':
                eligible = hitters[hitters['Position'].isin(['OF'])].copy()
            else:
                eligible = hitters[hitters['Position'] == pos].copy()
            
            # Remove selected
            for selected in lineup_hitters:
                eligible = eligible[eligible['Id'] != selected['Id']]
            
            # Try star first if budget allows and we need more stars
            selected = None
            if star_count < 4:
                star_eligible = eligible[eligible['Salary'] >= 4000].sort_values('FPPG', ascending=False)
                for player in star_eligible.itertuples():
                    if total_salary + player.Salary <= SALARY_CAP:
                        selected = player
                        star_count += 1
                        break
            
            # If no star fits, get best value
            if not selected:
                value_eligible = eligible.sort_values('FPPG', ascending=False)
                for player in value_eligible.itertuples():
                    if total_salary + player.Salary <= SALARY_CAP:
                        selected = player
                        break
            
            if selected:
                lineup_hitters.append(selected._asdict())
                total_salary += selected.Salary
                total_fppg += selected.FPPG
            else:
                break
        
        if len(lineup_hitters) == 8 and total_fppg >= TARGET_FPPG:
            logging.info(f"   SUCCESS: FOUND 153+ LINEUP: {total_fppg:.1f} FPPG")
            return {
                'pitcher': pitcher,
                'hitters': lineup_hitters,
                'total_fppg': total_fppg,
                'total_salary': total_salary
            }
        elif len(lineup_hitters) == 8:
            logging.info(f"   P: {pitcher.Nickname} + {star_count} stars | Total: {total_fppg:.1f} FPPG | Need: +{TARGET_FPPG - total_fppg:.1f}")
    
    return None

def build_contrarian_lineup(pitchers, hitters):
    """Build contrarian lineup with high ceiling players"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Look for medium-priced pitchers with upside
    contrarian_pitchers = pitchers[(pitchers['Salary'] >= 7000) & (pitchers['Salary'] <= 9000)].sort_values('value', ascending=False)
    
    for pitcher in contrarian_pitchers.head(8).itertuples():
        remaining_salary = SALARY_CAP - pitcher.Salary
        
        # Mix of one expensive hitter and several medium-price high-upside
        lineup_hitters = []
        total_salary = pitcher.Salary
        total_fppg = pitcher.FPPG
        
        # Get one expensive hitter first
        expensive_hitters = hitters[hitters['Salary'] >= 4500].sort_values('FPPG', ascending=False)
        star_added = False
        
        for pos in positions:
            if pos == 'OF':
                eligible = hitters[hitters['Position'].isin(['OF'])].copy()
            else:
                eligible = hitters[hitters['Position'] == pos].copy()
            
            # Remove selected
            for selected in lineup_hitters:
                eligible = eligible[eligible['Id'] != selected['Id']]
            
            selected = None
            
            # Add one star if we haven't yet
            if not star_added:
                star_eligible = eligible[eligible['Salary'] >= 4500].sort_values('FPPG', ascending=False)
                for player in star_eligible.itertuples():
                    if total_salary + player.Salary <= SALARY_CAP - 10000:  # Leave room for others
                        selected = player
                        star_added = True
                        break
            
            # If no star or already added, get medium-price high FPPG
            if not selected:
                medium_eligible = eligible[(eligible['Salary'] >= 3000) & (eligible['Salary'] <= 4500)].sort_values('FPPG', ascending=False)
                for player in medium_eligible.itertuples():
                    if total_salary + player.Salary <= SALARY_CAP:
                        selected = player
                        break
            
            # Last resort: any player that fits
            if not selected:
                any_eligible = eligible.sort_values('FPPG', ascending=False)
                for player in any_eligible.itertuples():
                    if total_salary + player.Salary <= SALARY_CAP:
                        selected = player
                        break
            
            if selected:
                lineup_hitters.append(selected._asdict())
                total_salary += selected.Salary
                total_fppg += selected.FPPG
            else:
                break
        
        if len(lineup_hitters) == 8 and total_fppg >= TARGET_FPPG:
            logging.info(f"   SUCCESS: FOUND 153+ LINEUP: {total_fppg:.1f} FPPG")
            return {
                'pitcher': pitcher,
                'hitters': lineup_hitters,
                'total_fppg': total_fppg,
                'total_salary': total_salary
            }
        elif len(lineup_hitters) == 8:
            logging.info(f"   P: {pitcher.Nickname} (contrarian) | Total: {total_fppg:.1f} FPPG | Need: +{TARGET_FPPG - total_fppg:.1f}")
    
    return None

def display_lineup(name, lineup_data):
    """Display a lineup in formatted output"""
    if not lineup_data:
        return
    
    logging.info(f"\nLINEUP: {name.upper()}")
    logging.info(f"DATA: Projection: {lineup_data['total_fppg']:.1f} FPPG | Salary: ${lineup_data['total_salary']:,}")
    logging.info("-" * 60)
    
    pitcher = lineup_data['pitcher']
    logging.info(f"P   | {pitcher.Nickname:<20} | {pitcher.Team} | {pitcher.Game:<8} | ${pitcher.Salary:,} | {pitcher.FPPG:5.1f}")
    
    position_map = {'C': 'C', '1B': '1B', '2B': '2B', '3B': '3B', 'SS': 'SS'}
    of_count = 1
    
    for hitter in lineup_data['hitters']:
        if hitter['Position'] == 'OF':
            pos_label = f"OF{of_count}"
            of_count += 1
        else:
            pos_label = position_map.get(hitter['Position'], hitter['Position'])
        
        star = "" if hitter['Salary'] >= 4000 else ""
        logging.info(f"{pos_label:<3} | {hitter['Nickname']:<20} | {hitter['Team']} | {hitter['Game']:<8} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
    
    rating = "TARGET: TOURNAMENT WINNER!" if lineup_data['total_fppg'] >= TARGET_FPPG else "SUCCESS: VIABLE"
    logging.info(f"TARGET: Rating: {rating}")
    
    if lineup_data['total_fppg'] >= TARGET_FPPG:
        logging.info("START: EXCEEDS 153 FPPG TARGET!")
    else:
        gap = TARGET_FPPG - lineup_data['total_fppg']
        logging.info(f"PROGRESS: Need: +{gap:.1f} FPPG to reach tournament level")

def main():
    """Run aggressive optimization"""
    
    best_lineups = analyze_extreme_combinations()
    
    logging.info("\n" + "="*80)
    logging.info("LINEUP: AGGRESSIVE OPTIMIZATION RESULTS")
    logging.info("="*80)
    
    tournament_winners = []
    viable_lineups = []
    
    for name, lineup in best_lineups:
        if lineup and lineup['total_fppg'] >= TARGET_FPPG:
            tournament_winners.append((name, lineup))
        elif lineup:
            viable_lineups.append((name, lineup))
        
        display_lineup(name, lineup)
    
    # Summary
    logging.info("\n" + "="*80)
    logging.info("DATA: OPTIMIZATION SUMMARY")
    logging.info("="*80)
    
    if tournament_winners:
        logging.info(f"COMPLETE: Found {len(tournament_winners)} tournament-winning lineups!")
        for name, lineup in tournament_winners:
            logging.info(f"   LINEUP: {name}: {lineup['total_fppg']:.1f} FPPG")
    else:
        logging.info("WARNING:  No lineups found exceeding 153 FPPG target")
        logging.info(" Analyzing why we can't reach 153+ FPPG...")
        
        # Analyze the gap
        if viable_lineups:
            best_viable = max(viable_lineups, key=lambda x: x[1]['total_fppg'])
            gap = TARGET_FPPG - best_viable[1]['total_fppg']
            logging.info(f"PROGRESS: Best viable: {best_viable[1]['total_fppg']:.1f} FPPG")
            logging.info(f"TARGET: Gap to target: {gap:.1f} FPPG")
            
            # Suggest what's needed
            if gap <= 3:
                logging.info("TIP: Small gap - need slightly better player selection")
            elif gap <= 6:
                logging.info("TIP: Medium gap - need better pitcher or 1-2 star upgrades")
            else:
                logging.info("TIP: Large gap - may need to reconsider target or slate quality")

if __name__ == "__main__":
    main()
