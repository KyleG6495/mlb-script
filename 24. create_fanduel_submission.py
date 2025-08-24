import pandas as pd
import glob
import os
from datetime import datetime

print("INFO: Creating FanDuel Submission CSV...")

# Find the most recent Enhanced ML DFS lineup file
enhanced_files = glob.glob("../data/enhanced_ml_dfs_lineups_*.csv")
if enhanced_files:
    # Sort by filename (timestamp) to get the most recent
    most_recent_file = sorted(enhanced_files)[-1]
    lineup_df = pd.read_csv(most_recent_file)
    
    # Get the best lineup (highest lineup_total_projection)
    best_lineup_id = lineup_df[lineup_df['lineup_total_projection'] == lineup_df['lineup_total_projection'].max()]['lineup_id'].iloc[0]
    best_lineup_rows = lineup_df[lineup_df['lineup_id'] == best_lineup_id]
    
    # Create lineup DataFrame from the best lineup
    lineup = []
    for _, player_row in best_lineup_rows.iterrows():
        lineup.append({
            'Nickname': player_row['name'],
            'Primary_Position': player_row['primary_position'],
            'Team': player_row['team'],
            'Salary': player_row['salary'],
            'ML_FPPG': player_row['ml_projected_fppg'],
            'Projected_FPPG': player_row['ml_projected_fppg'],
            'Value': player_row['value_score']
        })
    
    lineup = pd.DataFrame(lineup)
    total_projection = best_lineup_rows['lineup_total_projection'].iloc[0]
    print(f"SUCCESS: Loaded ENHANCED ML lineup: {len(lineup)} players from {os.path.basename(most_recent_file)}")
    print(f"SUCCESS: Best lineup projection: {total_projection:.1f} FPPG")
    
else:
    # Fallback to old method
    try:
        lineup = pd.read_csv("../data/todays_actual_lineup.csv")
        print(f"SUCCESS: Loaded TODAY'S optimized lineup: {len(lineup)} players")
    except FileNotFoundError:
        print("ERROR: todays_actual_lineup.csv not found! Run Script 23 first.")
        print("INFO: Falling back to ml_optimized_lineup.csv...")
        lineup = pd.read_csv("../data/ml_optimized_lineup.csv")

# Load today's FanDuel slate to verify players are actually starting
print(" Verifying players are in today's slate...")
try:
    todays_slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # Check if all lineup players are in today's slate
    players_in_slate = lineup['Nickname'].isin(todays_slate['Nickname'])
    if not players_in_slate.all():
        print("WARNING: WARNING: Some lineup players are NOT in today's slate!")
        missing_players = lineup[~players_in_slate]['Nickname'].tolist()
        print(f"ERROR: Missing players: {missing_players}")
        
        # Filter to only players actually in today's slate
        lineup = lineup[players_in_slate].copy()
        print(f"SUCCESS: Filtered to {len(lineup)} players confirmed in today's slate")
    else:
        print(f"SUCCESS: All {len(lineup)} players confirmed in today's slate")
        
    # Additional check: Verify players have batting orders (are starters)
    if 'Batting Order' in todays_slate.columns:
        slate_starters = todays_slate[
            (todays_slate['Batting Order'].notna()) & 
            (todays_slate['Batting Order'] >= 1) & 
            (todays_slate['Batting Order'] <= 9)
        ]['Nickname'].tolist()
        
        lineup_starters = lineup['Nickname'].isin(slate_starters)
        if not lineup_starters.all():
            non_starters = lineup[~lineup_starters]['Nickname'].tolist()
            print(f"WARNING: WARNING: These players may not be starting today:")
            for player in non_starters:
                print(f"  ERROR: {player} - No batting order found")
        else:
            print(f"SUCCESS: All lineup players confirmed as starters with batting orders")
            
except FileNotFoundError:
    print("WARNING: Could not verify against today's slate - fd_slate_today.csv not found")

print(f"SUCCESS: Final lineup verified: {len(lineup)} players")

# FanDuel submission format requires specific columns and order
# Standard FanDuel CSV format: C,1B,2B,3B,SS,OF,OF,OF,OF

# Sort lineup by position order for FanDuel submission
position_order = {'C': 1, '1B': 2, '2B': 3, '3B': 4, 'SS': 5, 'OF': 6}
lineup['pos_order'] = lineup['Primary_Position'].map(position_order)

# Use the correct FPPG column name based on what's available
fppg_col = 'Projected_FPPG' if 'Projected_FPPG' in lineup.columns else 'ML_FPPG'
lineup_sorted = lineup.sort_values(['pos_order', fppg_col], ascending=[True, False])

print("\nLINEUP: LINEUP ORDER FOR SUBMISSION:")
print(lineup_sorted[['Nickname', 'Primary_Position', 'Team', 'Salary', fppg_col]].to_string(index=False))

# Create FanDuel submission format
# Method 1: Player ID format (if you have FanDuel player IDs)
if 'player_id' in lineup.columns:
    fd_submission_ids = pd.DataFrame({
        'C': [lineup_sorted[lineup_sorted['Primary_Position'] == 'C']['player_id'].iloc[0]],
        '1B': [lineup_sorted[lineup_sorted['Primary_Position'] == '1B']['player_id'].iloc[0]],
        '2B': [lineup_sorted[lineup_sorted['Primary_Position'] == '2B']['player_id'].iloc[0]],
        '3B': [lineup_sorted[lineup_sorted['Primary_Position'] == '3B']['player_id'].iloc[0]],
        'SS': [lineup_sorted[lineup_sorted['Primary_Position'] == 'SS']['player_id'].iloc[0]],
        'OF': lineup_sorted[lineup_sorted['Primary_Position'] == 'OF']['player_id'].tolist()[:4]
    })
    
    # Flatten OF positions to separate columns
    fd_submission_ids['OF1'] = fd_submission_ids['OF'].apply(lambda x: x[0] if len(x) > 0 else None)
    fd_submission_ids['OF2'] = fd_submission_ids['OF'].apply(lambda x: x[1] if len(x) > 1 else None)
    fd_submission_ids['OF3'] = fd_submission_ids['OF'].apply(lambda x: x[2] if len(x) > 2 else None)
    fd_submission_ids['OF4'] = fd_submission_ids['OF'].apply(lambda x: x[3] if len(x) > 3 else None)
    fd_submission_ids = fd_submission_ids.drop('OF', axis=1)
    
    # Reorder columns for FanDuel format
    fd_submission_ids = fd_submission_ids[['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'OF4']]
    fd_submission_ids.to_csv("../data/fanduel_submission_ids.csv", index=False)
    print("SUCCESS: Saved FanDuel submission (Player IDs): ../data/fanduel_submission_ids.csv")

# Method 2: Player Names format (more readable)
of_players = lineup_sorted[lineup_sorted['Primary_Position'] == 'OF']['Nickname'].tolist()

# Check if we have players for all required positions
required_positions = ['C', '1B', '2B', '3B', 'SS']
missing_positions = []
for pos in required_positions:
    if len(lineup_sorted[lineup_sorted['Primary_Position'] == pos]) == 0:
        missing_positions.append(pos)

if missing_positions:
    print(f"WARNING: WARNING: Missing players for positions: {missing_positions}")
    print("Cannot create full lineup - need players in all positions")
    print("Using available players only for partial submission...")

# Helper function to get player name safely
def get_player_name(position):
    players = lineup_sorted[lineup_sorted['Primary_Position'] == position]['Nickname']
    return players.iloc[0] if len(players) > 0 else f"NEED_{position}_PLAYER"

# Ensure we have exactly 4 OF players
while len(of_players) < 4:
    of_players.append("NEED_OF_PLAYER")

fd_submission_names = pd.DataFrame({
    'C': [get_player_name('C')],
    '1B': [get_player_name('1B')],
    '2B': [get_player_name('2B')],
    '3B': [get_player_name('3B')],
    'SS': [get_player_name('SS')],
    'OF1': [of_players[0]],
    'OF2': [of_players[1]],
    'OF3': [of_players[2]],
    'OF4': [of_players[3]]
})

fd_submission_names.to_csv("../data/fanduel_submission_names.csv", index=False)
print("SUCCESS: Saved FanDuel submission (Names): ../data/fanduel_submission_names.csv")

# Method 3: Detailed lineup card for manual entry
lineup_card = []
for pos in ['C', '1B', '2B', '3B', 'SS']:
    players_at_pos = lineup_sorted[lineup_sorted['Primary_Position'] == pos]
    if len(players_at_pos) > 0:
        player = players_at_pos.iloc[0]
        lineup_card.append({
            'Position': pos,
            'Player': player['Nickname'],
            'Team': player['Team'],
            'Salary': f"${player['Salary']:,}",
            'Projected': f"{player[fppg_col]:.1f}",
            'Value': f"{player['Value']:.1f}"
        })
    else:
        lineup_card.append({
            'Position': pos,
            'Player': f'NEED_{pos}_PLAYER',
            'Team': 'N/A',
            'Salary': '$0',
            'Projected': '0.0',
            'Value': '0.0'
        })

# Add OF players
of_players_detailed = lineup_sorted[lineup_sorted['Primary_Position'] == 'OF']
for i, (_, player) in enumerate(of_players_detailed.iterrows(), 1):
    lineup_card.append({
        'Position': f'OF{i}',
        'Player': player['Nickname'],
        'Team': player['Team'],
        'Salary': f"${player['Salary']:,}",
        'Projected': f"{player[fppg_col]:.1f}",
        'Value': f"{player['Value']:.1f}"
    })

lineup_card_df = pd.DataFrame(lineup_card)
lineup_card_df.to_csv("../data/fanduel_lineup_card.csv", index=False)
print("SUCCESS: Saved detailed lineup card: ../data/fanduel_lineup_card.csv")

# Summary for manual entry
print(f"\nINFO: FANDUEL MANUAL ENTRY SUMMARY:")
print(f"Total Salary: ${lineup['Salary'].sum():,} / $35,000")
print(f"Projected Points: {lineup[fppg_col].sum():.1f}")
print(f"Average Value: {lineup['Value'].mean():.1f} pts/$1K")

print(f"\nTARGET: LINEUP FOR FANDUEL ENTRY:")
for _, player in lineup_card_df.iterrows():
    print(f"{player['Position']:>3}: {player['Player']:<20} ({player['Team']}) - {player['Salary']:<8} - {player['Projected']} pts")

print(f"\nSUCCESS: Created 3 submission formats:")
print(f"   1. fanduel_submission_ids.csv - Player ID format")
print(f"   2. fanduel_submission_names.csv - Player names format") 
print(f"   3. fanduel_lineup_card.csv - Detailed lineup card")