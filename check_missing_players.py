import pandas as pd

# Load August 13th slate 
slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')

# Check why we missed key players
missing_players = ['Jakob Marsee', 'Joe Ryan', 'Xavier Edwards']

print('=== WHY WE MISSED WINNING PLAYERS ===')
print()

for player_name in missing_players:
    first_name = player_name.split()[0]
    last_name = player_name.split()[1]
    
    player_rows = slate[
        (slate['Nickname'].str.contains(first_name, na=False)) & 
        (slate['Last Name'].str.contains(last_name, na=False))
    ]
    
    if len(player_rows) > 0:
        player = player_rows.iloc[0]
        print(f'{player_name}:')
        print(f'  Salary: ${player["Salary"]}')
        print(f'  Position: {player["Position"]}')
        if 'Probable Pitcher' in slate.columns:
            print(f'  Probable Pitcher: {player.get("Probable Pitcher", "N/A")}')
        if 'Batting Order' in slate.columns:
            print(f'  Batting Order: {player.get("Batting Order", "N/A")}')
        if 'Injury Indicator' in slate.columns:
            print(f'  Injury: {player.get("Injury Indicator", "None")}')
        print()
    else:
        print(f'{player_name}: NOT FOUND in slate')
        print()
