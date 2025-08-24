#!/usr/bin/env python3
"""
ROBUST DFS LINEUP OPTIMIZER
===========================
Fixed version that handles bad data and generates quality lineups.
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def clean_and_prepare_slate():
    """Load and clean slate data"""
    base_dir = Path(__file__).parent.parent / "data"
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    # Load slate
    slate_file = slate_dir / "fd_slate_today.csv"
    slate = pd.read_csv(slate_file)
    
    print(f"📥 Loaded {len(slate)} players from slate")
    
    # Clean bad data
    original_count = len(slate)
    
    # Remove players with negative or very low FPPG
    slate = slate[slate['FPPG'] > 2.0]  # Minimum reasonable FPPG
    print(f"🧹 Removed {original_count - len(slate)} players with bad FPPG")
    
    # Remove players with missing essential data
    slate = slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])
    
    # Fix any remaining FPPG issues
    slate['FPPG'] = slate['FPPG'].clip(lower=2.0, upper=60.0)
    
    # Calculate value metrics
    slate['projection'] = slate['FPPG']
    slate['value'] = slate['projection'] / (slate['Salary'] / 1000)
    slate['ceiling'] = slate['projection'] * 1.5
    slate['floor'] = slate['projection'] * 0.7
    
    print(f"✅ Final slate: {len(slate)} players")
    print(f"   FPPG range: {slate['FPPG'].min():.1f} - {slate['FPPG'].max():.1f}")
    print(f"   Salary range: ${slate['Salary'].min()} - ${slate['Salary'].max()}")
    print(f"   Value range: {slate['value'].min():.2f} - {slate['value'].max():.2f}")
    
    # Check position distribution
    print("\n📊 Position breakdown:")
    position_counts = {}
    for pos in ['P', 'C/1B', '2B', '3B', 'SS', 'OF']:
        count = len(slate[slate['Roster Position'].str.contains(pos, na=False)])
        position_counts[pos] = count
        print(f"   {pos}: {count} players")
    
    # Verify we have enough players for each position
    if any(count < 5 for count in position_counts.values()):
        print("⚠️  Warning: Some positions have very few players")
    
    return slate

def create_lineup(slate, strategy='balanced', used_players=None):
    """Create a single optimized lineup"""
    
    if used_players is None:
        used_players = set()
    
    # Create optimization problem
    prob = LpProblem(f"DFS_{strategy}", LpMaximize)
    
    # Decision variables
    player_vars = {}
    for idx, player in slate.iterrows():
        player_vars[player['Id']] = LpVariable(f"p_{player['Id']}", cat='Binary')
    
    # Objective function
    objective = 0
    for idx, player in slate.iterrows():
        player_id = player['Id']
        
        # Base score depends on strategy
        if strategy == 'cash':
            score = player['floor'] * 0.8 + player['value'] * 0.2
        elif strategy == 'gpp':
            score = player['ceiling'] * 0.7 + player['value'] * 0.3
        else:  # balanced
            score = player['projection'] + player['value'] * 0.1
        
        # Diversity bonus/penalty
        if player_id in used_players:
            score *= 0.9  # Small penalty for reused players
        
        objective += score * player_vars[player_id]
    
    prob += objective
    
    # Constraints
    
    # Salary constraint
    salary_constraint = lpSum([
        slate.loc[slate['Id'] == pid, 'Salary'].iloc[0] * player_vars[pid] 
        for pid in player_vars
    ])
    prob += salary_constraint <= 35000
    prob += salary_constraint >= 33000  # Use most of the budget
    
    # Position constraints
    positions = {
        'P': 1,
        'C/1B': 1, 
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3,
        'UTIL': 1
    }
    
    for position, required in positions.items():
        eligible_players = slate[slate['Roster Position'].str.contains(position, na=False)]['Id']
        if len(eligible_players) >= required:
            prob += lpSum([player_vars[pid] for pid in eligible_players]) == required
        else:
            print(f"⚠️  Not enough {position} players: {len(eligible_players)}")
            return None
    
    # Total players
    prob += lpSum([player_vars[pid] for pid in player_vars]) == 9
    
    # Solve
    prob.solve(PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:  # Optimal solution found
        selected_players = []
        total_salary = 0
        total_projection = 0
        
        for player_id, var in player_vars.items():
            if var.value() == 1:
                player_row = slate[slate['Id'] == player_id].iloc[0]
                selected_players.append(player_row)
                total_salary += player_row['Salary']
                total_projection += player_row['projection']
        
        return {
            'players': selected_players,
            'total_salary': total_salary,
            'total_projection': total_projection,
            'strategy': strategy
        }
    
    return None

def format_fanduel_lineup(lineup):
    """Format lineup for FanDuel submission"""
    players = lineup['players']
    fanduel_lineup = {}
    
    # Convert to DataFrame for easier handling
    players_df = pd.DataFrame(players)
    remaining_players = players_df.copy()
    
    # Fill positions in order
    position_order = ['P', 'C/1B', '2B', '3B', 'SS']
    
    for pos in position_order:
        eligible = remaining_players[remaining_players['Roster Position'].str.contains(pos, na=False)]
        if not eligible.empty:
            chosen = eligible.iloc[0]
            name = chosen['Nickname'] if pd.notna(chosen['Nickname']) else f"{chosen['First Name']} {chosen['Last Name']}"
            fanduel_lineup[pos] = name
            remaining_players = remaining_players[remaining_players['Id'] != chosen['Id']]
    
    # Fill OF positions
    of_eligible = remaining_players[remaining_players['Roster Position'].str.contains('OF', na=False)]
    for i, of_pos in enumerate(['OF', 'OF2', 'OF3']):
        if i < len(of_eligible):
            chosen = of_eligible.iloc[i]
            name = chosen['Nickname'] if pd.notna(chosen['Nickname']) else f"{chosen['First Name']} {chosen['Last Name']}"
            fanduel_lineup[of_pos] = name
            remaining_players = remaining_players[remaining_players['Id'] != chosen['Id']]
    
    # Fill UTIL with remaining player
    if not remaining_players.empty:
        chosen = remaining_players.iloc[0]
        name = chosen['Nickname'] if pd.notna(chosen['Nickname']) else f"{chosen['First Name']} {chosen['Last Name']}"
        fanduel_lineup['UTIL'] = name
    
    return fanduel_lineup

def generate_quality_lineups(num_lineups=20):
    """Generate high-quality diverse lineups"""
    
    print("🚀 ROBUST DFS LINEUP OPTIMIZER")
    print("=" * 50)
    
    # Load and clean data
    slate = clean_and_prepare_slate()
    
    if len(slate) < 200:
        print("❌ Not enough quality players in slate")
        return None, None
    
    print(f"\n🎯 Generating {num_lineups} optimized lineups...")
    
    lineups = []
    used_players = set()
    
    # Define lineup mix
    strategies = (
        ['cash'] * 4 + 
        ['balanced'] * 12 + 
        ['gpp'] * 4
    )
    
    for i in range(num_lineups):
        strategy = strategies[i] if i < len(strategies) else 'balanced'
        print(f"   Creating lineup {i+1}: {strategy}")
        
        lineup = create_lineup(slate, strategy, used_players)
        
        if lineup:
            lineups.append(lineup)
            
            # Add some diversity by remembering some players
            player_ids = [p['Id'] for p in lineup['players']]
            if len(lineups) % 3 == 0:  # Every 3rd lineup, add players to used set
                used_players.update(player_ids[:3])
            
            print(f"     ✅ ${lineup['total_salary']}, {lineup['total_projection']:.1f} FPPG")
        else:
            print(f"     ❌ Failed")
    
    print(f"\n📊 Successfully generated {len(lineups)} lineups")
    
    if lineups:
        projections = [l['total_projection'] for l in lineups]
        salaries = [l['total_salary'] for l in lineups]
        
        print(f"   Projection range: {min(projections):.1f} - {max(projections):.1f}")
        print(f"   Average projection: {np.mean(projections):.1f}")
        print(f"   Salary range: ${min(salaries)} - ${max(salaries)}")
        print(f"   Average salary: ${np.mean(salaries):,.0f}")
    
    return slate, lineups

def save_lineups_to_files(lineups):
    """Save lineups to FanDuel format"""
    if not lineups:
        print("❌ No lineups to save")
        return None
    
    base_dir = Path(__file__).parent.parent / "data"
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create FanDuel format data
    fanduel_data = []
    
    for i, lineup in enumerate(lineups):
        fd_lineup = format_fanduel_lineup(lineup)
        fd_lineup.update({
            'Lineup_ID': f"ROBUST_{lineup['strategy'].upper()}_{i+1}",
            'Contest_Type': lineup['strategy'],
            'Total_Salary': lineup['total_salary'],
            'Total_Projection': round(lineup['total_projection'], 2)
        })
        fanduel_data.append(fd_lineup)
    
    # Create DataFrame
    df = pd.DataFrame(fanduel_data)
    
    # Reorder columns for FanDuel
    column_order = [
        'Lineup_ID', 'Contest_Type', 'P', 'C/1B', '2B', '3B', 'SS', 
        'OF', 'OF2', 'OF3', 'UTIL', 'Total_Salary', 'Total_Projection'
    ]
    df = df.reindex(columns=column_order)
    
    # Save files
    main_file = slate_dir / "Robust_Lineups_FD_Format.csv"
    backup_file = base_dir / f"robust_fanduel_submission_{timestamp}.csv"
    
    df.to_csv(main_file, index=False)
    df.to_csv(backup_file, index=False)
    
    print(f"\n💾 Saved lineups to:")
    print(f"   📁 Main: {main_file}")
    print(f"   📁 Backup: {backup_file}")
    
    return main_file

if __name__ == "__main__":
    try:
        slate, lineups = generate_quality_lineups(20)
        
        if lineups and len(lineups) > 0:
            main_file = save_lineups_to_files(lineups)
            
            print(f"\n🎉 SUCCESS!")
            print(f"   Generated {len(lineups)} quality lineups")
            print(f"   Ready for FanDuel submission: {main_file}")
            print(f"\n💡 These lineups should perform MUCH better!")
            print(f"   - Removed players with bad projections")
            print(f"   - Used proper value-based optimization")
            print(f"   - Applied strategic diversity")
            print(f"   - Ensured good salary utilization")
            
        else:
            print("❌ Failed to generate quality lineups")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
