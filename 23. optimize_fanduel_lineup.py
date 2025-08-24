import pandas as pd
import numpy as np
import joblib
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

print("START: FanDuel Lineup Optimizer - TODAY'S ACTUAL SLATE")

# 1. Load TODAY'S actual FanDuel slate
print("SWAP: Loading TODAY'S FanDuel slate...")
todays_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")

# Keep ALL players (hitters AND pitchers)
all_players_today = todays_slate.copy()

print(f"DATA: Today's slate: {len(todays_slate)} total players")
print(f"DATA: Hitters: {len(todays_slate[todays_slate['Position'] != 'P'])} available")
print(f"DATA: Pitchers: {len(todays_slate[todays_slate['Position'] == 'P'])} available")

# 2. Check what data we have for today's slate
print(f"\n Today's slate columns:")
print(all_players_today.columns.tolist())

print(f"\nDATA: Today's games:")
print(all_players_today['Game'].value_counts())

print(f"\nDATA: Position distribution:")
print(all_players_today['Position'].value_counts())

print(f"\nMONEY: Salary range: ${all_players_today['Salary'].min()} - ${all_players_today['Salary'].max()}")

# 3. Handle missing batting order data for HITTERS (pitchers don't need batting orders)
hitters_today = all_players_today[all_players_today['Position'] != 'P'].copy()
pitchers_today = all_players_today[all_players_today['Position'] == 'P'].copy()

if 'Batting Order' in hitters_today.columns and hitters_today['Batting Order'].notna().any():
    hitter_starters = hitters_today[
        (hitters_today['Batting Order'].notna()) & 
        (hitters_today['Batting Order'] >= 1) & 
        (hitters_today['Batting Order'] <= 9)
    ].copy()
    print(f"\nSUCCESS: Found {len(hitter_starters)} confirmed hitter starters with batting orders")
else:
    print(f"\nWARNING: No batting order data - using salary-based starter filtering")
    # Use salary thresholds to identify likely starters
    min_salary_by_pos = {
        'C': 2400, '1B': 2600, '2B': 2500, '3B': 2500, 'SS': 2500, 'OF': 2300
    }
    
    hitter_starters = hitters_today.copy()
    # Remove very low salary players (likely bench)
    hitter_starters = hitter_starters[hitter_starters['Salary'] >= 2300]
    print(f"Filtered to {len(hitter_starters)} hitters with salary >= $2,300")

# For pitchers, filter to probable starters only
if 'Probable Pitcher' in pitchers_today.columns:
    pitcher_starters = pitchers_today[pitchers_today['Probable Pitcher'] == 'Yes'].copy()
    print(f"SUCCESS: Found {len(pitcher_starters)} confirmed starting pitchers")
else:
    # Use salary threshold for pitchers
    pitcher_starters = pitchers_today[pitchers_today['Salary'] >= 8000].copy()
    print(f"Using {len(pitcher_starters)} high-salary pitchers (${8000}+)")

# Combine hitters and pitchers
starters = pd.concat([hitter_starters, pitcher_starters], ignore_index=True)

#  FILTER OUT INJURED PLAYERS
print(f"\n Checking for injured players...")
initial_count = len(starters)

# Check for injury indicators
if 'Injury Indicator' in starters.columns:
    injured_players = starters[starters['Injury Indicator'].notna()]
    if len(injured_players) > 0:
        print(f" Found {len(injured_players)} injured players:")
        for _, player in injured_players.iterrows():
            injury_detail = player.get('Injury Details', 'Unknown')
            print(f"  ERROR: {player['Nickname']} ({player['Team']}) - {player['Injury Indicator']} - {injury_detail}")
    
    # Remove ALL players with injury indicators
    starters = starters[starters['Injury Indicator'].isna()].copy()

# Double-check for IL in injury details
if 'Injury Details' in starters.columns:
    il_players = starters[starters['Injury Details'].str.contains('IL|Injured List|DTD|Out', case=False, na=False)]
    if len(il_players) > 0:
        print(f" Additional injured players found:")
        for _, player in il_players.iterrows():
            print(f"  ERROR: {player['Nickname']} - {player['Injury Details']}")
        starters = starters[~starters['Injury Details'].str.contains('IL|Injured List|DTD|Out', case=False, na=False)].copy()

healthy_count = len(starters)
removed_count = initial_count - healthy_count

print(f"SUCCESS: Injury filter complete:")
print(f"  - Removed: {removed_count} injured players")
print(f"  - Healthy: {healthy_count} players available")

# 4. Fix FPPG projection issue
print(f"\n Checking FPPG data...")
print(f"FPPG non-null count: {starters['FPPG'].notna().sum()}")
print(f"FPPG range: {starters['FPPG'].min():.1f} - {starters['FPPG'].max():.1f}")

if starters['FPPG'].isna().all():
    print("WARNING: All FPPG values are NaN - using salary-based projections")
    # Create projections based on salary (rough but functional)
    starters['Projected_FPPG'] = (starters['Salary'] / 300) + np.random.normal(0, 1, len(starters))
    starters['Projected_FPPG'] = starters['Projected_FPPG'].clip(lower=0)  # No negative projections
else:
    starters['Projected_FPPG'] = starters['FPPG'].fillna(starters['Salary'] / 300)

print(f"SUCCESS: Created projections: {starters['Projected_FPPG'].min():.1f} - {starters['Projected_FPPG'].max():.1f}")

# 5. Show top players by game for verification
print(f"\nINFO: TOP PLAYERS BY GAME (Salary-Based):")
for game in starters['Game'].unique():
    game_players = starters[starters['Game'] == game].nlargest(9, 'Salary')
    print(f"\n{game} - Top 9 by salary:")
    for _, player in game_players.iterrows():
        print(f"  {player['Nickname']} ({player['Roster Position']}) - ${player['Salary']} - {player['Projected_FPPG']:.1f} proj")

# 6. Prepare position data
def get_primary_position(roster_pos):
    """Extract primary position - BALANCED VERSION"""
    if pd.isna(roster_pos):
        return 'OF'
    
    pos_str = str(roster_pos).upper()
    
    # Handle pitchers first
    if 'P' in pos_str or roster_pos == 'P':
        return 'P'
    
    # Handle pure positions first
    if 'C' in pos_str and '1B' not in pos_str:  # Pure C players
        return 'C'
    elif '1B' in pos_str and 'C' not in pos_str:  # Pure 1B players
        return '1B'
    elif '2B' in pos_str and 'SS' not in pos_str and '3B' not in pos_str:  # Pure 2B
        return '2B'
    elif '3B' in pos_str and '2B' not in pos_str and 'SS' not in pos_str:  # Pure 3B
        return '3B'
    elif 'SS' in pos_str and '2B' not in pos_str and '3B' not in pos_str:  # Pure SS
        return 'SS'
    elif 'OF' in pos_str and all(pos not in pos_str for pos in ['C', '1B', '2B', '3B', 'SS']):  # Pure OF
        return 'OF'
    
    # Handle multi-position players - distribute more evenly
    if 'C' in pos_str and '1B' in pos_str:
        # For C/1B players, prefer 1B since it's more common
        return '1B'
    elif 'SS' in pos_str:
        return 'SS'
    elif '3B' in pos_str:
        return '3B'
    elif '2B' in pos_str:
        return '2B'
    elif 'C' in pos_str:
        return 'C'
    elif '1B' in pos_str:
        return '1B'
    elif 'OF' in pos_str:
        return 'OF'
    else:
        return 'OF'

def get_position_eligibility(roster_pos):
    """Get all positions a player is eligible for"""
    if pd.isna(roster_pos):
        return ['OF']
    
    pos_str = str(roster_pos).upper()
    eligible = []
    
    # Handle pitchers
    if 'P' in pos_str or roster_pos == 'P':
        eligible.append('P')
        return eligible  # Pitchers can only play P
    
    if 'C' in pos_str:
        eligible.append('C')
    if '1B' in pos_str:
        eligible.append('1B')
    if '2B' in pos_str:
        eligible.append('2B')
    if '3B' in pos_str:
        eligible.append('3B')
    if 'SS' in pos_str:
        eligible.append('SS')
    if 'OF' in pos_str:
        eligible.append('OF')
    
    return eligible if eligible else ['OF']

starters['Primary_Position'] = starters['Roster Position'].apply(get_primary_position)
starters['All_Positions'] = starters['Roster Position'].apply(get_position_eligibility)

print(f"\nDATA: CORRECTED position distribution:")
print(starters['Primary_Position'].value_counts())

# Show both C and 1B eligible players
eligible_c = starters[starters['All_Positions'].apply(lambda x: 'C' in x)]
eligible_1b = starters[starters['All_Positions'].apply(lambda x: '1B' in x)]

print(f"\n Players eligible for C ({len(eligible_c)}):")
for _, player in eligible_c.head(3).iterrows():
    print(f"  {player['Nickname']} ({player['Roster Position']}) - ${player['Salary']}")

print(f"\n Players eligible for 1B ({len(eligible_1b)}):")
for _, player in eligible_1b.head(3).iterrows():
    print(f"  {player['Nickname']} ({player['Roster Position']}) - ${player['Salary']}")

# Manual fix: Ensure we have both C and 1B players
c_count = len(starters[starters['Primary_Position'] == 'C'])
b1_count = len(starters[starters['Primary_Position'] == '1B'])

print(f"\nSTEP: Current assignment: {c_count} C players, {b1_count} 1B players")

# We need at least 1 C and 1 1B
if c_count < 1 or b1_count < 1:
    print("STEP: Rebalancing positions to ensure we have both C and 1B...")
    
    # Find all C/1B dual eligible players
    dual_eligible = starters[starters['All_Positions'].apply(lambda x: 'C' in x and '1B' in x)]
    
    if len(dual_eligible) >= 2:  # Need at least 2 to split between C and 1B
        # Sort by salary (highest first)
        dual_sorted = dual_eligible.sort_values('Salary', ascending=False)
        
        # Assign top player to C, second player to 1B
        top_for_c = dual_sorted.iloc[0:1]  # Best player goes to C
        rest_for_1b = dual_sorted.iloc[1:]  # Rest go to 1B
        
        # Update assignments
        starters.loc[top_for_c.index, 'Primary_Position'] = 'C'
        starters.loc[rest_for_1b.index, 'Primary_Position'] = '1B'
        
        print(f"SUCCESS: Assigned to C: {top_for_c.iloc[0]['Nickname']} (${top_for_c.iloc[0]['Salary']})")
        print(f"SUCCESS: Assigned to 1B: {len(rest_for_1b)} players")
        
        # Show first few 1B assignments
        for _, player in rest_for_1b.head(3).iterrows():
            print(f"   {player['Nickname']} (${player['Salary']})")
    else:
        print("ERROR: Not enough dual-eligible C/1B players for proper split")

# Final verification
c_count_final = len(starters[starters['Primary_Position'] == 'C'])
b1_count_final = len(starters[starters['Primary_Position'] == '1B'])

print(f"\nDATA: FINAL REBALANCED position distribution:")
print(starters['Primary_Position'].value_counts())
print(f"SUCCESS: Catchers: {c_count_final}, First Basemen: {b1_count_final}")

# 7. Filter for lineup optimization
valid_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF']
lineup_pool = starters[
    (starters['Primary_Position'].isin(valid_positions)) &
    (starters['Salary'] >= 2000) &  # Minimum viable salary
    (starters['Projected_FPPG'] > 0)  # Positive projections
].copy()

print(f"\nDATA: Final lineup pool: {len(lineup_pool)} players")

# Check position availability
for pos in valid_positions:
    count = len(lineup_pool[lineup_pool['Primary_Position'] == pos])
    print(f"  {pos}: {count} players available")

if len(lineup_pool) < 9:
    print("ERROR: Not enough players for optimization!")
    exit()

# 8. Create optimization problem with STACKING
print("\nTARGET: Setting up lineup optimization with STACKING STRATEGY...")

def optimize_with_stacking(lineup_pool, strategy='balanced'):
    """Optimize lineup with stacking considerations"""
    
    prob = LpProblem(f"FanDuel_Stack_{strategy}", LpMaximize)
    
    # Decision variables
    player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in lineup_pool.index}
    
    # Base objective: Maximize projected FPPG
    base_objective = lpSum(lineup_pool.loc[i, 'Projected_FPPG'] * player_vars[i] for i in lineup_pool.index)
    
    # STACKING BONUSES
    stacking_bonus = 0
    
    # 1. Team Stack Bonus (3+ players from same team)
    print(" Adding team stacking bonuses...")
    team_stack_vars = {}
    
    for team in lineup_pool[lineup_pool['Primary_Position'] != 'P']['Team'].unique():
        team_hitters = lineup_pool[
            (lineup_pool['Team'] == team) & 
            (lineup_pool['Primary_Position'] != 'P')
        ].index
        
        if len(team_hitters) >= 3:
            # Create team stack variable
            stack_var = LpVariable(f"team_stack_{team}", cat='Binary')
            team_stack_vars[team] = stack_var
            
            # Team stack constraints
            prob += lpSum(player_vars[i] for i in team_hitters) >= 3 * stack_var
            prob += lpSum(player_vars[i] for i in team_hitters) <= 8 * stack_var + 2
            
            # Calculate team stack value
            team_avg_projection = lineup_pool.loc[team_hitters, 'Projected_FPPG'].mean()
            team_bonus = team_avg_projection * 0.15  # 15% bonus for team correlation
            
            stacking_bonus += stack_var * team_bonus
            print(f"  DATA: {team}: {len(team_hitters)} eligible, {team_bonus:.1f} bonus points")
    
    # 2. Game Stack Bonus (multiple players from high-scoring games)
    print("\n Adding game stacking bonuses...")
    game_stack_vars = {}
    
    for game in lineup_pool['Game'].unique():
        game_hitters = lineup_pool[
            (lineup_pool['Game'] == game) & 
            (lineup_pool['Primary_Position'] != 'P')
        ].index
        
        if len(game_hitters) >= 4:
            game_var = LpVariable(f"game_stack_{game.replace('@', '_')}", cat='Binary')
            game_stack_vars[game] = game_var
            
            prob += lpSum(player_vars[i] for i in game_hitters) >= 4 * game_var
            prob += lpSum(player_vars[i] for i in game_hitters) <= 8 * game_var + 3
            
            game_total_projection = lineup_pool.loc[game_hitters, 'Projected_FPPG'].sum()
            game_bonus = game_total_projection * 0.08  # 8% bonus for game correlation
            
            stacking_bonus += game_var * game_bonus
            print(f"   {game}: {len(game_hitters)} eligible, {game_bonus:.1f} bonus points")
    
    # 3. Batting Order Correlation Bonus
    if 'Batting Order' in lineup_pool.columns:
        print("\n Adding batting order correlation...")
        
        # Bonus for consecutive batters from same team
        for team in lineup_pool[lineup_pool['Primary_Position'] != 'P']['Team'].unique():
            team_players = lineup_pool[
                (lineup_pool['Team'] == team) & 
                (lineup_pool['Primary_Position'] != 'P') &
                (lineup_pool['Batting Order'].notna())
            ]
            
            if len(team_players) >= 2:
                # Check for consecutive batting orders
                for i in range(1, 8):  # Batting orders 1-8
                    consec_players = team_players[
                        team_players['Batting Order'].isin([i, i+1])
                    ].index
                    
                    if len(consec_players) == 2:
                        consec_var = LpVariable(f"consec_{team}_{i}", cat='Binary')
                        prob += lpSum(player_vars[j] for j in consec_players) >= 2 * consec_var
                        prob += lpSum(player_vars[j] for j in consec_players) <= 2 * consec_var
                        
                        stacking_bonus += consec_var * 2  # 2 point bonus for consecutive batters
    
    # Combined objective with stacking
    prob += base_objective + stacking_bonus
    
    # Standard constraints
    prob += lpSum(player_vars[i] for i in lineup_pool.index) == 9
    prob += lpSum(lineup_pool.loc[i, 'Salary'] * player_vars[i] for i in lineup_pool.index) <= 35000
    
    # Position constraints
    position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    
    for pos, required in position_requirements.items():
        pos_players = lineup_pool[lineup_pool['Primary_Position'] == pos].index
        if len(pos_players) >= required:
            prob += lpSum(player_vars[i] for i in pos_players) == required
        else:
            print(f"WARNING: Warning: Only {len(pos_players)} {pos} players available, need {required}")
    
    return prob, player_vars, team_stack_vars, game_stack_vars

# Run optimization with stacking
prob, player_vars, team_stack_vars, game_stack_vars = optimize_with_stacking(lineup_pool)

# 9. Solve optimization
print("SWAP: Solving optimization with STACKING STRATEGY...")
solver = PULP_CBC_CMD(msg=False)
status = prob.solve(solver)

print(f"Solver Status: {status}")

if status == 1:  # Optimal solution found
    selected_indices = [i for i in lineup_pool.index if player_vars[i].value() == 1]
    lineup = lineup_pool.loc[selected_indices].copy()
    
    lineup['Value'] = lineup['Projected_FPPG'] / lineup['Salary'] * 1000
    
    # Sort by position for display
    position_order = {'P': 1, 'C': 2, '1B': 3, '2B': 4, '3B': 5, 'SS': 6, 'OF': 7}
    lineup['pos_order'] = lineup['Primary_Position'].map(position_order)
    lineup = lineup.sort_values('pos_order')
    
    print(f"\nLINEUP: OPTIMAL STACKED LINEUP - TODAY'S ACTUAL SLATE:")
    display_cols = ['Nickname', 'Primary_Position', 'Team', 'Game', 'Salary', 'Projected_FPPG', 'Value']
    if 'Batting Order' in lineup.columns:
        display_cols.insert(3, 'Batting Order')
    print(lineup[display_cols].to_string(index=False))
    
    print(f"\nMONEY: Total Salary: ${lineup['Salary'].sum():,}")
    print(f"TARGET: Total Projected FPPG: {lineup['Projected_FPPG'].sum():.2f}")
    print(f"PROGRESS: Average Value: {lineup['Value'].mean():.1f} pts/$1K")
    
    # ANALYZE STACKING IN THE LINEUP
    print(f"\n STACKING ANALYSIS:")
    
    # Team stacks
    hitters = lineup[lineup['Primary_Position'] != 'P']
    team_counts = hitters['Team'].value_counts()
    team_stacks = team_counts[team_counts >= 2]
    
    if len(team_stacks) > 0:
        print(f"DATA: Team Stacks:")
        for team, count in team_stacks.items():
            team_players = hitters[hitters['Team'] == team]
            team_projection = team_players['Projected_FPPG'].sum()
            print(f"   {team}: {count} players, {team_projection:.1f} combined projection")
            
            # Show batting order if available
            if 'Batting Order' in team_players.columns:
                batting_orders = team_players['Batting Order'].dropna().sort_values()
                if len(batting_orders) > 0:
                    print(f"     Batting orders: {batting_orders.tolist()}")
    else:
        print(f"DATA: No team stacks (2+ players) in lineup")
    
    # Game stacks
    game_counts = lineup['Game'].value_counts()
    game_stacks = game_counts[game_counts >= 2]
    
    if len(game_stacks) > 0:
        print(f"\n Game Stacks:")
        for game, count in game_stacks.items():
            game_players = lineup[lineup['Game'] == game]
            game_projection = game_players['Projected_FPPG'].sum()
            teams_in_stack = game_players['Team'].unique()
            print(f"   {game}: {count} players, {game_projection:.1f} combined projection")
            print(f"     Teams: {', '.join(teams_in_stack)}")
    
    # Check which stacking bonuses were activated
    print(f"\n ACTIVATED STACKING BONUSES:")
    
    active_team_stacks = [team for team, var in team_stack_vars.items() if var.value() == 1]
    if active_team_stacks:
        print(f"   Team stacks: {', '.join(active_team_stacks)}")
    
    active_game_stacks = [game for game, var in game_stack_vars.items() if var.value() == 1]
    if active_game_stacks:
        print(f"  TARGET: Game stacks: {', '.join(active_game_stacks)}")
    
    if not active_team_stacks and not active_game_stacks:
        print(f"  DATA: No major stacking bonuses activated (pure value lineup)")
    
    # Correlation score
    correlation_score = 0
    if len(team_stacks) > 0:
        correlation_score += sum(count * 10 for count in team_stacks)
    if len(game_stacks) > 0:
        correlation_score += sum(count * 5 for count in game_stacks)
    
    print(f"PROGRESS: Correlation Score: {correlation_score} (higher = more correlated)")
    
    # Verify all players are in today's slate
    print(f"\nSUCCESS: LINEUP VERIFICATION:")
    print(f"All players confirmed in today's slate: {all(lineup['Nickname'].isin(todays_slate['Nickname']))}")
    
    # Save lineup with stacking info
    output_file = "../data/todays_stacked_lineup.csv"
    lineup.to_csv(output_file, index=False)
    print(f"SUCCESS: Saved STACKED lineup to {output_file}")
    
    # Show alternatives from non-selected teams
    print(f"\n TOP ALTERNATIVES FROM OTHER TEAMS:")
    selected_teams = lineup['Team'].unique()
    alternatives = lineup_pool[
        ~lineup_pool.index.isin(selected_indices) &
        ~lineup_pool['Team'].isin(selected_teams)
    ].nlargest(5, 'Projected_FPPG')
    
    if len(alternatives) > 0:
        alt_cols = ['Nickname', 'Primary_Position', 'Team', 'Salary', 'Projected_FPPG']
        print(alternatives[alt_cols].to_string(index=False))
    else:
        print("All major teams represented in lineup")
    
else:
    print("ERROR: No optimal solution found with stacking constraints.")

# 10. Show today's games summary
print(f"\nINFO: TODAY'S GAMES SUMMARY:")
for game in todays_slate['Game'].unique():
    if 'P' not in game:  # Skip if malformed
        teams = game.split('@')
        if len(teams) == 2:
            print(f"  {teams[0]} @ {teams[1]}")