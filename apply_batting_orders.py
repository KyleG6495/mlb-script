import pandas as pd
import json

print('=== MANUAL BATTING ORDER APPLICATION ===')

# Load the lineup data
with open('temp_lineup_data.json', 'r') as f:
    lineup_data = json.load(f)
print(f'Loaded {len(lineup_data)} batting order assignments')

# Load FD slate
slate_file = '../fd_current_slate/fd_slate_today.csv'
df = pd.read_csv(slate_file)
print(f'Loaded FD slate with {len(df)} players')

# Add Order column if it doesn't exist
if 'Order' not in df.columns:
    df['Order'] = None
    print('Added Order column to FD slate')

# Apply batting orders
matches = 0
for key, order in lineup_data.items():
    team, player_name = key.split('_', 1)
    
    # Find matching player in FD slate
    mask = (df['Team'] == team) & (df['Position'] != 'P')
    team_players = df[mask]
    
    for idx, row in team_players.iterrows():
        fd_name = f"{row['First Name']} {row['Nickname']}"
        
        # Try various name matching approaches
        if (player_name in fd_name or fd_name in player_name or 
            player_name.split()[-1] in fd_name or
            any(part in fd_name for part in player_name.split() if len(part) > 2)):
            df.at[idx, 'Order'] = order
            matches += 1
            print(f'✅ {team}: {player_name} -> {fd_name} (Order {order})')
            break

print(f'\nApplied {matches} batting orders')

# Save updated file
df.to_csv(slate_file, index=False)
print(f'Updated file saved: {slate_file}')

# Show coverage
orders_assigned = df[df['Order'].notna()]
teams_with_orders = orders_assigned['Team'].unique()
teams_in_slate = df['Team'].unique()

print(f'\nFinal coverage: {len(teams_with_orders)}/{len(teams_in_slate)} teams')
print(f'Players with orders: {len(orders_assigned)}/{len(df)}')

# Show teams with complete lineups
print(f'\nTeams with batting orders: {sorted(teams_with_orders)}')
