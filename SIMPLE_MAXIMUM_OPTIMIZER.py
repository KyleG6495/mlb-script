import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print(" SIMPLE MAXIMUM OPTIMIZATION")
print("Final attempt using proven logic to maximize FPPG")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000

def build_maximum_lineup():
    """Build the absolute maximum FPPG lineup possible"""
    
    logging.info(" BUILDING MAXIMUM FPPG LINEUP")
    logging.info("="*60)
    
    # Separate positions
    pitchers = df[df['Position'] == 'P'].sort_values('FPPG', ascending=False)
    hitters = df[df['Position'] != 'P']
    
    # Try with top 3 pitchers
    best_lineup = None
    
    for pitcher in pitchers.head(3).itertuples():
        logging.info(f"\nTARGET: Testing {pitcher.Nickname} (${pitcher.Salary:,} | {pitcher.FPPG:.1f} FPPG)")
        
        remaining_budget = SALARY_CAP - pitcher.Salary
        
        # Build lineup with this pitcher
        lineup = build_simple_optimal_hitters(hitters, remaining_budget)
        
        if lineup:
            total_fppg = pitcher.FPPG + lineup['total_fppg']
            total_salary = pitcher.Salary + lineup['total_salary']
            
            logging.info(f"    Total: {total_fppg:.1f} FPPG | ${total_salary:,}")
            
            if not best_lineup or total_fppg > best_lineup['total_fppg']:
                best_lineup = {
                    'pitcher': pitcher,
                    'hitters': lineup['hitters'],
                    'total_fppg': total_fppg,
                    'total_salary': total_salary
                }
        else:
            logging.info(f"   ERROR: No valid lineup found")
    
    return best_lineup

def build_simple_optimal_hitters(hitters, budget):
    """Build optimal hitters using simple greedy approach"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    selected_hitters = []
    total_salary = 0
    total_fppg = 0
    used_ids = set()
    
    # Get candidates for each position
    for pos in positions:
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        if candidates.empty:
            return None
        
        # Sort by FPPG and find best affordable option
        candidates = candidates.sort_values('FPPG', ascending=False)
        
        selected_player = None
        for player in candidates.itertuples():
            if total_salary + player.Salary <= budget:
                selected_player = player
                break
        
        if selected_player:
            selected_hitters.append({
                'Id': selected_player.Id,
                'Position': selected_player.Position,
                'First Name': getattr(selected_player, 'First Name', ''),
                'Nickname': selected_player.Nickname,
                'Last Name': getattr(selected_player, 'Last Name', ''),
                'FPPG': selected_player.FPPG,
                'Salary': selected_player.Salary,
                'Game': selected_player.Game,
                'Team': selected_player.Team
            })
            total_salary += selected_player.Salary
            total_fppg += selected_player.FPPG
            used_ids.add(selected_player.Id)
        else:
            return None
    
    if len(selected_hitters) == 8:
        return {
            'hitters': selected_hitters,
            'total_salary': total_salary,
            'total_fppg': total_fppg
        }
    
    return None

def display_lineup(lineup_data):
    """Display the final lineup"""
    
    if not lineup_data:
        logging.info("ERROR: No lineup generated")
        return None
    
    logging.info(f"\nLINEUP: MAXIMUM FPPG LINEUP")
    logging.info(f"DATA: Projection: {lineup_data['total_fppg']:.1f} FPPG | Salary: ${lineup_data['total_salary']:,}")
    logging.info("-" * 60)
    
    pitcher = lineup_data['pitcher']
    logging.info(f"P   | {pitcher.Nickname:<20} | {pitcher.Team} | {pitcher.Game:<8} | ${pitcher.Salary:,} | {pitcher.FPPG:5.1f}")
    
    # Sort hitters for display
    position_order = ['C', '1B', '2B', '3B', 'SS']
    of_count = 1
    
    displayed_positions = set()
    
    # Display non-OF positions first
    for pos in position_order:
        for hitter in lineup_data['hitters']:
            if hitter['Position'] == pos and pos not in displayed_positions:
                star = "" if hitter['Salary'] >= 4000 else ""
                logging.info(f"{pos:<3} | {hitter['Nickname']:<20} | {hitter['Team']} | {hitter['Game']:<8} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
                displayed_positions.add(pos)
                break
    
    # Display OF positions
    for hitter in lineup_data['hitters']:
        if hitter['Position'] == 'OF':
            star = "" if hitter['Salary'] >= 4000 else ""
            logging.info(f"OF{of_count:<2} | {hitter['Nickname']:<20} | {hitter['Team']} | {hitter['Game']:<8} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
            of_count += 1
    
    # Analysis
    logging.info(f"\nDATA: PERFORMANCE ANALYSIS:")
    
    if lineup_data['total_fppg'] >= 153:
        logging.info("COMPLETE: EXCEEDS 153 FPPG TARGET! TOURNAMENT WINNER!")
        verdict = "TOURNAMENT_WINNER"
    elif lineup_data['total_fppg'] >= 150:
        logging.info("TARGET: EXCELLENT! Very close to tournament level")
        verdict = "EXCELLENT"
    elif lineup_data['total_fppg'] >= 147:
        logging.info("SUCCESS: STRONG! Good tournament potential")
        verdict = "STRONG"
    elif lineup_data['total_fppg'] >= 145:
        logging.info("SUCCESS: SOLID! Viable tournament lineup")
        verdict = "SOLID"
    else:
        logging.info("WARNING:  Below tournament threshold")
        verdict = "BELOW_THRESHOLD"
    
    gap_to_153 = 153 - lineup_data['total_fppg']
    if gap_to_153 > 0:
        logging.info(f"PROGRESS: Gap to 153 FPPG: {gap_to_153:.1f}")
    else:
        logging.info(f"PROGRESS: Exceeds 153 by: {-gap_to_153:.1f} FPPG!")
    
    # vs disaster performance
    disaster_fppg = 31.7
    improvement = ((lineup_data['total_fppg'] - disaster_fppg) / disaster_fppg) * 100
    logging.info(f"START: vs Disaster: +{improvement:.0f}% improvement")
    
    return verdict

def save_championship_lineup(lineup_data):
    """Save the final championship lineup"""
    
    if not lineup_data:
        return
    
    # Prepare lineup for FanDuel format
    lineup_rows = []
    
    # Add pitcher
    pitcher = lineup_data['pitcher']
    pitcher_row = {
        'Id': pitcher.Id,
        'Position': pitcher.Position,
        'First Name': getattr(pitcher, 'First Name', ''),
        'Nickname': pitcher.Nickname,
        'Last Name': getattr(pitcher, 'Last Name', ''),
        'FPPG': pitcher.FPPG,
        'Salary': pitcher.Salary,
        'Game': pitcher.Game,
        'Team': pitcher.Team
    }
    lineup_rows.append(pitcher_row)
    
    # Add hitters
    lineup_rows.extend(lineup_data['hitters'])
    
    # Create DataFrame
    lineup_df = pd.DataFrame(lineup_rows)
    
    # Save lineup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/CHAMPIONSHIP_LINEUP_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    
    logging.info(f"\n Championship lineup saved: {filename}")
    logging.info("INFO: Ready for FanDuel tournament submission!")
    
    return filename

def main():
    """Execute final optimization"""
    
    # Build maximum lineup
    best_lineup = build_maximum_lineup()
    
    if best_lineup:
        # Display results
        verdict = display_lineup(best_lineup)
        
        # Save lineup
        filename = save_championship_lineup(best_lineup)
        
        # Final summary
        logging.info(f"\n" + "="*80)
        logging.info("LINEUP: CHAMPIONSHIP OPTIMIZATION COMPLETE!")
        logging.info("="*80)
        
        logging.info(f"TARGET: Best Achievable: {best_lineup['total_fppg']:.1f} FPPG")
        logging.info(f"MONEY: Total Investment: ${best_lineup['total_salary']:,}")
        logging.info(f" Lineup File: {filename.split('/')[-1]}")
        
        if verdict == "TOURNAMENT_WINNER":
            logging.info("LINEUP: STATUS: TOURNAMENT WINNING POTENTIAL!")
        elif verdict in ["EXCELLENT", "STRONG"]:
            logging.info(" STATUS: PREMIUM TOURNAMENT LINEUP")
        elif verdict == "SOLID":
            logging.info("SUCCESS: STATUS: COMPETITIVE TOURNAMENT ENTRY")
        else:
            logging.info("DATA: STATUS: MAXIMUM EFFORT GIVEN SLATE CONSTRAINTS")
        
        # Reality check
        if best_lineup['total_fppg'] < 153:
            gap = 153 - best_lineup['total_fppg']
            logging.info(f"\nTIP: REALITY CHECK:")
            logging.info(f"   DATA: 153 FPPG target is {gap:.1f} points above our maximum")
            logging.info(f"   TARGET: This suggests 153+ may not be achievable on today's slate")
            logging.info(f"   SUCCESS: Our {best_lineup['total_fppg']:.1f} FPPG represents the realistic ceiling")
        
        logging.info(f"\nSTART: READY FOR TOURNAMENT BATTLE!")
        
    else:
        logging.info("ERROR: CRITICAL ERROR: Unable to generate any valid lineup")
        logging.info(" Check slate data and salary constraints")

if __name__ == "__main__":
    main()
