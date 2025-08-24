import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("🎯 FINAL OPTIMIZATION PUSH")
print("Last attempt to find 150+ FPPG lineup using micro-optimizations")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000

def micro_optimize_lineup():
    """Try micro-optimizations to squeeze out maximum FPPG"""
    
    logging.info("🔬 MICRO-OPTIMIZATION ANALYSIS")
    logging.info("="*60)
    
    # Get the best combinations we've found
    best_lineups = []
    
    # Top pitchers to try
    pitchers = df[df['Position'] == 'P'].sort_values('FPPG', ascending=False)
    hitters = df[df['Position'] != 'P']
    
    # Try our best pitcher with different hitter combinations
    top_pitchers = ['Garrett Crochet', 'Zack Wheeler', 'Brandon Woodruff']
    
    for pitcher_name in top_pitchers:
        pitcher_row = pitchers[pitchers['Nickname'] == pitcher_name]
        if pitcher_row.empty:
            continue
        pitcher = pitcher_row.iloc[0]
        
        logging.info(f"\n🎯 Optimizing around {pitcher_name} (${pitcher['Salary']:,} | {pitcher['FPPG']:.1f} FPPG)")
        
        remaining_budget = SALARY_CAP - pitcher['Salary']
        
        # Get absolutely best lineup for this pitcher
        best_combo = find_absolute_best_hitters(hitters, remaining_budget)
        
        if best_combo:
            total_fppg = pitcher['FPPG'] + best_combo['total_fppg']
            total_salary = pitcher['Salary'] + best_combo['total_salary']
            
            logging.info(f"   💎 Best combo: {total_fppg:.1f} FPPG | ${total_salary:,}")
            
            best_lineups.append({
                'name': f"{pitcher_name} Optimized",
                'pitcher': pitcher,
                'hitters': best_combo['hitters'],
                'total_fppg': total_fppg,
                'total_salary': total_salary
            })
    
    # Try value pitcher + premium hitters approach
    logging.info(f"\n🎯 Value pitcher + premium hitters strategy")
    value_pitchers = pitchers[pitchers['Salary'] <= 9500].sort_values('FPPG', ascending=False)
    
    for pitcher in value_pitchers.head(5).itertuples():
        remaining_budget = SALARY_CAP - pitcher.Salary
        
        # With more budget, can we get better hitters?
        best_combo = find_absolute_best_hitters(hitters, remaining_budget)
        
        if best_combo:
            total_fppg = pitcher.FPPG + best_combo['total_fppg']
            total_salary = pitcher.Salary + best_combo['total_salary']
            
            if total_fppg > 147:  # Only show promising ones
                logging.info(f"   💎 {pitcher.Nickname}: {total_fppg:.1f} FPPG | ${total_salary:,}")
                
                best_lineups.append({
                    'name': f"{pitcher.Nickname} Value Strategy",
                    'pitcher': pitcher._asdict(),
                    'hitters': best_combo['hitters'],
                    'total_fppg': total_fppg,
                    'total_salary': total_salary
                })
    
    # Return best overall
    if best_lineups:
        return max(best_lineups, key=lambda x: x['total_fppg'])
    return None

def find_absolute_best_hitters(hitters, budget):
    """Find absolute best hitter combination within budget using exhaustive search on top players"""
    
    positions_needed = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Get top candidates for each position (reduce search space but maintain quality)
    position_candidates = {}
    
    for pos in ['C', '1B', '2B', '3B', 'SS']:
        candidates = hitters[hitters['Position'] == pos].sort_values('FPPG', ascending=False).head(8)
        position_candidates[pos] = candidates.to_dict('records')
    
    # Get top OF players
    of_candidates = hitters[hitters['Position'] == 'OF'].sort_values('FPPG', ascending=False).head(15)
    position_candidates['OF'] = of_candidates.to_dict('records')
    
    # Exhaustive search on reduced candidate set
    best_combo = None
    best_fppg = 0
    
    # Generate combinations
    import itertools
    
    logging.info(f"   🔍 Searching combinations...")
    
    # Try different OF combinations first (3 OF needed)
    for of_combo in itertools.combinations(position_candidates['OF'], 3):
        of_salary = sum(p['Salary'] for p in of_combo)
        of_fppg = sum(p['FPPG'] for p in of_combo)
        
        if of_salary > budget:
            continue
            
        remaining_budget = budget - of_salary
        
        # Try combinations for other positions
        for c in position_candidates['C'][:5]:  # Top 5 catchers
            if c['Salary'] > remaining_budget:
                continue
            for first_b in position_candidates['1B'][:5]:
                if c['Salary'] + first_b['Salary'] > remaining_budget:
                    continue
                for second_b in position_candidates['2B'][:5]:
                    if c['Salary'] + first_b['Salary'] + second_b['Salary'] > remaining_budget:
                        continue
                    for third_b in position_candidates['3B'][:5]:
                        if c['Salary'] + first_b['Salary'] + second_b['Salary'] + third_b['Salary'] > remaining_budget:
                            continue
                        for ss in position_candidates['SS'][:5]:
                            total_salary = (c['Salary'] + first_b['Salary'] + second_b['Salary'] + 
                                          third_b['Salary'] + ss['Salary'] + of_salary)
                            
                            if total_salary <= remaining_budget:
                                total_fppg = (c['FPPG'] + first_b['FPPG'] + second_b['FPPG'] + 
                                            third_b['FPPG'] + ss['FPPG'] + of_fppg)
                                
                                if total_fppg > best_fppg:
                                    best_fppg = total_fppg
                                    best_combo = {
                                        'hitters': [c, first_b, second_b, third_b, ss] + list(of_combo),
                                        'total_fppg': total_fppg,
                                        'total_salary': total_salary
                                    }
    
    return best_combo

def display_final_lineup(lineup_data):
    """Display the final optimized lineup"""
    
    if not lineup_data:
        logging.info("❌ No lineup found")
        return
    
    logging.info(f"\n🏆 {lineup_data['name'].upper()}")
    logging.info(f"📊 Projection: {lineup_data['total_fppg']:.1f} FPPG | Salary: ${lineup_data['total_salary']:,}")
    logging.info("-" * 60)
    
    if isinstance(lineup_data['pitcher'], dict):
        pitcher = lineup_data['pitcher']
        logging.info(f"P   | {pitcher['Nickname']:<20} | {pitcher['Team']} | {pitcher['Game']:<8} | ${pitcher['Salary']:,} | {pitcher['FPPG']:5.1f}")
    else:
        pitcher = lineup_data['pitcher']
        logging.info(f"P   | {pitcher['Nickname']:<20} | {pitcher['Team']} | {pitcher['Game']:<8} | ${pitcher['Salary']:,} | {pitcher['FPPG']:5.1f}")
    
    # Sort hitters by position for display
    position_order = ['C', '1B', '2B', '3B', 'SS']
    of_count = 1
    
    sorted_hitters = []
    for pos in position_order:
        for hitter in lineup_data['hitters']:
            if hitter['Position'] == pos:
                sorted_hitters.append((pos, hitter))
                break
    
    # Add OF players
    for hitter in lineup_data['hitters']:
        if hitter['Position'] == 'OF':
            sorted_hitters.append((f'OF{of_count}', hitter))
            of_count += 1
    
    for pos_label, hitter in sorted_hitters:
        star = "⭐" if hitter['Salary'] >= 4000 else "💎"
        logging.info(f"{pos_label:<3} | {hitter['Nickname']:<20} | {hitter['Team']} | {hitter['Game']:<8} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
    
    # Analysis
    logging.info(f"\n📊 FINAL ANALYSIS:")
    if lineup_data['total_fppg'] >= 153:
        logging.info("🎉 EXCEEDS 153 FPPG TARGET!")
    elif lineup_data['total_fppg'] >= 150:
        logging.info("🎯 Strong lineup - very close to target")
    elif lineup_data['total_fppg'] >= 145:
        logging.info("✅ Solid tournament lineup")
    else:
        logging.info("⚠️  Below tournament threshold")
    
    gap = 153 - lineup_data['total_fppg']
    if gap > 0:
        logging.info(f"📈 Gap to 153 FPPG: {gap:.1f}")
    else:
        logging.info(f"📈 Exceeds 153 by: {-gap:.1f}")
    
    return lineup_data

def save_final_lineup(lineup_data):
    """Save the final optimized lineup"""
    
    if not lineup_data:
        return
    
    # Create FanDuel format
    lineup_rows = []
    
    # Add pitcher
    if isinstance(lineup_data['pitcher'], dict):
        pitcher = lineup_data['pitcher']
    else:
        pitcher = {
            'Id': lineup_data['pitcher']['Id'],
            'Position': lineup_data['pitcher']['Position'],
            'First Name': lineup_data['pitcher']['First Name'],
            'Nickname': lineup_data['pitcher']['Nickname'],
            'Last Name': lineup_data['pitcher']['Last Name'],
            'FPPG': lineup_data['pitcher']['FPPG'],
            'Salary': lineup_data['pitcher']['Salary'],
            'Game': lineup_data['pitcher']['Game'],
            'Team': lineup_data['pitcher']['Team']
        }
    
    lineup_rows.append(pitcher)
    
    # Add hitters
    for hitter in lineup_data['hitters']:
        lineup_rows.append(hitter)
    
    # Create DataFrame and save
    lineup_df = pd.DataFrame(lineup_rows)
    
    # Reorder columns for FanDuel format
    column_order = ['Id', 'Position', 'First Name', 'Nickname', 'Last Name', 
                   'FPPG', 'Salary', 'Game', 'Team']
    
    for col in column_order:
        if col not in lineup_df.columns:
            lineup_df[col] = ''
    
    lineup_df = lineup_df[column_order]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/FINAL_OPTIMIZED_LINEUP_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    
    logging.info(f"\n💾 Lineup saved: {filename}")
    logging.info("📋 Ready for FanDuel upload!")

def main():
    """Run final optimization"""
    
    best_lineup = micro_optimize_lineup()
    
    if best_lineup:
        final_result = display_final_lineup(best_lineup)
        save_final_lineup(final_result)
        
        logging.info(f"\n🎯 FINAL VERDICT:")
        logging.info("="*60)
        
        if best_lineup['total_fppg'] >= 153:
            logging.info("✅ TARGET ACHIEVED! 153+ FPPG lineup found!")
        elif best_lineup['total_fppg'] >= 150:
            logging.info("🎯 CLOSE! Strong tournament potential")
        elif best_lineup['total_fppg'] >= 145:
            logging.info("✅ SOLID! Good tournament lineup")
        else:
            logging.info("⚠️  Below optimal, but still viable")
        
        logging.info(f"🏆 Best achievable: {best_lineup['total_fppg']:.1f} FPPG")
        
        if best_lineup['total_fppg'] < 153:
            logging.info(f"📊 Reality check: 153 FPPG may not be achievable on this slate")
            logging.info(f"🎯 Our best effort: {best_lineup['total_fppg']:.1f} FPPG")
    
    else:
        logging.info("❌ Unable to generate optimized lineup")

if __name__ == "__main__":
    main()
