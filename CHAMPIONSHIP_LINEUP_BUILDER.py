import pandas as pd
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("SUCCESS: WORKING LINEUP BUILDER")
print("Building lineups with proper budget management")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

# CRITICAL: Filter to ONLY confirmed starting pitchers
df['Probable Pitcher'] = df['Probable Pitcher'].fillna('').str.strip().str.lower()
confirmed_starters = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'yes')].copy()

logging.info(f"WARNING:  CONFIRMED STARTING PITCHERS TODAY: {len(confirmed_starters)}")
for pitcher in confirmed_starters.itertuples():
    logging.info(f"   INFO: {pitcher.Nickname} - ${pitcher.Salary:,} - {pitcher.FPPG:.1f} FPPG")

SALARY_CAP = 35000

def build_budget_managed_lineup():
    """Build lineup with proper budget management using ONLY confirmed starting pitchers"""
    
    logging.info("SUCCESS: BUILDING BUDGET-MANAGED LINEUP WITH CONFIRMED STARTERS")
    logging.info("="*60)
    
    # Use ONLY confirmed starting pitchers
    pitchers = confirmed_starters.sort_values('FPPG', ascending=False)
    hitters = df[df['Position'] != 'P']
    
    if pitchers.empty:
        logging.error("ERROR: NO CONFIRMED STARTING PITCHERS AVAILABLE!")
        return None
    
    best_lineup = None
    
    # Try confirmed starting pitchers only
    for pitcher in pitchers.itertuples():
        logging.info(f"\nTARGET: Testing {pitcher.Nickname} (${pitcher.Salary:,} | {pitcher.FPPG:.1f} FPPG) [CONFIRMED STARTER]")
        
        remaining_budget = SALARY_CAP - pitcher.Salary
        
        # Build lineup with budget management
        lineup = build_smart_hitter_lineup(hitters, remaining_budget)
        
        if lineup:
            total_fppg = pitcher.FPPG + lineup['total_fppg']
            total_salary = pitcher.Salary + lineup['total_salary']
            
            logging.info(f"   SUCCESS: Success: {total_fppg:.1f} FPPG | ${total_salary:,}")
            
            if not best_lineup or total_fppg > best_lineup['total_fppg']:
                best_lineup = {
                    'pitcher': pitcher,
                    'hitters': lineup['hitters'],
                    'total_fppg': total_fppg,
                    'total_salary': total_salary
                }
        else:
            logging.info(f"   ERROR: Failed to build complete lineup")
    
    return best_lineup

def build_smart_hitter_lineup(hitters, budget):
    """Build hitter lineup with smart budget allocation"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Calculate minimum budget needed for remaining positions
    def get_min_costs_remaining(remaining_positions, used_ids):
        min_total = 0
        for pos in remaining_positions:
            if pos == 'OF':
                candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
            else:
                candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
            
            if not candidates.empty:
                min_cost = candidates['Salary'].min()
                min_total += min_cost
            else:
                return float('inf')  # No candidates available
        return min_total
    
    selected_hitters = []
    total_salary = 0
    total_fppg = 0
    used_ids = set()
    
    for i, pos in enumerate(positions):
        remaining_positions = positions[i+1:]
        
        # Get candidates for this position
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        if candidates.empty:
            return None
        
        # Sort by FPPG
        candidates = candidates.sort_values('FPPG', ascending=False)
        
        # Find best player we can afford while leaving budget for remaining positions
        selected_player = None
        
        for player in candidates.itertuples():
            # Check if we can afford this player AND have budget for remaining positions
            cost_with_player = total_salary + player.Salary
            budget_left = budget - cost_with_player
            min_needed_for_rest = get_min_costs_remaining(remaining_positions, used_ids | {player.Id})
            
            if cost_with_player <= budget and budget_left >= min_needed_for_rest:
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

def optimize_lineup_swaps(lineup_data):
    """Try to optimize by swapping players for better FPPG"""
    
    if not lineup_data:
        return lineup_data
    
    logging.info(f"\nSWAP: OPTIMIZING SWAPS")
    
    original_fppg = lineup_data['total_fppg']
    hitters = df[df['Position'] != 'P']
    
    # Try swapping each hitter for a better option
    improved = False
    
    for i, current_hitter in enumerate(lineup_data['hitters']):
        current_pos = current_hitter['Position']
        current_salary = current_hitter['Salary']
        current_fppg = current_hitter['FPPG']
        
        # Get other players at this position
        if current_pos == 'OF':
            candidates = hitters[hitters['Position'] == 'OF']
        else:
            candidates = hitters[hitters['Position'] == current_pos]
        
        # Remove current player and others already in lineup
        used_ids = {h['Id'] for h in lineup_data['hitters']}
        candidates = candidates[~candidates['Id'].isin(used_ids)]
        
        # Calculate available budget for swap
        other_hitters_salary = sum(h['Salary'] for j, h in enumerate(lineup_data['hitters']) if j != i)
        available_budget = SALARY_CAP - lineup_data['pitcher'].Salary - other_hitters_salary
        
        # Look for better players within budget
        affordable_candidates = candidates[candidates['Salary'] <= available_budget]
        
        if not affordable_candidates.empty:
            best_candidate = affordable_candidates.loc[affordable_candidates['FPPG'].idxmax()]
            
            if best_candidate['FPPG'] > current_fppg:
                # Make the swap
                logging.info(f"   SWAP: Swapping {current_hitter['Nickname']} for {best_candidate['Nickname']}")
                logging.info(f"     FPPG: {current_fppg:.1f}  {best_candidate['FPPG']:.1f} (+{best_candidate['FPPG'] - current_fppg:.1f})")
                
                lineup_data['hitters'][i] = {
                    'Id': best_candidate['Id'],
                    'Position': best_candidate['Position'],
                    'First Name': best_candidate.get('First Name', ''),
                    'Nickname': best_candidate['Nickname'],
                    'Last Name': best_candidate.get('Last Name', ''),
                    'FPPG': best_candidate['FPPG'],
                    'Salary': best_candidate['Salary'],
                    'Game': best_candidate['Game'],
                    'Team': best_candidate['Team']
                }
                
                # Recalculate totals
                lineup_data['total_salary'] = (lineup_data['pitcher'].Salary + 
                                             sum(h['Salary'] for h in lineup_data['hitters']))
                lineup_data['total_fppg'] = (lineup_data['pitcher'].FPPG + 
                                           sum(h['FPPG'] for h in lineup_data['hitters']))
                improved = True
    
    if improved:
        improvement = lineup_data['total_fppg'] - original_fppg
        logging.info(f"   SUCCESS: Optimization complete: +{improvement:.1f} FPPG improvement")
    else:
        logging.info(f"   SUCCESS: No beneficial swaps found")
    
    return lineup_data

def display_final_championship_lineup(lineup_data):
    """Display the championship lineup"""
    
    if not lineup_data:
        logging.info("ERROR: No lineup to display")
        return
    
    logging.info(f"\nLINEUP: CHAMPIONSHIP LINEUP")
    logging.info(f"DATA: Projection: {lineup_data['total_fppg']:.1f} FPPG | Salary: ${lineup_data['total_salary']:,}")
    logging.info("="*80)
    
    pitcher = lineup_data['pitcher']
    logging.info(f"P   | {pitcher.Nickname:<20} | {pitcher.Team} | {pitcher.Game:<8} | ${pitcher.Salary:,} | {pitcher.FPPG:5.1f}")
    
    # Display hitters in position order
    position_order = ['C', '1B', '2B', '3B', 'SS']
    of_count = 1
    displayed_positions = set()
    
    # Display non-OF positions
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
    
    # Performance analysis
    logging.info(f"\nDATA: CHAMPIONSHIP ANALYSIS:")
    logging.info("="*60)
    
    if lineup_data['total_fppg'] >= 153:
        logging.info("COMPLETE: EXCEEDS 153 FPPG TARGET! TOURNAMENT CHAMPION!")
        status = "CHAMPION"
    elif lineup_data['total_fppg'] >= 150:
        logging.info("LINEUP: ELITE! Strong tournament potential")
        status = "ELITE"
    elif lineup_data['total_fppg'] >= 147:
        logging.info(" PREMIUM! Excellent tournament lineup")
        status = "PREMIUM"
    elif lineup_data['total_fppg'] >= 145:
        logging.info("SUCCESS: SOLID! Good tournament entry")
        status = "SOLID"
    else:
        logging.info("DATA: BASELINE! Competitive but needs optimization")
        status = "BASELINE"
    
    gap_to_153 = 153 - lineup_data['total_fppg']
    if gap_to_153 > 0:
        logging.info(f"TARGET: Gap to 153 FPPG: {gap_to_153:.1f}")
    else:
        logging.info(f"START: Exceeds 153 by: {-gap_to_153:.1f} FPPG!")
    
    # Comparison to disaster
    disaster_fppg = 31.7
    improvement = ((lineup_data['total_fppg'] - disaster_fppg) / disaster_fppg) * 100
    logging.info(f"PROGRESS: vs Disaster Performance: +{improvement:.0f}% improvement")
    
    return status

def save_championship_submission(lineup_data):
    """Save championship lineup for FanDuel submission in ID:Name format"""
    
    if not lineup_data:
        return None
    
    # Create FanDuel lineup format (single row with ID:Name format)
    pitcher = lineup_data['pitcher']
    
    # Get hitters by position
    hitters_by_pos = {}
    for hitter in lineup_data['hitters']:
        pos = hitter['Position']
        if pos not in hitters_by_pos:
            hitters_by_pos[pos] = []
        hitters_by_pos[pos].append(hitter)
    
    # Create lineup row with ID:Name format
    lineup_row = {
        'Lineup_ID': 'CHAMPIONSHIP_1',
        'Contest_Type': 'tournament',
        'P': f"{pitcher.Id}:{pitcher.Nickname}",
        'C/1B': f"{hitters_by_pos.get('C', [{}])[0].get('Id', '')}:{hitters_by_pos.get('C', [{}])[0].get('Nickname', '')}" if hitters_by_pos.get('C') else f"{hitters_by_pos.get('1B', [{}])[0].get('Id', '')}:{hitters_by_pos.get('1B', [{}])[0].get('Nickname', '')}" if hitters_by_pos.get('1B') else '',
        '2B': f"{hitters_by_pos.get('2B', [{}])[0].get('Id', '')}:{hitters_by_pos.get('2B', [{}])[0].get('Nickname', '')}" if hitters_by_pos.get('2B') else '',
        '3B': f"{hitters_by_pos.get('3B', [{}])[0].get('Id', '')}:{hitters_by_pos.get('3B', [{}])[0].get('Nickname', '')}" if hitters_by_pos.get('3B') else '',
        'SS': f"{hitters_by_pos.get('SS', [{}])[0].get('Id', '')}:{hitters_by_pos.get('SS', [{}])[0].get('Nickname', '')}" if hitters_by_pos.get('SS') else '',
        'OF': f"{hitters_by_pos.get('OF', [{}])[0].get('Id', '')}:{hitters_by_pos.get('OF', [{}])[0].get('Nickname', '')}" if len(hitters_by_pos.get('OF', [])) > 0 else '',
        'OF2': f"{hitters_by_pos.get('OF', [{}])[1].get('Id', '')}:{hitters_by_pos.get('OF', [{}])[1].get('Nickname', '')}" if len(hitters_by_pos.get('OF', [])) > 1 else '',
        'OF3': f"{hitters_by_pos.get('OF', [{}])[2].get('Id', '')}:{hitters_by_pos.get('OF', [{}])[2].get('Nickname', '')}" if len(hitters_by_pos.get('OF', [])) > 2 else '',
        'UTIL': '',  # Will be filled with remaining player
        'Total_Salary': lineup_data['total_salary'],
        'Total_Projection': round(lineup_data['total_fppg'], 1)
    }
    
    # Find the UTIL player (the one not yet assigned)
    assigned_ids = set()
    for key in ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3']:
        if lineup_row[key] and ':' in lineup_row[key]:
            player_id = lineup_row[key].split(':')[0]
            assigned_ids.add(player_id)
    
    # Find unassigned hitter for UTIL
    for hitter in lineup_data['hitters']:
        if hitter['Id'] not in assigned_ids:
            lineup_row['UTIL'] = f"{hitter['Id']}:{hitter['Nickname']}"
            break
    
    # Create DataFrame and save
    lineup_df = pd.DataFrame([lineup_row])
    
    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../data/CHAMPIONSHIP_SUBMISSION_{timestamp}.csv"
    lineup_df.to_csv(filename, index=False)
    
    logging.info(f"\n Championship submission saved: {filename}")
    logging.info("INFO: Ready for FanDuel tournament upload!")
    logging.info(f"TARGET: Format: ID:Name format for direct FanDuel upload")
    
    return filename

def main():
    """Execute championship lineup building"""
    
    # Build initial lineup
    best_lineup = build_budget_managed_lineup()
    
    if best_lineup:
        # Optimize with swaps
        optimized_lineup = optimize_lineup_swaps(best_lineup)
        
        # Display final result
        status = display_final_championship_lineup(optimized_lineup)
        
        # Save for submission
        filename = save_championship_submission(optimized_lineup)
        
        # Final championship summary
        logging.info(f"\n" + "="*80)
        logging.info("LINEUP: CHAMPIONSHIP LINEUP COMPLETE!")
        logging.info("="*80)
        
        logging.info(f"TARGET: Final Score: {optimized_lineup['total_fppg']:.1f} FPPG")
        logging.info(f"MONEY: Total Salary: ${optimized_lineup['total_salary']:,}")
        logging.info(f" Submission File: {filename.split('/')[-1]}")
        logging.info(f" Status: {status}")
        
        # Reality assessment
        if optimized_lineup['total_fppg'] >= 153:
            logging.info(f"COMPLETE: MISSION ACCOMPLISHED! Target exceeded!")
        else:
            gap = 153 - optimized_lineup['total_fppg']
            logging.info(f"DATA: Gap to 153 target: {gap:.1f} FPPG")
            logging.info(f"TARGET: This appears to be the realistic ceiling for today's slate")
            logging.info(f"SUCCESS: {optimized_lineup['total_fppg']:.1f} FPPG represents our maximum effort")
        
        logging.info(f"\nSTART: READY FOR TOURNAMENT GLORY!")
        
    else:
        logging.info("ERROR: CRITICAL FAILURE: Unable to build championship lineup")

if __name__ == "__main__":
    main()
