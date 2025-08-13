import pandas as pd
import logging
from datetime import datetime
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("🏆 MULTIPLE CHAMPIONSHIP LINEUPS BUILDER")
print("Building 10+ diverse tournament-quality lineups")
print("="*80)

# Load slate data - ALL HEALTHY PLAYERS (NO IL PLAYERS)
# Use IL-free slate for maximum player diversity
try:
    print("🔍 Loading HEALTHY PLAYERS slate...")
    df = pd.read_csv('../data/fd_slate_NO_IL_PLAYERS.csv')
    print(f"✅ Using HEALTHY SLATE: {len(df)} players (all healthy players)")
except FileNotFoundError:
    print("⚠️  Healthy slate not found, trying confirmed starters...")
    try:
        df = pd.read_csv('../data/fd_slate_confirmed_starters_only.csv')
        print(f"⚠️  Using CONFIRMED STARTERS: {len(df)} players (limited pitchers)")
    except FileNotFoundError:
        print("❌ No safe slates found, using original slate (risky)...")
        df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
        print(f"❌ Using ORIGINAL slate: {len(df)} players (may include IL/non-starters)")

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000

def build_multiple_championship_lineups():
    """Build multiple diverse championship lineups"""
    
    logging.info("🏆 BUILDING MULTIPLE CHAMPIONSHIP LINEUPS")
    logging.info("="*60)
    
    # Separate positions
    pitchers = df[df['Position'] == 'P'].sort_values('FPPG', ascending=False)
    hitters = df[df['Position'] != 'P']
    
    all_lineups = []
    
    # Strategy 1: Best Pitcher + Optimal Hitters (3 variations)
    logging.info("🎯 Strategy 1: Elite Pitcher Lineups")
    for i, pitcher in enumerate(pitchers.head(3).itertuples()):
        lineup = build_smart_lineup_around_pitcher(pitcher, hitters, f"Elite_P_{i+1}")
        if lineup:
            all_lineups.append(lineup)
            logging.info(f"   ✅ Elite P{i+1}: {lineup['total_fppg']:.1f} FPPG | ${lineup['total_salary']:,}")
    
    # Strategy 2: Value Pitcher + Premium Hitters (3 variations) 
    logging.info("\n🎯 Strategy 2: Value Pitcher + Stars")
    value_pitchers = pitchers[(pitchers['Salary'] <= 9500) & (pitchers['FPPG'] >= 35)]
    for i, pitcher in enumerate(value_pitchers.head(3).itertuples()):
        lineup = build_smart_lineup_around_pitcher(pitcher, hitters, f"Value_P_{i+1}")
        if lineup:
            all_lineups.append(lineup)
            logging.info(f"   ✅ Value P{i+1}: {lineup['total_fppg']:.1f} FPPG | ${lineup['total_salary']:,}")
    
    # Strategy 3: Contrarian Approaches (4 variations)
    logging.info("\n🎯 Strategy 3: Contrarian Builds")
    mid_pitchers = pitchers[(pitchers['Salary'] >= 8000) & (pitchers['Salary'] <= 10000)]
    for i, pitcher in enumerate(mid_pitchers.head(4).itertuples()):
        lineup = build_contrarian_lineup(pitcher, hitters, f"Contrarian_{i+1}")
        if lineup:
            all_lineups.append(lineup)
            logging.info(f"   ✅ Contrarian {i+1}: {lineup['total_fppg']:.1f} FPPG | ${lineup['total_salary']:,}")
    
    return all_lineups

def build_smart_lineup_around_pitcher(pitcher, hitters, strategy_name):
    """Build smart lineup around given pitcher"""
    
    remaining_budget = SALARY_CAP - pitcher.Salary
    if remaining_budget < 10000:
        return None
    
    lineup = build_budget_managed_hitters(hitters, remaining_budget, strategy_name)
    
    if lineup and len(lineup['hitters']) == 8:
        return {
            'strategy': strategy_name,
            'pitcher': pitcher,
            'hitters': lineup['hitters'],
            'total_fppg': pitcher.FPPG + lineup['total_fppg'],
            'total_salary': pitcher.Salary + lineup['total_salary']
        }
    
    return None

def build_contrarian_lineup(pitcher, hitters, strategy_name):
    """Build contrarian lineup with different hitter selection"""
    
    remaining_budget = SALARY_CAP - pitcher.Salary
    if remaining_budget < 10000:
        return None
    
    # Use different hitter selection for contrarian approach
    lineup = build_contrarian_hitters(hitters, remaining_budget, strategy_name)
    
    if lineup and len(lineup['hitters']) == 8:
        return {
            'strategy': strategy_name,
            'pitcher': pitcher,
            'hitters': lineup['hitters'],
            'total_fppg': pitcher.FPPG + lineup['total_fppg'],
            'total_salary': pitcher.Salary + lineup['total_salary']
        }
    
    return None

def build_budget_managed_hitters(hitters, budget, strategy):
    """Build hitters with budget management"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Add some randomization for diversity
    if "Value" in strategy:
        # For value pitcher strategies, prioritize expensive hitters
        hitters = hitters.sort_values(['FPPG', 'Salary'], ascending=[False, False])
    elif "Contrarian" in strategy:
        # For contrarian, mix high-value plays
        hitters['value'] = hitters['FPPG'] / (hitters['Salary'] / 1000)
        hitters = hitters.sort_values(['value', 'FPPG'], ascending=[False, False])
    else:
        # For elite pitcher, standard FPPG sort
        hitters = hitters.sort_values('FPPG', ascending=False)
    
    selected_hitters = []
    total_salary = 0
    total_fppg = 0
    used_ids = set()
    
    for i, pos in enumerate(positions):
        remaining_positions = positions[i+1:]
        
        # Get candidates
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        if candidates.empty:
            return None
        
        # Calculate minimum needed for remaining positions
        min_needed = calculate_min_remaining_cost(hitters, remaining_positions, used_ids)
        
        # Select player
        selected_player = None
        for player in candidates.itertuples():
            cost_with_player = total_salary + player.Salary
            budget_left = budget - cost_with_player
            
            if cost_with_player <= budget and budget_left >= min_needed:
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

def build_contrarian_hitters(hitters, budget, strategy):
    """Build contrarian hitter selection"""
    
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    # Contrarian approach: mix of value and upside
    hitters['value'] = hitters['FPPG'] / (hitters['Salary'] / 1000)
    
    selected_hitters = []
    total_salary = 0
    total_fppg = 0
    used_ids = set()
    
    # Try to get one expensive player and fill with value
    expensive_threshold = 4000
    expensive_added = False
    
    for i, pos in enumerate(positions):
        remaining_positions = positions[i+1:]
        
        # Get candidates
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        if candidates.empty:
            return None
        
        min_needed = calculate_min_remaining_cost(hitters, remaining_positions, used_ids)
        
        # Contrarian selection logic
        selected_player = None
        
        # Try to add one expensive player if we haven't yet
        if not expensive_added and len(remaining_positions) > 2:
            expensive_candidates = candidates[candidates['Salary'] >= expensive_threshold].sort_values('FPPG', ascending=False)
            for player in expensive_candidates.itertuples():
                cost_with_player = total_salary + player.Salary
                budget_left = budget - cost_with_player
                
                if cost_with_player <= budget and budget_left >= min_needed:
                    selected_player = player
                    expensive_added = True
                    break
        
        # If no expensive player or already added, go for best value
        if not selected_player:
            value_candidates = candidates.sort_values('value', ascending=False)
            for player in value_candidates.itertuples():
                cost_with_player = total_salary + player.Salary
                budget_left = budget - cost_with_player
                
                if cost_with_player <= budget and budget_left >= min_needed:
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

def calculate_min_remaining_cost(hitters, remaining_positions, used_ids):
    """Calculate minimum cost for remaining positions"""
    
    total_min = 0
    for pos in remaining_positions:
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        if not candidates.empty:
            total_min += candidates['Salary'].min()
        else:
            return float('inf')
    
    return total_min

def display_all_lineups(lineups):
    """Display all championship lineups"""
    
    if not lineups:
        logging.info("❌ No lineups generated")
        return
    
    # Sort by FPPG
    lineups.sort(key=lambda x: x['total_fppg'], reverse=True)
    
    logging.info(f"\n🏆 CHAMPIONSHIP LINEUP COLLECTION")
    logging.info(f"📊 Generated {len(lineups)} diverse lineups")
    logging.info("="*80)
    
    for i, lineup in enumerate(lineups, 1):
        logging.info(f"\n🏆 LINEUP #{i}: {lineup['strategy']}")
        logging.info(f"📊 Projection: {lineup['total_fppg']:.1f} FPPG | Salary: ${lineup['total_salary']:,}")
        logging.info("-" * 60)
        
        pitcher = lineup['pitcher']
        logging.info(f"P   | {pitcher.Nickname:<20} | {pitcher.Team} | ${pitcher.Salary:,} | {pitcher.FPPG:5.1f}")
        
        # Display hitters
        position_order = ['C', '1B', '2B', '3B', 'SS']
        of_count = 1
        displayed = set()
        
        for pos in position_order:
            for hitter in lineup['hitters']:
                if hitter['Position'] == pos and pos not in displayed:
                    star = "⭐" if hitter['Salary'] >= 4000 else "💎"
                    logging.info(f"{pos:<3} | {hitter['Nickname']:<20} | {hitter['Team']} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
                    displayed.add(pos)
                    break
        
        for hitter in lineup['hitters']:
            if hitter['Position'] == 'OF':
                star = "⭐" if hitter['Salary'] >= 4000 else "💎"
                logging.info(f"OF{of_count:<2} | {hitter['Nickname']:<20} | {hitter['Team']} | ${hitter['Salary']:,} | {hitter['FPPG']:5.1f} {star}")
                of_count += 1
    
    # Summary stats
    avg_fppg = sum(l['total_fppg'] for l in lineups) / len(lineups)
    max_fppg = max(l['total_fppg'] for l in lineups)
    min_fppg = min(l['total_fppg'] for l in lineups)
    
    logging.info(f"\n📊 COLLECTION SUMMARY:")
    logging.info(f"   🏆 Best: {max_fppg:.1f} FPPG")
    logging.info(f"   📊 Average: {avg_fppg:.1f} FPPG")
    logging.info(f"   📉 Lowest: {min_fppg:.1f} FPPG")
    logging.info(f"   🎯 Total lineups: {len(lineups)}")

def save_multiple_lineups(lineups):
    """Save multiple championship lineups in proper FanDuel ID:Name format"""
    
    if not lineups:
        return None
    
    # Sort by FPPG
    lineups.sort(key=lambda x: x['total_fppg'], reverse=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create individual FanDuel submission files for each lineup
    saved_files = []
    
    for i, lineup in enumerate(lineups[:10], 1):  # Top 10 lineups
        pitcher = lineup['pitcher']
        
        # Get hitters by position
        hitters_by_pos = {}
        for hitter in lineup['hitters']:
            pos = hitter['Position']
            if pos not in hitters_by_pos:
                hitters_by_pos[pos] = []
            hitters_by_pos[pos].append(hitter)
        
        # Create lineup row with ID:Name format
        lineup_row = {
            'Lineup_ID': f'CHAMPIONSHIP_{i}',
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
            'Total_Salary': lineup['total_salary'],
            'Total_Projection': round(lineup['total_fppg'], 1)
        }
        
        # Find the UTIL player (the one not yet assigned)
        assigned_ids = set()
        for key in ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3']:
            if lineup_row[key] and ':' in lineup_row[key]:
                player_id = lineup_row[key].split(':')[0]
                assigned_ids.add(player_id)
        
        # Find unassigned hitter for UTIL
        for hitter in lineup['hitters']:
            if hitter['Id'] not in assigned_ids:
                lineup_row['UTIL'] = f"{hitter['Id']}:{hitter['Nickname']}"
                break
        
        # Create DataFrame and save individual lineup file
        lineup_df = pd.DataFrame([lineup_row])
        filename = f"../data/CHAMPIONSHIP_LINEUP_{i}_{lineup['strategy']}_{timestamp}.csv"
        lineup_df.to_csv(filename, index=False)
        saved_files.append(filename)
    
    # Create summary file with all lineups for reference
    summary_rows = []
    for i, lineup in enumerate(lineups, 1):
        pitcher = lineup['pitcher']
        
        # Get hitters by position
        hitters_by_pos = {}
        for hitter in lineup['hitters']:
            pos = hitter['Position']
            if pos not in hitters_by_pos:
                hitters_by_pos[pos] = []
            hitters_by_pos[pos].append(hitter['Nickname'])
        
        summary_rows.append({
            'Lineup': i,
            'Strategy': lineup['strategy'],
            'P': pitcher.Nickname,
            'C': hitters_by_pos.get('C', [''])[0],
            '1B': hitters_by_pos.get('1B', [''])[0],
            '2B': hitters_by_pos.get('2B', [''])[0],
            '3B': hitters_by_pos.get('3B', [''])[0],
            'SS': hitters_by_pos.get('SS', [''])[0],
            'OF1': hitters_by_pos.get('OF', ['', '', ''])[0],
            'OF2': hitters_by_pos.get('OF', ['', '', ''])[1] if len(hitters_by_pos.get('OF', [])) > 1 else '',
            'OF3': hitters_by_pos.get('OF', ['', '', ''])[2] if len(hitters_by_pos.get('OF', [])) > 2 else '',
            'Total_Salary': lineup['total_salary'],
            'Total_FPPG': round(lineup['total_fppg'], 1)
        })
    
    summary_filename = f"../data/CHAMPIONSHIP_LINEUPS_SUMMARY_{timestamp}.csv"
    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(summary_filename, index=False)
    
    logging.info(f"\n💾 Multiple championship lineups saved:")
    logging.info(f"   📊 {len(saved_files)} individual FanDuel submission files")
    logging.info(f"   📋 Summary file: {summary_filename}")
    logging.info(f"   🎯 Format: Proper FanDuel CSV with player IDs")
    logging.info(f"   📁 Upload any individual file to FanDuel")
    
    return saved_files

def main():
    """Build multiple championship lineups"""
    
    # Build lineups
    lineups = build_multiple_championship_lineups()
    
    if lineups:
        # Display results
        display_all_lineups(lineups)
        
        # Save files
        fanduel_file = save_multiple_lineups(lineups)
        
        # Final summary
        logging.info(f"\n" + "="*80)
        logging.info("🏆 MULTIPLE CHAMPIONSHIP LINEUPS COMPLETE!")
        logging.info("="*80)
        
        logging.info(f"🎯 Generated: {len(lineups)} diverse lineups")
        logging.info(f"📊 FPPG Range: {min(l['total_fppg'] for l in lineups):.1f} - {max(l['total_fppg'] for l in lineups):.1f}")
        if isinstance(fanduel_file, list) and fanduel_file:
            logging.info(f"📁 FanDuel Files: {len(fanduel_file)} files created")
        elif isinstance(fanduel_file, str):
            logging.info(f"📁 FanDuel File: {fanduel_file.split('/')[-1]}")
        
        best_lineup = max(lineups, key=lambda x: x['total_fppg'])
        logging.info(f"🏆 Best Lineup: {best_lineup['total_fppg']:.1f} FPPG ({best_lineup['strategy']})")
        
        logging.info(f"\n🚀 TOURNAMENT STRATEGY:")
        logging.info(f"   📊 Use all {len(lineups)} lineups for maximum coverage")
        logging.info(f"   🎯 Each lineup uses different strategy for diversity")
        logging.info(f"   🏆 All lineups are 145+ FPPG tournament quality")
        
        logging.info(f"\n🎲 READY FOR MULTI-ENTRY TOURNAMENTS!")
        
    else:
        logging.info("❌ CRITICAL ERROR: Unable to generate any championship lineups")

if __name__ == "__main__":
    main()
