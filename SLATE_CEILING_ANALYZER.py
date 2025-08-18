import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print(" SLATE CEILING ANALYSIS")
print("Determining the theoretical maximum FPPG possible")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000

def analyze_slate_ceiling():
    """Analyze the theoretical maximum possible FPPG"""
    
    # Separate positions
    pitchers = df[df['Position'] == 'P'].copy()
    hitters = df[df['Position'] != 'P'].copy()
    
    logging.info("TARGET: THEORETICAL MAXIMUM ANALYSIS")
    logging.info("="*60)
    
    # Best pitcher
    best_pitcher = pitchers.loc[pitchers['FPPG'].idxmax()]
    logging.info(f" Best Pitcher: {best_pitcher['Nickname']} - ${best_pitcher['Salary']:,} | {best_pitcher['FPPG']:.1f} FPPG")
    
    # Best hitters by position
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF']
    
    logging.info("\n Best Hitters by Position:")
    best_hitters = {}
    total_dream_salary = best_pitcher['Salary']
    total_dream_fppg = best_pitcher['FPPG']
    
    for pos in positions:
        if pos == 'OF':
            pos_players = hitters[hitters['Position'] == 'OF'].sort_values('FPPG', ascending=False)
            # Get top 3 OF
            for i, player in pos_players.head(3).iterrows():
                pos_key = f"OF{len([k for k in best_hitters.keys() if k.startswith('OF')]) + 1}"
                best_hitters[pos_key] = player
                total_dream_salary += player['Salary']
                total_dream_fppg += player['FPPG']
                logging.info(f"   {pos_key}: {player['Nickname']} - ${player['Salary']:,} | {player['FPPG']:.1f} FPPG")
        else:
            pos_players = hitters[hitters['Position'] == pos].sort_values('FPPG', ascending=False)
            if not pos_players.empty:
                player = pos_players.iloc[0]
                best_hitters[pos] = player
                total_dream_salary += player['Salary']
                total_dream_fppg += player['FPPG']
                logging.info(f"   {pos}: {player['Nickname']} - ${player['Salary']:,} | {player['FPPG']:.1f} FPPG")
    
    logging.info(f"\nLINEUP: DREAM TEAM TOTALS:")
    logging.info(f"   MONEY: Total Salary: ${total_dream_salary:,}")
    logging.info(f"   DATA: Total FPPG: {total_dream_fppg:.1f}")
    logging.info(f"    Over Budget: ${total_dream_salary - SALARY_CAP:,}")
    
    # Realistic ceiling - best possible within budget
    logging.info(f"\nTARGET: REALISTIC CEILING ANALYSIS")
    logging.info("="*60)
    
    best_realistic = find_realistic_ceiling(pitchers, hitters)
    if best_realistic:
        logging.info(f" Best Realistic Lineup: {best_realistic['total_fppg']:.1f} FPPG")
        logging.info(f"MONEY: Total Salary: ${best_realistic['total_salary']:,}")
        
        # Compare to targets
        logging.info(f"\nDATA: TARGET COMPARISONS:")
        logging.info(f"   vs 153 FPPG: {best_realistic['total_fppg'] - 153:.1f} FPPG {'SUCCESS:' if best_realistic['total_fppg'] >= 153 else 'ERROR:'}")
        logging.info(f"   vs 145 FPPG: {best_realistic['total_fppg'] - 145:.1f} FPPG {'SUCCESS:' if best_realistic['total_fppg'] >= 145 else 'ERROR:'}")
        
        return best_realistic
    
    return None

def find_realistic_ceiling(pitchers, hitters):
    """Find the best possible lineup within salary constraints"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Try multiple approaches to maximize FPPG
    best_lineup = None
    
    # Approach 1: Start with best pitcher, fill optimally
    for pitcher in pitchers.sort_values('FPPG', ascending=False).head(10).itertuples():
        lineup = build_optimal_around_pitcher(pitcher, hitters, positions)
        if lineup and (not best_lineup or lineup['total_fppg'] > best_lineup['total_fppg']):
            best_lineup = lineup
    
    # Approach 2: Start with best value pitcher, maximize hitters
    value_pitchers = pitchers.copy()
    value_pitchers['value'] = value_pitchers['FPPG'] / (value_pitchers['Salary'] / 1000)
    
    for pitcher in value_pitchers.sort_values('value', ascending=False).head(15).itertuples():
        lineup = build_optimal_around_pitcher(pitcher, hitters, positions)
        if lineup and (not best_lineup or lineup['total_fppg'] > best_lineup['total_fppg']):
            best_lineup = lineup
    
    return best_lineup

def build_optimal_around_pitcher(pitcher, hitters, positions):
    """Build optimal lineup around a given pitcher"""
    
    remaining_salary = SALARY_CAP - pitcher.Salary
    if remaining_salary < 10000:  # Need minimum for hitters
        return None
    
    # Use dynamic programming approach to maximize FPPG within salary
    best_combo = find_best_hitter_combination(hitters, positions, remaining_salary)
    
    if best_combo and len(best_combo['players']) == 8:
        return {
            'pitcher': pitcher,
            'hitters': best_combo['players'],
            'total_fppg': pitcher.FPPG + best_combo['total_fppg'],
            'total_salary': pitcher.Salary + best_combo['total_salary']
        }
    
    return None

def find_best_hitter_combination(hitters, positions, budget):
    """Find best combination of hitters within budget using greedy optimization"""
    
    # Create position pools
    position_pools = {}
    for pos in set(positions):
        if pos == 'OF':
            position_pools[pos] = hitters[hitters['Position'] == 'OF'].sort_values('FPPG', ascending=False).head(20)
        else:
            position_pools[pos] = hitters[hitters['Position'] == pos].sort_values('FPPG', ascending=False).head(15)
    
    # Greedy selection with backtracking
    best_result = None
    
    # Try different strategies
    strategies = [
        'max_fppg',      # Pure FPPG maximization
        'balanced',      # Balance FPPG and value
        'value_heavy'    # Value-heavy approach
    ]
    
    for strategy in strategies:
        result = greedy_select_hitters(position_pools, positions, budget, strategy)
        if result and (not best_result or result['total_fppg'] > best_result['total_fppg']):
            best_result = result
    
    return best_result

def greedy_select_hitters(position_pools, positions, budget, strategy):
    """Greedy hitter selection with different strategies"""
    
    selected = []
    used_ids = set()
    remaining_budget = budget
    total_fppg = 0
    
    # Sort positions by scarcity (fewer good options first)
    position_order = sorted(set(positions), key=lambda p: len(position_pools[p]))
    
    for pos in position_order:
        count_needed = positions.count(pos)
        pool = position_pools[pos]
        
        # Filter out already selected
        available = pool[~pool['Id'].isin(used_ids)]
        
        # Select based on strategy
        for _ in range(count_needed):
            if available.empty:
                break
                
            selected_player = None
            
            if strategy == 'max_fppg':
                # Pure FPPG optimization
                for player in available.itertuples():
                    if player.Salary <= remaining_budget:
                        selected_player = player
                        break
            
            elif strategy == 'balanced':
                # Balance FPPG and value
                available['score'] = available['FPPG'] + (available['FPPG'] / (available['Salary'] / 1000)) * 0.3
                for player in available.sort_values('score', ascending=False).itertuples():
                    if player.Salary <= remaining_budget:
                        selected_player = player
                        break
            
            elif strategy == 'value_heavy':
                # Value-heavy approach
                available['value'] = available['FPPG'] / (available['Salary'] / 1000)
                for player in available.sort_values('value', ascending=False).itertuples():
                    if player.Salary <= remaining_budget:
                        selected_player = player
                        break
            
            if selected_player:
                selected.append(selected_player._asdict())
                used_ids.add(selected_player.Id)
                remaining_budget -= selected_player.Salary
                total_fppg += selected_player.FPPG
                
                # Remove from available
                available = available[available['Id'] != selected_player.Id]
            else:
                # Can't afford anyone for this position
                return None
    
    if len(selected) == 8:
        return {
            'players': selected,
            'total_fppg': total_fppg,
            'total_salary': budget - remaining_budget
        }
    
    return None

def main():
    """Run slate ceiling analysis"""
    
    ceiling_result = analyze_slate_ceiling()
    
    if ceiling_result:
        logging.info(f"\nLINEUP: REALISTIC CEILING BREAKDOWN:")
        logging.info("="*60)
        
        pitcher = ceiling_result['pitcher']
        logging.info(f"P   | {pitcher.Nickname:<20} | {pitcher.Team} | ${pitcher.Salary:,} | {pitcher.FPPG:5.1f}")
        
        position_map = {'C': 'C', '1B': '1B', '2B': '2B', '3B': '3B', 'SS': 'SS'}
        of_count = 1
        
        for hitter in ceiling_result['hitters']:
            if hitter['Position'] == 'OF':
                pos_label = f"OF{of_count}"
                of_count += 1
            else:
                pos_label = position_map.get(hitter['Position'], hitter['Position'])
            
            logging.info(f"{pos_label:<3} | {hitter['Nickname']:<20} | {hitter['Team']} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f}")
        
        logging.info(f"\nTARGET: CEILING ASSESSMENT:")
        if ceiling_result['total_fppg'] >= 153:
            logging.info("SUCCESS: 153+ FPPG IS ACHIEVABLE!")
        elif ceiling_result['total_fppg'] >= 150:
            logging.info("WARNING:  Close to 153 FPPG - optimization needed")
        elif ceiling_result['total_fppg'] >= 145:
            logging.info(" Moderate ceiling - strong optimization required")
        else:
            logging.info("ERROR: Low ceiling slate - 153 FPPG may not be realistic")
        
        gap_to_153 = 153 - ceiling_result['total_fppg']
        logging.info(f"DATA: Gap to 153 FPPG: {gap_to_153:.1f}")
        
        if gap_to_153 > 0:
            logging.info(f"\nTIP: To reach 153 FPPG, need:")
            logging.info(f"    {gap_to_153:.1f} additional FPPG from current selection")
            logging.info(f"    OR find players averaging {gap_to_153/9:.1f} more FPPG per position")
    
    else:
        logging.info("ERROR: Could not determine realistic ceiling")

if __name__ == "__main__":
    main()
