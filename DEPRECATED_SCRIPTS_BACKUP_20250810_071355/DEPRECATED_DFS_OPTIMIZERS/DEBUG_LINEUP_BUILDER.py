import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print("🔍 DEBUGGING LINEUP BUILDER")
print("Finding out why we can't build lineups")
print("="*80)

# Load slate data
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Clean and prepare data
df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
df = df.dropna(subset=['FPPG', 'Salary'])

SALARY_CAP = 35000

def debug_lineup_building():
    """Debug why we can't build lineups"""
    
    logging.info("🔍 DEBUGGING ANALYSIS")
    logging.info("="*60)
    
    # Check data structure
    logging.info(f"📊 Total players: {len(df)}")
    logging.info(f"📊 Columns: {list(df.columns)}")
    
    # Check positions
    pitchers = df[df['Position'] == 'P']
    hitters = df[df['Position'] != 'P']
    
    logging.info(f"📊 Pitchers: {len(pitchers)}")
    logging.info(f"📊 Hitters: {len(hitters)}")
    
    # Check position breakdown
    for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
        pos_count = len(hitters[hitters['Position'] == pos])
        logging.info(f"📊 {pos}: {pos_count} players")
    
    # Test with Garrett Crochet
    garrett = pitchers[pitchers['Nickname'] == 'Garrett Crochet'].iloc[0]
    logging.info(f"\n🎯 Testing {garrett['Nickname']}")
    logging.info(f"   Salary: ${garrett['Salary']:,}")
    logging.info(f"   Remaining budget: ${SALARY_CAP - garrett['Salary']:,}")
    
    # Try to build lineup step by step
    remaining_budget = SALARY_CAP - garrett['Salary']
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    selected_hitters = []
    total_salary = 0
    used_ids = set()
    
    logging.info(f"\n🔨 Building lineup step by step:")
    
    for i, pos in enumerate(positions):
        logging.info(f"\n   Position {i+1}: {pos}")
        
        if pos == 'OF':
            candidates = hitters[(hitters['Position'] == 'OF') & (~hitters['Id'].isin(used_ids))]
        else:
            candidates = hitters[(hitters['Position'] == pos) & (~hitters['Id'].isin(used_ids))]
        
        logging.info(f"     Available candidates: {len(candidates)}")
        
        if candidates.empty:
            logging.info(f"     ❌ No candidates available for {pos}")
            break
        
        # Sort by FPPG
        candidates = candidates.sort_values('FPPG', ascending=False)
        
        # Show top 3 candidates
        logging.info(f"     Top candidates:")
        for j, player in candidates.head(3).iterrows():
            affordable = "✅" if total_salary + player['Salary'] <= remaining_budget else "❌"
            logging.info(f"       {player['Nickname']}: ${player['Salary']:,} | {player['FPPG']:.1f} FPPG {affordable}")
        
        # Try to select
        selected_player = None
        for player in candidates.itertuples():
            if total_salary + player.Salary <= remaining_budget:
                selected_player = player
                break
        
        if selected_player:
            logging.info(f"     ✅ Selected: {selected_player.Nickname} - ${selected_player.Salary:,}")
            selected_hitters.append(selected_player)
            total_salary += selected_player.Salary
            used_ids.add(selected_player.Id)
            logging.info(f"     💰 Running total: ${total_salary:,} | Remaining: ${remaining_budget - total_salary:,}")
        else:
            logging.info(f"     ❌ No affordable player found for {pos}")
            logging.info(f"     💰 Need budget for {8 - len(selected_hitters)} more players")
            
            # Show cheapest available
            cheapest = candidates.iloc[0] if not candidates.empty else None
            if cheapest is not None:
                logging.info(f"     💸 Cheapest available: {cheapest['Nickname']} - ${cheapest['Salary']:,}")
            break
    
    logging.info(f"\n📊 FINAL RESULT:")
    logging.info(f"   Players selected: {len(selected_hitters)}/8")
    logging.info(f"   Total salary: ${total_salary:,}")
    logging.info(f"   Budget remaining: ${remaining_budget - total_salary:,}")
    
    if len(selected_hitters) == 8:
        total_fppg = garrett['FPPG'] + sum(p.FPPG for p in selected_hitters)
        logging.info(f"   Total FPPG: {total_fppg:.1f}")
        logging.info("   ✅ SUCCESSFUL LINEUP!")
        return True
    else:
        logging.info("   ❌ FAILED TO BUILD COMPLETE LINEUP")
        return False

def analyze_budget_constraints():
    """Analyze if budget constraints are realistic"""
    
    logging.info(f"\n💰 BUDGET CONSTRAINT ANALYSIS")
    logging.info("="*60)
    
    hitters = df[df['Position'] != 'P']
    
    # Find minimum cost for each position
    min_costs = {}
    for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
        pos_players = hitters[hitters['Position'] == pos]
        if not pos_players.empty:
            min_cost = pos_players['Salary'].min()
            min_costs[pos] = min_cost
            logging.info(f"   {pos}: Min cost ${min_cost:,}")
    
    # Calculate minimum hitter budget needed
    min_hitter_budget = (min_costs.get('C', 0) + min_costs.get('1B', 0) + 
                        min_costs.get('2B', 0) + min_costs.get('3B', 0) + 
                        min_costs.get('SS', 0) + min_costs.get('OF', 0) * 3)
    
    logging.info(f"\n   Minimum hitter budget needed: ${min_hitter_budget:,}")
    
    # Check with top pitchers
    pitchers = df[df['Position'] == 'P'].sort_values('FPPG', ascending=False)
    
    for pitcher in pitchers.head(5).itertuples():
        remaining = SALARY_CAP - pitcher.Salary
        feasible = "✅" if remaining >= min_hitter_budget else "❌"
        logging.info(f"   {pitcher.Nickname}: ${pitcher.Salary:,} | Remaining: ${remaining:,} {feasible}")

def main():
    """Run debugging analysis"""
    
    # Debug lineup building
    success = debug_lineup_building()
    
    # Analyze budget constraints
    analyze_budget_constraints()
    
    if not success:
        logging.info(f"\n🔧 RECOMMENDATIONS:")
        logging.info("   1. Check if salary cap is correct ($35,000)")
        logging.info("   2. Verify player salary data is accurate")
        logging.info("   3. Consider using cheaper pitcher options")
        logging.info("   4. Look for more value plays in hitter pool")

if __name__ == "__main__":
    main()
