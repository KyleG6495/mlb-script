import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD

# Load data
df = pd.read_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/finalize_hitter_features.csv')
fd_df = pd.read_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/fd_hitter_features_final.csv')

# Normalize player_id to match formats
df['player_id'] = df['player_id'].astype(str).str.replace('118689-', '')
fd_df['player_id'] = fd_df['player_id'].astype(str)

# Debug player_id matches
common_ids = set(df['player_id']).intersection(set(fd_df['player_id']))
print(f"Common player_ids: {len(common_ids)} out of {len(df)} in finalize_hitter_features.csv")
print("Sample player_ids in finalize_hitter_features.csv:", df['player_id'].head().tolist())
print("Sample player_ids in fd_hitter_features_final.csv:", fd_df['player_id'].head().tolist())

# Check for Position, Team, and name columns
position_col = 'Position' if 'Position' in fd_df.columns else 'position' if 'position' in fd_df.columns else None
team_col = 'Team' if 'Team' in fd_df.columns else 'team' if 'team' in fd_df.columns else None
first_name_col = 'First Name' if 'First Name' in fd_df.columns else 'First_Name' if 'First_Name' in fd_df.columns else None
last_name_col = 'Last Name' if 'Last Name' in fd_df.columns else 'Last_Name' if 'Last_Name' in fd_df.columns else None
nickname_col = 'Nickname' if 'Nickname' in fd_df.columns else None

if position_col is None or team_col is None:
    print(f"Error: Position column ({position_col}) or Team column ({team_col}) not found in fd_hitter_features_final.csv")
    exit()

# Merge to get Position, Team, and names
merge_columns = ['player_id', position_col, team_col]
if first_name_col:
    merge_columns.append(first_name_col)
if last_name_col:
    merge_columns.append(last_name_col)
if nickname_col:
    merge_columns.append(nickname_col)

df = df.merge(fd_df[merge_columns], on='player_id', how='left')
df = df.rename(columns={position_col: 'Position', team_col: 'Team', first_name_col: 'First_Name', last_name_col: 'Last_Name', nickname_col: 'Nickname'})
print("Columns after merge:", df.columns.tolist())
print("Missing Position values:", df['Position'].isna().sum())
print("Missing Team values:", df['Team'].isna().sum())

# Create Player_Name column (use Nickname if available, else First_Name + Last_Name)
def get_player_name(row):
    if pd.notna(row.get('Nickname')):
        return row['Nickname']
    if pd.notna(row.get('First_Name')) and pd.notna(row.get('Last_Name')):
        return f"{row['First_Name']} {row['Last_Name']}"
    return 'Unknown'

df['Player_Name'] = df.apply(get_player_name, axis=1)
print("Missing Player_Name values:", df['Player_Name'].isna().sum())

# Assign primary position (first listed position for multi-position players)
def get_primary_position(pos):
    if pd.isna(pos):
        return None
    # Take the first position if multiple (e.g., '2B/SS/OF' -> '2B')
    return pos.split('/')[0]

df['Primary_Position'] = df['Position'].apply(get_primary_position)
print("Missing Primary_Position values:", df['Primary_Position'].isna().sum())

# Filter out low-plate-appearance players, FPPG == 0, and invalid Primary_Position
df = df[(df['Played'] > 10) & (df['FPPG'] > 0) & (df['Primary_Position'].notna())]
print(f"Rows after filtering low-plate-appearance players, FPPG > 0, and valid Primary_Position: {len(df)}")

# Check available positions
positions = ['C', '1B', '2B', '3B', 'SS', 'OF']
for pos in positions:
    count = len(df[df['Primary_Position'] == pos])
    print(f"Players available for {pos}: {count}")

# Calculate actual Salary from log_Salary
df['Salary'] = df['log_Salary'].apply(np.expm1)

# Create PuLP problem
prob = LpProblem("FanDuel_MLB_Lineup", LpMaximize)

# Binary variables for player selection
player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in df.index}

# Objective: Maximize predicted FPPG
prob += lpSum(df.loc[i, 'FPPG'] * player_vars[i] for i in df.index)

# Constraints
prob += lpSum(player_vars[i] for i in df.index) == 9  # 9 players
prob += lpSum(df.loc[i, 'Salary'] * player_vars[i] for i in df.index) <= 35000  # Salary cap

# Position constraints (strict == 1 for all positions except OF)
for pos in positions[:-1]:  # C, 1B, 2B, 3B, SS
    prob += lpSum(player_vars[i] for i in df[df['Primary_Position'] == pos].index) == 1
prob += lpSum(player_vars[i] for i in df[df['Primary_Position'] == 'OF'].index) == 4  # 4 outfielders

# Solve with detailed output
solver = PULP_CBC_CMD(msg=True)
prob.solve(solver)

# Check solver status
print("Solver Status:", prob.status)

# Output lineup
lineup = df.loc[[i for i in df.index if player_vars[i].value() == 1], ['player_id', 'Player_Name', 'Position', 'Primary_Position', 'Team', 'FPPG', 'Salary']]
print("Optimal Lineup:")
print(lineup[['player_id', 'Player_Name', 'Position', 'Primary_Position', 'Team', 'FPPG', 'Salary']])
print(f"Total Salary: {lineup['Salary'].sum():.0f}")
print(f"Total Predicted FPPG: {lineup['FPPG'].sum():.2f}")

# Save lineup
lineup.to_csv('C:/Users/kgone/OneDrive/Personal_Information/MLB/data/optimized_lineup.csv', index=False)